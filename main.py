import logging
import os
import random
import re
import nltk
import psycopg2
import pymorphy2

from aioalice.utils.helper import Helper, HelperMode, Item
from aiohttp import web
from aioalice import Dispatcher, get_new_configured_app, types
from aioalice.dispatcher import MemoryStorage, SkipHandler
from dotenv import load_dotenv
from store import *

load_dotenv()
WEBHOOK_URL_PATH = '/my-alice-webhook/'  # webhook endpoint

WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001
SKILL_ID = os.getenv("SKILL_ID")
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger_ru')
# Создаем экземпляр диспетчера и подключаем хранилище в памяти
dp = Dispatcher(storage=MemoryStorage(), skill_id=SKILL_ID, oauth_token=OAUTH_TOKEN)
numbers_t = {'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7}
start_buttons = ["Давай", "Не хочу"]
no_list = ['нет', 'не хочу', 'не правильно']
cancel_text = ['конец игры', 'стоп', 'прекрати', 'хватит']
yes_list = ['давай', 'начать игру', 'да', 'хочу', 'начнем игру', 'еще', 'продолжить']
skills_list = ['что ты умеешь', 'что ты умеешь?']
help_text = ['помоги', 'помощь']
reset_text = ['с начала', 'сбросить', 'сброс']
player_num_buttons = [num.capitalize() for num in list(numbers_t.keys())]


class GameStates(Helper):
    mode = HelperMode.snake_case

    START = Item()
    PLAYERS = Item()
    PLAYERS_CHECK = Item()
    PLAYERS_RIGHT_CHECK = Item()
    GAME = Item()
    SUPER = Item()


class Message:
    def __init__(self, alice_request):
        self.user_id = alice_request.session.user_id
        self.session_id = alice_request.session.session_id
        self.command = alice_request.request.command


async def get_names(string):
    # Разбиваем текст на токены (слова)
    tokens = nltk.word_tokenize(string, language='russian')

    # Определяем части речи для каждого токена
    pos_tags = nltk.pos_tag(tokens, lang='rus')

    # Фильтруем токены, оставляя только имена собственные (имена, фамилии, географические названия и проч.)
    proper_names = [token for token, pos in pos_tags if pos.startswith('S')]

    # Возвращаем список имен собственных
    return proper_names


async def agree_word(number, word_forms):
    if number % 10 == 1 and number % 100 != 11:
        word_form = word_forms[0]  # единственное число
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        word_form = word_forms[1]  # несколько
    else:
        word_form = word_forms[2]  # множественное число
    return word_form


async def find_number(string):
    print(string)

    try:
        num = int(string)
        return num
    except BaseException:
        nums = re.findall(r'\d+|\b(один|два|три|четыре|пять|шесть|семь)\b', string, re.IGNORECASE)
        if nums:
            return int(numbers_t[nums[0].lower()])

        else:

            return None


async def contains_stop_words(stop_words, text):
    pattern = '|'.join([re.escape(word) for word in stop_words])
    regex = re.compile(pattern, re.IGNORECASE)
    matches = regex.findall(text)
    print('gang', bool(matches))
    return bool(matches)


async def check_intent(alice_request):
    m = Message(alice_request)

    stop_res = await contains_stop_words(cancel_text, m.command)
    skills_res = await contains_stop_words(skills_list, m.command)
    if stop_res:
        print("Хватит")
        text = random.choice(end_session_messages)
        await dp.storage.reset_state(m.user_id)
        return alice_request.response(text,
                                      end_session=True)
    elif skills_res:
        print("Что ты умеешь?")
        text = random.choice(new_user_messages)

        return alice_request.response(
            text,
            buttons=start_buttons)

    else:
        return None


async def get_random_question(excluded_ids, count=1):
    conn = psycopg2.connect("""
        host=185.185.68.54
        port=5432
        dbname=chgk
        user=postgres
        password=Taner2320
    """)

    excluded_ids_str = ', '.join(str(idd) for idd in excluded_ids)
    print(f'SELECT * FROM questions WHERE id NOT IN ({excluded_ids_str}) ORDER BY random() LIMIT {count}')
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM questions WHERE id NOT IN ({excluded_ids_str}) ORDER BY random() LIMIT {count}")

    result = cur.fetchone()
    questions = result if result else ''

    cur.close()
    conn.close()
    print("ok")
    return questions


async def get_curr_turn(user_id):
    data = await dp.storage.get_data(user_id)
    return data.get('curr_turn')


async def get_players_list(user_id):
    data = await dp.storage.get_data(user_id)
    return data.get('user_list')


async def get_curr_question(user_id):
    data = await dp.storage.get_data(user_id)
    return data.get('curr_question')


async def get_data(user_id, data_name):
    data = await dp.storage.get_data(user_id)
    return data.get(data_name)


async def update_question(user_id, new_question):
    await dp.storage.update_data(user_id, curr_question=new_question)


async def update_hint_count(user_id, hint_count):
    await dp.storage.update_data(user_id, hint_count=hint_count)


async def update_excluded_ids(user_id, new_id):
    excluded_ids = await get_data(user_id, 'excluded_ids')
    excluded_ids = list(excluded_ids)
    excluded_ids.append(new_id)

    await dp.storage.update_data(user_id, excluded_ids=excluded_ids)


async def update_turn(user_id):
    player_list = await get_players_list(user_id)
    player_count = len(player_list
                       )
    curr_turn = await get_curr_turn(user_id)
    code = 0
    curr_round_turn = await get_data(user_id, 'curr_round_turn')
    turns_in_this_round = await get_data(user_id, 'turns_in_this_round')
    player_list = await get_players_list(user_id)
    curr_round = await get_data(user_id, 'curr_round')
    if player_count and (curr_turn + 1) % player_count == 0:
        curr_round_turn += 1
        print('new round turn')
    if curr_round_turn == turns_in_this_round:
        print('tr', turns_in_this_round)

        curr_round_turn = 0
        curr_round += 1

        turns_in_this_round = random.randrange(2, 4)
        print("new round")
        code = 1
    if curr_round == max_rounds - 1:
        curr_round = 0
        turns_in_this_round = 10 ** 9
        code = 2
        await dp.storage.update_data(user_id, is_super_round=1)
    if not player_list:
        code = 3
    print("next turn")
    print(curr_round_turn, curr_round)
    if player_count:
        curr_turn = (curr_turn + 1) % player_count
    await dp.storage.update_data(user_id,
                                 curr_turn=curr_turn, hint_count=0,
                                 left_points=points_for_win, curr_round_turn=curr_round_turn, curr_round=curr_round,
                                 turns_in_this_round=turns_in_this_round)
    return code


async def update_points(user_id):
    left_points = await get_data(user_id, 'left_points')
    players_data = await get_data(user_id, 'users_data')
    player_id = await get_curr_turn(user_id)
    players_data[player_id]['points'] += left_points
    await dp.storage.update_data(user_id, users_data=players_data)


async def update_left_points(user_id, point_to_minus):
    left_points = await get_data(user_id, 'left_points')

    await dp.storage.update_data(user_id, left_points=max(left_points - point_to_minus, 0))


async def make_turn_text(user_id):
    text = random.choice(turn_messages)
    curr_turn = await get_curr_turn(user_id)

    name = await get_players_list(user_id)
    name = name[curr_turn]
    text = text.format(name)
    excluded_ids = await get_data(user_id, 'excluded_ids')
    question = await get_random_question(list(excluded_ids))
    print(question)
    await update_question(user_id, question)
    text += question[1]
    return text


async def make_out_text(user_id):
    text = random.choice(out_messages)
    curr_turn = await get_curr_turn(user_id)

    name = await get_players_list(user_id)
    name = name[curr_turn]
    text = text.format(name)
    player_list = list(await get_players_list(user_id))
    player_list.pop(int(curr_turn))
    await dp.storage.update_data(user_id, user_list=player_list, curr_turn=curr_turn - 1)

    return text


async def agree_verb_with_proper_noun(verb, proper_noun):
    morph = pymorphy2.MorphAnalyzer()
    parsed = morph.parse(proper_noun)
    noun_info = parsed[0]
    gender = noun_info.tag.gender

    if gender == 'masc':
        return verb + 'л'
    elif gender == 'femn':
        return verb + 'ла'
    elif gender == 'neut':
        return verb + 'ло'
    else:
        return verb


async def make_end_text(user_id):
    text = 'Вот и всё на этом! Осталось лишь подвести итоги нашей игры. А вот как раз и они: '

    users_data = dict(await get_data(user_id, 'users_data'))
    for data in list(list(users_data.values())):
        point_word = await agree_word(int(data["points"]), ['балл', 'балла', 'баллов'])
        text += f'{data["name"]} {await agree_verb_with_proper_noun("набра", data["name"])} {data["points"]} {point_word}, '
    text = text[:-2] + '. '
    sorted_lst = sorted(list(users_data.values()), key=lambda x: x["points"], reverse=True)
    text += f'И победителем нашей викторины становится {sorted_lst[0]["name"]}! '

    return text


async def check_answer(user_answer, correct_answer):
    # Удаление знаков препинания и приведение к нижнему регистру
    user_answer = re.sub(r'[^\w\s]', '', user_answer.lower())
    correct_answer = re.sub(r'[^\w\s]', '', correct_answer.lower())

    # Разделение ответа пользователя и правильного ответа на слова
    user_words = set(user_answer.split())
    correct_words = set(correct_answer.split())

    # Проверка наличия правильных слов в ответе пользователя
    if correct_words.issubset(user_words):
        return True

    # Поиск схожих слов с помощью алгоритма Левенштейна
    for correct_word in correct_words:
        for user_word in user_words:
            # Расчет расстояния Левенштейна между словами
            distance = await levenshtein_distance(correct_word, user_word)
            # Если расстояние меньше или равно 2 (настраиваемый порог),
            # то считаем слова похожими и считаем ответ пользователя правильным

            if distance <= 1.5:
                return True

    return False


async def levenshtein_distance(s, t):
    if s == t:
        return 0
    elif len(s) == 0:
        return len(t)
    elif len(t) == 0:
        return len(s)
    else:
        v0 = [None] * (len(t) + 1)
        v1 = [None] * (len(t) + 1)

        for i in range(len(v0)):
            v0[i] = i

        for i in range(len(s)):
            v1[0] = i + 1
            for j in range(len(t)):
                cost = 0 if s[i] == t[j] else 1
                v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
            for j in range(len(v0)):
                v0[j] = v1[j]

        return v1[len(t)]


@dp.request_handler(state="*", contains=cancel_text)
async def handle_user_cancel(alice_request):
    print("Хва тит")
    m = Message(alice_request)
    text = random.choice(end_session_messages)
    await dp.storage.reset_state(m.user_id)
    return alice_request.response(text,
                                  end_session=True)


@dp.request_handler(state="*", contains=skills_list)
async def handle_user_skills(alice_request):
    print("Что ты умеешь?")
    text = random.choice(new_user_messages)

    return alice_request.response(
        text,
        buttons=start_buttons)


@dp.request_handler(contains=help_text)
async def handle_user_what(alice_request):
    m = Message(alice_request)
    text = random.choice(rules_messages)
    return alice_request.response(
        text, buttons=start_buttons)


@dp.request_handler()
async def handle_new_session(alice_request):
    print(alice_request)
    m = Message(alice_request)
    # intent_res = await check_intent(alice_request)
    # print("i", intent_res)
    # if intent_res:
    #     return intent_res
    await dp.storage.set_state(m.user_id, GameStates.START)
    text = random.choice(new_user_messages) + random.choice(lets_start_messages)

    return alice_request.response(text, tts=text, buttons=start_buttons)


@dp.request_handler(state=GameStates.START)
async def handle_user_agrees(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)
    # intent_res = await check_intent(alice_request)
    # print("i", intent_res)
    # if intent_res:
    #     return intent_res
    await dp.storage.reset_state(m.user_id)
    if m.command in no_list:
        return alice_request.response("Жаль, возвращайтесь как решите сыграть.\n"
                                      "До встречи!",
                                      end_session=True)

    await dp.storage.update_data(m.user_id, user_counts=0)

    text = random.choice(rules_messages) + random.choice(user_count_messages)
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS)

    return alice_request.response(text, tts=text, buttons=player_num_buttons)


