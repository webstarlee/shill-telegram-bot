from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from controller.sm_controller import user_shillmaster, get_user_shillmaster, clear_database
from controller.lb_controller import get_broadcast, token_update, Leaderboard
from config import bot_token, leaderboard_id, Session
from helper.emoji import emojis
from helper import sepatate_command, check_table_exist, start_text
import asyncio

application = ApplicationBuilder().token(bot_token).build()
db = Session()

async def send_telegram_message(chat_id, text, reply_markup="", disable_preview=False):
    if reply_markup == "":
        result = await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_web_page_preview=disable_preview,
                parse_mode='MARKDOWN'
            )
        return result
    else:
        result = await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
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
                            result = await send_telegram_message(broadcast.chat_id, broadcast.text, "", True)
                            broadcast.message_id = result['message_id']
                            db.commit()
                    else:
                        result = await send_telegram_message(broadcast.chat_id, broadcast.text, "", True)
                        broadcast.message_id = result['message_id']
                        db.commit()

        await asyncio.sleep(600)

async def start(update, context):
    chat_id = update.effective_chat.id
    text = start_text()
    await send_telegram_message(chat_id, text)

async def advertise(update, context):
    chat_id = update.effective_chat.id
    text = emojis['v']+" Thank you for enquiring about advertising.\n What would you like to do today?"
    keyboard = [
        [InlineKeyboardButton(text="Book an Ad (Info if there is time for ad or not in the next 3 days)", callback_data="show_time")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_telegram_message(chat_id, text, reply_markup, True)


async def button(update, context):
    query = update.callback_query

    await query.answer()
    command = query.data
    if command == "show_time":
        keyboard = [
            [InlineKeyboardButton(text="6PM UTC", callback_data="SELECTED_TIME_6")],
            [InlineKeyboardButton(text="7PM UTC", callback_data="SELECTED_TIME_7")],
            [InlineKeyboardButton(text="8PM UTC", callback_data="SELECTED_TIME_8")],
            [InlineKeyboardButton(text="9PM UTC", callback_data="SELECTED_TIME_9")],
        ]
        time_select_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose TIME", reply_markup=time_select_markup)
    if "SELECTED_TIME" in command:
        keyboard = [
            [InlineKeyboardButton(text="2HOURS (0.1ETH/ 5.9BNB)", callback_data="SELECTED_CRYPTO_2")],
            [InlineKeyboardButton(text="4HOURS (0.19ETH/ 10.64BNB)", callback_data="SELECTED_CRYPTO_4")],
            [InlineKeyboardButton(text="8HOURS (0.36ETH/ 20.16BNB)", callback_data="SELECTED_CRYPTO_8")],
            [InlineKeyboardButton(text="12HOURS (0.51ETH/ 28.56BNB)", callback_data="SELECTED_CRYPTO_12")],
            [InlineKeyboardButton(text="24HOURS (0.96ETH/ 53.76BNB)", callback_data="SELECTED_CRYPTO_24")],
        ]
        time_select_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose HOURS", reply_markup=time_select_markup)
    
    if "SELECTED_CRYPTO" in command:
        await query.edit_message_text(text="From here need to integrate the crypto payment gateway")

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
    application.add_handler(CommandHandler("advertise", advertise))
    application.add_handler(CommandHandler("emptydb", empty_database))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT, shil_command))
    application.run_polling()

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass
