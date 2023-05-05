import logging
from bot import ShillmasterTelegramBot
import asyncio
from controller.leaderboard import token_update
from helpers.utile import mongo_db_init

async def database_update():
    while True:
        mongo_db_init()
        await asyncio.sleep(10)
        await token_update()
        await asyncio.sleep(300)

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    loop = asyncio.get_event_loop()
    loop.create_task(database_update())

    shillmaster_bot = ShillmasterTelegramBot()
    shillmaster_bot.run()

if __name__ == '__main__':
    main()