@dp.request_handler(state=GameStates.PLAYERS)
async def handle_user_names(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)
    # intent_res = await check_intent(alice_request)
    # print("i", intent_res)
    # if intent_res:
    #     return intent_res

    users_count = await find_number(m.command)
    if not users_count or users_count > 7:
        text = random.choice(wrong_players_count_messages) + random.choice(user_count_messages)
        return alice_request.response(text, buttons=player_num_buttons)
    await dp.storage.reset_state(m.user_id)
    await dp.storage.update_data(m.user_id, user_counts=users_count)

    text = random.choice(names_messages)
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_CHECK)

    return alice_request.response(text)


@dp.request_handler(state=GameStates.PLAYERS_CHECK, contains=help_text)
async def handle_user_names(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)

    text = 'Вам нужно произнести имена всех игроков в строчку, например: "Маша, Петя, Даша". '
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_CHECK)

    return alice_request.response(text)


@dp.request_handler(state=GameStates.PLAYERS_CHECK)
async def handle_user_names(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)
    user_list = await get_names(m.command)

    if not user_list or len(user_list) > 7:
        text = random.choice(wrong_players_count_named_messages) + random.choice(help_messages)
        return alice_request.response(text)
    print(user_list)
    user_list = [user.capitalize() for user in user_list]
    # intent_res = await check_intent(alice_request)
    # print("i", intent_res)
    # if intent_res:
    #     return intent_res
    await dp.storage.reset_state(m.user_id)

    users = {i: {
        'name': user_list[i],
        'points': 0
    } for i in range(len(user_list))}
    print(users)
    turns_in_this_round = random.randrange(2, 4)
    await dp.storage.update_data(m.user_id, user_counts=len(user_list), users_data=users, user_list=user_list,
                                 curr_turn=0, curr_question='', hint_count=0, left_points=points_for_win, curr_round=0,
                                 turns_in_this_round=turns_in_this_round, curr_round_turn=0, excluded_ids=[1],
                                 is_super_round=0)

    user_string = ', '.join(user_list)
    text = random.choice(will_play_message) + user_string + ". Вcё правильно?"
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_RIGHT_CHECK)

    return alice_request.response(text, buttons=["Да", "Нет"])


