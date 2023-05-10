import logging
from bot import ShillmasterTelegramBot
import asyncio
from controller.leaderboard import token_update
from helpers.utile import pair_project_match

async def database_update():
    while True:
        # pair_project_match()
        # logging.info("callededed")
        # await asyncio.sleep(10)
        await token_update()
        await asyncio.sleep(500)

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


