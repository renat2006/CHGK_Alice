import logging
import random
import psycopg2
from aioalice.utils.helper import Helper, HelperMode, Item
from aiohttp import web
from aioalice import Dispatcher, get_new_configured_app, types
from aioalice.dispatcher import MemoryStorage

WEBHOOK_URL_PATH = '/my-alice-webhook/'  # webhook endpoint

WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001
SKILL_ID = 'e6769ffe-cc98-4375-bab9-c992027649b9'
OAUTH_TOKEN = 'y0_AgAAAAAjiGoWAAT7owAAAADe4ez8G_br3guXSv2t4CeYQLObwUmlieo'

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

# Создаем экземпляр диспетчера и подключаем хранилище в памяти
dp = Dispatcher(storage=MemoryStorage(), skill_id=SKILL_ID, oauth_token=OAUTH_TOKEN)

def connect_to_db():
    import psycopg2

    conn = psycopg2.connect("""
        host=rc1b-1dkhcvps79tr5wu2.mdb.yandexcloud.net
        port=6432
        dbname=questions
        user=user1
        password=Taner2320
        target_session_attrs=read-write
    """)

    q = conn.cursor()
    q.execute('SELECT version()')

    print(q.fetchone())

    conn.close()
class GameStates(Helper):
    mode = HelperMode.snake_case

    SELECT_GAME = Item()  # = select_game
    GUESS_NUM = Item()  # = guess_num
    THIMBLES = Item()  # = thimbles

@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    print(alice_request)
    connect_to_db()
    return alice_request.response('Привет! Купи слона!', buttons=["Прив"])

if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, loop=dp.loop)