@dp.request_handler(state=GameStates.PLAYERS_RIGHT_CHECK)
async def handle_user_check_names(alice_request):
    m = Message(alice_request)

    await dp.storage.reset_state(m.user_id)
    if m.command in no_list:
        text = random.choice(names_messages)
        await dp.storage.set_state(m.user_id, GameStates.PLAYERS_CHECK)
        return alice_request.response(text)
    text = random.choice(game_start_messages)
    await dp.storage.set_state(m.user_id, GameStates.GAME)
    text += await make_turn_text(m.user_id)

    return alice_request.response(text, tts=sounds['intro'] + text)


@dp.request_handler(state=GameStates.GAME, contains=help_text)
async def handle_game(alice_request):
    m = Message(alice_request)

    text = 'Всего за правильный ответ можно получить пять баллов. За каждый неверный ответ вы теряете один балл за этот ответ.' \
           'Вы можете сказать "Повтори" и я повторю вопрос или попросить подсказку, ' \
           'тогда вы услышите одну из двух имеющихся подсказок. За каждую подсказку с вас снимается два балла. ' \
           'Если вы не знаете кто сейчас ходит, произнесите слово "Очередь". ' \
           'А если вам по какой-то причине не хочется отвечать на вопрос, скажите "Пас". Удачной игры!'

    return alice_request.response(text)


@dp.request_handler(state=GameStates.GAME)
async def handle_game(alice_request):
    m = Message(alice_request)
    curr_question = await get_curr_question(m.user_id)
    curr_turn = await get_curr_turn(m.user_id)
    text = ''
    is_super_round = await get_data(m.user_id, 'is_super_round')
    print('super', is_super_round)
    if 'подска' in m.command.lower():
        if is_super_round:
            text = 'Это супер-раунд, здесь не работают подсказки!'
            return alice_request.response(text)
        hint_count = await get_data(m.user_id, 'hint_count')
        hint_count = int(hint_count)
        left_points = await get_data(m.user_id, 'left_points')
        if left_points - 2 < 1:
            text = random.choice(not_enough_points_messages)
        else:
            match hint_count:

                case 0:
                    question_data = curr_question
                    hint1 = question_data[3]

                    text = random.choice(hint1_messages)
                    text += hint1
                    await update_hint_count(m.user_id, hint_count + 1)
                case 1:
                    question_data = curr_question
                    hint2 = question_data[4]

                    text = random.choice(hint2_messages)
                    text += hint2
                    await update_hint_count(m.user_id, hint_count + 1)
                case 2:
                    text = random.choice(hint_max_messages)
            await update_left_points(m.user_id, minus_points_for_hint)
            return alice_request.response(text, tts=sounds['hint'] + text)

    elif 'повтор' in m.command.lower():

        question = curr_question

        text = question[1]
    elif 'пас' == m.command.lower() and not is_super_round:

        text = "Хорошо, пропускаем. "
        code = await update_turn(m.user_id)
        turn_text = ''
        new_round_tts = ''
        if code == 1:

            new_round_tts += sounds['next_round']
            curr_round = await get_data(m.user_id, 'curr_round')
            turn_text += f'Мы начинаем раунд {curr_round + 1}. '

        elif code == 2:
            new_round_tts += sounds['super']
            text += random.choice(super_round_message)
        turn_text += await make_turn_text(m.user_id)
        print("Ready")
        return alice_request.response(text + turn_text, tts=sounds['skip'] + text + new_round_tts + turn_text)
    elif 'очередь' in m.command.lower():
        curr_turn = await get_curr_turn(m.user_id)
        name = await get_players_list(m.user_id)
        name = name[curr_turn]

        text = "Сейчас отвечает {}".format(name)
    else:
        question_data = curr_question
        answer = question_data[2]
        print(answer.lower(), m.command.lower())
        corr_answer = await check_answer(m.command.lower(), answer.lower())
        if corr_answer:
            points = await get_data(m.user_id, "left_points")
            if is_super_round:
                points = 10
            point_word = await agree_word(int(points), ['балл', 'балла', 'баллов'])
            text = f"{random.choice(right_answer_messages)} Вы получаете {points} {point_word}. "
            await update_points(m.user_id)
            print(await get_data(m.user_id, 'users_data'))
            await update_excluded_ids(m.user_id, question_data[0])
            code = await update_turn(m.user_id)

            new_round_tts = ''
            turn_text = ''
            if code == 1:
                new_round_tts += sounds['next_round']
                curr_round = await get_data(m.user_id, 'curr_round')
                turn_text += f'Мы начинаем раунд {curr_round + 1}. '

            elif code == 2:
                new_round_tts += sounds['super']
                text += random.choice(super_round_message)

            turn_text += await make_turn_text(m.user_id)
            return alice_request.response(text + turn_text, tts=sounds['right'] + text + new_round_tts + turn_text)

        else:

            await update_left_points(m.user_id, minus_points_for_wrong_answer)
            points = await get_data(m.user_id, "left_points")
            text = random.choice(wrong_answer_messages)
            new_round_tts = ''
            turn_text = ''
            res_sound = ''
            end_text = ''
            end_s = False
            sound = sounds['wrong']
            if points - minus_points_for_wrong_answer < 0 or is_super_round:
                text = random.choice(zero_point_messages)
                if is_super_round:
                    turn_text = await make_out_text(m.user_id)
                    player_list = list(await get_players_list(m.user_id))
                    sound = sounds['death']
                    print(player_list)

                code = await update_turn(m.user_id)

                if code == 1:
                    new_round_tts += sounds['next_round']
                    curr_round = await get_data(m.user_id, 'curr_round')
                    turn_text += f'Мы начинаем раунд {curr_round + 1}. '


                elif code == 2:
                    new_round_tts += sounds['super']
                    text += random.choice(super_round_message)

                elif code == 3:
                    new_round_tts += sounds['end']
                    text += await make_end_text(m.user_id)
                    res_sound = sounds['res']
                    end_text = 'И теперь точно всё на этом, увидимся в следующей викторине!'
                    turn_text = ''
                    await dp.storage.reset_state(m.user_id)
                if code != 3:
                    turn_text += await make_turn_text(m.user_id)
            return alice_request.response(text + turn_text + end_text,
                                          tts=sound + text + new_round_tts + turn_text + res_sound + end_text
                                          )

    return alice_request.response(text)


@dp.request_handler()
async def handle_all_other_requests(alice_request):
    m = Message(alice_request)

    return alice_request.response(
        'Немного не понял вас. Если нужна помощь, скажите "Помощь" или "Что ты умеешь?".'
    )


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, loop=dp.loop)
