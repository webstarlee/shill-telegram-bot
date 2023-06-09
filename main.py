import logging
from bot import ShillmasterBot
from helpers.util import warn_json_to_mongo

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    shillmaster_bot = ShillmasterBot()
    shillmaster_bot.run()

if __name__ == '__main__':
    main()