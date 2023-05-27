import logging
import os
import random
import re

import psycopg2
from aioalice.utils.helper import Helper, HelperMode, Item
from aiohttp import web
from aioalice import Dispatcher, get_new_configured_app, types
from aioalice.dispatcher import MemoryStorage, SkipHandler
from dotenv import load_dotenv
from natasha import NamesExtractor, MorphVocab
from store import *

load_dotenv()
WEBHOOK_URL_PATH = '/my-alice-webhook/'  # webhook endpoint

WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001
SKILL_ID = os.getenv("SKILL_ID")
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

# Создаем экземпляр диспетчера и подключаем хранилище в памяти
dp = Dispatcher(storage=MemoryStorage(), skill_id=SKILL_ID, oauth_token=OAUTH_TOKEN)
numbers_t = {'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7}
start_buttons = ["Давай", "Не хочу"]
no_list = ['нет', 'не хочу', 'не правильно']
cancel_text = ['конец игры', 'стоп', 'стой', 'прекрати', 'хватит']
yes_list = ['давай', 'начать игру', 'да', 'хочу', 'начнем игру', 'еще', 'продолжить']
skills_list = ['что ты умеешь', 'что ты умеешь?']
help_text = ['помоги', 'помощь']
player_num_buttons = [num.capitalize() for num in list(numbers_t.keys())]


class GameStates(Helper):
    mode = HelperMode.snake_case

    START = Item()
    PLAYERS = Item()
    PLAYERS_CHECK = Item()
    PLAYERS_RIGHT_CHECK = Item()


class Message:
    def __init__(self, alice_request):
        self.user_id = alice_request.session.user_id
        self.session_id = alice_request.session.session_id
        self.command = alice_request.request.command


async def get_names(string):
    morph_vocab = MorphVocab()
    extractor = NamesExtractor(morph_vocab)

    matches = extractor(string)

    names = [match.fact.first for match in matches]
    return names


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


async def get_random_question(count=1):
    conn = psycopg2.connect("""
        host=rc1b-1dkhcvps79tr5wu2.mdb.yandexcloud.net
        port=6432
        dbname=questions
        user=user1
        password=Taner2320
        target_session_attrs=read-write
    """)

    cur = conn.cursor()

    cur.execute(f"SELECT * FROM chgk_questions ORDER BY random() LIMIT {count}")

    result = cur.fetchone()
    questions = result if result else ''

    cur.close()
    conn.close()
    print("ok")
    return questions


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


@dp.request_handler(func=lambda areq: areq.session.new)
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
    await dp.storage.reset_state(m.user_id)
    users_count = int(await find_number(m.command))
    if not users_count or users_count > 7:
        text = random.choice(wrong_players_count_messages) + random.choice(user_count_messages)
        return alice_request.response(text, buttons=player_num_buttons)
    await dp.storage.update_data(m.user_id, user_counts=users_count)

    text = random.choice(names_messages)
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
    await dp.storage.update_data(m.user_id, user_counts=len(user_list), users_data=users, user_list=user_list)

    text = random.choice(names_messages)
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_RIGHT_CHECK)

    return alice_request.response(text)


@dp.request_handler(state=GameStates.PLAYERS_CHECK, contains=help_text)
async def handle_user_names(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)

    text = 'Вам нужно произнести имена всех игроков в строчку, например: "Маша, Петя, Даша". '
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_RIGHT_CHECK)

    return alice_request.response(text)


@dp.request_handler(state=GameStates.PLAYERS_RIGHT_CHECK)
async def handle_user_names(alice_request):
    if alice_request.request.command == "ping":
        return alice_request.response('pong')
    m = Message(alice_request)

    # intent_res = await check_intent(alice_request)
    # print("i", intent_res)
    # if intent_res:
    #     return intent_res
    await dp.storage.reset_state(m.user_id)

    data = await dp.storage.get_data(m.user_id)
    user_string = ', '.join(data.get("user_list"))
    text = random.choice(will_play_message) + user_string + ". Вcё правильно?"
    await dp.storage.set_state(m.user_id, GameStates.PLAYERS_RIGHT_CHECK)

    return alice_request.response(text, buttons=random.choices(yes_list, k=2) + random.choices(no_list, k=2))


@dp.request_handler()
async def handle_all_other_requests(alice_request):
    m = Message(alice_request)

    return alice_request.response(
        'Немного не поняла вас. Если нужна помощь, скажите "Помощь" или "Что ты умеешь?".'
    )


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, loop=dp.loop)
