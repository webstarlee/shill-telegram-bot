import threading
import logging
from multiprocessing.pool import Pool
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from config import bot_token, leaderboard_id
from bot import (
    shill_token_save,
    shill_token_status,
    remove_user_warning,
    user_unblock
)
import asyncio

logging.basicConfig(level=logging.DEBUG)

application = ApplicationBuilder().token(bot_token).build()

async def shill(update, context):
    receive_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    logging.debug('Token shill thread start!')
    asyncio.get_event_loop().create_task(shill_token_save(receive_text, chat_id, user_id, username))

    return None

async def shillmaster(update, context):
    receive_text = update.message.text
    chat_id = update.effective_chat.id
    asyncio.get_event_loop().create_task(shill_token_status(receive_text, chat_id))

    return None

async def remove_warning(update, context):
    receive_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    asyncio.get_event_loop().create_task(remove_user_warning(receive_text, chat_id, user_id, context))

    return None

async def unban(update, context):
    receive_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    asyncio.get_event_loop().create_task(user_unblock(receive_text, chat_id, user_id, context))
    
    return None

if __name__ == '__main__':
    application.add_handler(MessageHandler(filters.Regex("/shill0x(s)?"), shill))
    application.add_handler(MessageHandler(filters.Regex("/shill 0x(s)?"), shill))
    application.add_handler(MessageHandler(filters.Regex("/shillmaster@(s)?"), shillmaster))
    application.add_handler(MessageHandler(filters.Regex("/shillmaster @(s)?"), shillmaster))
    application.add_handler(MessageHandler(filters.Regex("/remove_warning@(s)?"), remove_warning))
    application.add_handler(MessageHandler(filters.Regex("/remove_warning @(s)?"), remove_warning))
    application.add_handler(MessageHandler(filters.Regex("/unban@(s)?"), unban))
    application.add_handler(MessageHandler(filters.Regex("/unban @(s)?"), unban))
    application.run_polling()
