new_user_messages = ["Привет, это навык вопросы знатокам! Вам придётся доказать, что именно вы достойны звания "
                     "чемпиона. Во время игры, вы будете отвечать на интересные вопросы раз за разом. "
                     "В конце вас ждёт суперигра. "
                     "Играть могут как один, так и несколько человек. "]
rules_messages = [
    "В этой игре будет всего 6 раундов: 5 обычных и один супер-раунд. Во время обычных раундов вам нужно будет "
    "по-очереди отвечать на вопросы. Если вы не знаете ответ на вопрос, вы можете попросить подсказку, всего их две. "
    "За каждую подсказку с вас будет сниматься по баллу, всего баллов за правильный ответ можно получить 5. "
    "По истечении 5 раундов, два человека с наибольшим количеством баллов сразятся в суперигре"
    "(если вы играете один, то и в суперигре отвечать будете один). "
    "Правила суперигры можно будет подробнее узнать ближе к её началу. "]
lets_start_messages = [
    "Ну что, погнали?", "Поехали?", "Начинаем?", "На старт?", "Играем?", "Ну что, на старт?", "Готовы начинать?"

]
user_count_messages = ["Сколько человек будет играть?", "Сколько будет игроков?", "Сколько человек сегодня играет?",
                       "Назовите количество игроков."]
end_session_messages = ["Спасибо за игру!", "Игра завершается! До скорого!",
                        "Игра подошла к концу, надеюсь, скоро увидимся!"]
names_messages = ["Назовите имена всех игроков!", "Теперь назовите имена всех участников. ",
                  "Скажите имена всех игроков. "]
wrong_players_count_messages = [
    "К сожалению, играть могут от одного до семи человек. Попробуйте поменять количество участников. ",
    "Играть могут максимум семь человек и минимум один. Попробуйте изменить команду. ",
    "Игроков может быть от одного до семи. "]
wrong_players_count_named_messages = ["Вы назвали недопустимое количество участников, попробуйте назвать всех заново. ",
                                      "Мне не удалось распознать необходимое количество игроков, пожалуйста повторите "
                                      "их имена заново. "]
help_messages = ["Если нужна помощь, то так и скажите", 'Если вы чего-то не понимаете, просто скажите:"Помощь". ']
will_play_message = ["Будут играть: ", "С нами будут играть: ", "Получается, с нами играют: ",
                     "Отлично, с нами играют: "]

game_start_messages = ["Отлично, тогда начинаем! ", "Рад слышать, начнём же! ",
                       "Прекрасно, игра начинается уже сейчас! "]
turn_messages = ["Сейчас ходит: {}. Слушай вопрос! ", "{}, твоя очередь! Слушай вопрос. ",
                 "{}, следующий вопрос тебе! "]
hint1_messages = ["Слушай внимательно первую подсказку. ", "Не отвлекайся и послушай первую подсказку. ",
                  "Внимание! Сейчас прозвучит первая подсказка. "]
hint2_messages = ["Слушай внимательно вторую подсказку. ", "Не отвлекайся и послушай вторую подсказку. ",
                  "Внимание! Сейчас прозвучит вторая подсказка. "]
hint_max_messages = ["К сожалению все подсказки истрачены. ", "Сожалею, но подсказок не осталось. "]
not_enough_points_messages = ["Сожалею, но у вас недостаточно баллов. ", "Простите, но у вас слишком мало баллов. ",
                              "К сожалению, вам не хватает баллов. "]
zero_point_messages = ["К сожалению у вас закончились баллы, очередь переходит другому игроку. ",
                       "У вас осталось ноль баллов, я вынужден отдать ход другому игроку. ",
                       "Вы исчерпали попытки, придётся передать ход другому игроку. "]
right_answer_messages = ["Правильно! ", "Правильный ответ! ", "Молодец! Ответ правильный. ",
                         "Прекрасно, верный ответ! ",
                         "Ура! Это верный ответ! ", "Отлично! Тебе удалось дать верный ответ. "]
wrong_answer_messages = ["Подумай ещё! ", "Неверный ответ! ", "Близко, но нет! ", "Не могу принять этот ответ. ",
                         "Нет, попробуй ещё! "]
sounds = {
    "intro": '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/926ca3fc-f437-4bd8-930a-92df43e0ddb7.opus">',
    "wrong": '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/5511405a-a770-46f2-9d0e-95c553cc5a43.opus">',
    "right": '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/f9061c5d-9d81-47b2-bcd7-b7b3536e3a04.opus">',
    "next_round": '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/9543b3e9-fe57-409a-ac71-457dbfc340ee.opus">',
    'hint': '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/2fa8277a-2b70-4191-ada0-43a04165677e.opus">',
    'skip': '<speaker audio="dialogs-upload/e6769ffe-cc98-4375-bab9-c992027649b9/8a397638-5445-4c9a-a7a8-36b076cfcc78.opus">',

}
points_for_win = 5
minus_points_for_wrong_answer = 1
minus_points_for_hint = 2
max_rounds = 6
