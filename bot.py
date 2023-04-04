from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from controller.sm_controller import user_shillmaster, get_user_shillmaster, clear_database
from controller.lb_controller import get_broadcast, token_update, Leaderboard
from config import bot_token, leaderboard_id, Session
from helper.emoji import emojis
from helper import sepatate_command, check_table_exist
import asyncio

application = ApplicationBuilder().token(bot_token).build()
db = Session()

async def send_telegram_message(chat_id, text, disable_preview=False):
    result = await application.bot.send_message(
            chat_id=chat_id,
            text=text,
            disable_web_page_preview=disable_preview,
            parse_mode='MARKDOWN'
        )
    return result

async def leaderboard():
    check_table_exist()
    while True:
        black_list = await token_update()
        if len(black_list)>0:
            for user in black_list:
                print(user)
                await application.bot.ban_chat_member(chat_id=user['group_id'], user_id=user['user_id'])

        broadcasts = get_broadcast()

        print(broadcasts)
        # keyboard = [
        #     [InlineKeyboardButton(text=emojis['bangbang']+emojis['dog']+" SHILL ON GRIMACE GROUP "+emojis['dog']+emojis['bangbang'], url="https://t.me/sh13shilBot")],
        # ]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        
        if len(broadcasts)>0:
            for item in broadcasts:
                broadcast = db.query(Leaderboard).filter(Leaderboard.id == item.id).first()
                if broadcast != None:
                    if broadcast.message_id:
                        try:
                            await application.bot.edit_message_text(
                                chat_id=broadcast.chat_id,
                                message_id=broadcast.message_id,
                                text=broadcast.text,
                                disable_web_page_preview=True,
                                parse_mode='MARKDOWN'
                            )
                        except:
                            result = await send_telegram_message(broadcast.chat_id, broadcast.text, True)
                            broadcast.message_id = result['message_id']
                            db.commit()
                    else:
                        result = await send_telegram_message(broadcast.chat_id, broadcast.text, True)
                        broadcast.message_id = result['message_id']
                        db.commit()

        await asyncio.sleep(600)

async def start(update, context):
    chat_id = update.effective_chat.id
    start_text = " ShillMasterBot Commands: \n\n"
    start_text += "/shill <contract_address>: Add a project recommendation by providing its contract address; the bot tracks the project's performance since your suggestion.\n\n"
    start_text += "/shillmaster@Username: View the recommendation history and performance metrics of a specific user."
    await send_telegram_message(chat_id, start_text)

async def empty_database(update, context):
    clear_database()
    chat_id = update.effective_chat.id
    text = "Delete all data from database"
    await send_telegram_message(chat_id, text)

async def shil_command(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username

    receive_text = update.message.text
    receive_text = receive_text.replace('/', '')
    command_param = sepatate_command(receive_text)
    command = command_param['command']
    param = command_param['param']
    payload_txt = ""
    
    if command == 'shillmaster':
        payload_txt = emojis['warning']+" Please specify username like below.\n/shillmaster@username\n"
        if param != '':
            payload_txt = await get_user_shillmaster(param)
    elif command == 'shill':
        payload = await user_shillmaster(user_id, username, chat_id, param)
        payload_txt = payload['text']
        is_new = payload['is_new']
        if is_new:
            await send_telegram_message(leaderboard_id, payload_txt)
    
    await send_telegram_message(chat_id, payload_txt)

loop = asyncio.get_event_loop()
task = loop.create_task(leaderboard())

if __name__ == '__main__':
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("emptydb", empty_database))
    application.add_handler(MessageHandler(filters.TEXT, shil_command))
    application.run_polling()

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass
