from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from controller.sm_controller import user_shillmaster, get_user_shillmaster, clear_database
from controller.lb_controller import get_broadcast, token_update, Leaderboard
from controller.ad_controller import new_advertise, check_available_time
from config import bot_token, leaderboard_id, Session
from helper.emoji import emojis
from helper import sepatate_command, check_table_exist, start_text, convert_am_pm
import asyncio

application = ApplicationBuilder().token(bot_token).build()
db = Session()
NEXT = map(chr, range(10, 22))
SHOW_HOUR, SHOW_TIME = map(chr, range(8, 10))
FINAL = map(chr, range(8, 10))
END = ConversationHandler.END

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
        [InlineKeyboardButton(text="Book an Ad (Info if there is time for ad or not in the next 3 days)", callback_data=str(SHOW_TIME))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_telegram_message(chat_id, text, reply_markup, True)

    return SHOW_TIME

async def show_time(update, context):
    available_time_list = check_available_time()
    keyboard = []
    query = update.callback_query
    if len(available_time_list)>0:
        if len(available_time_list)>12:
            start_index = 0
            end_index = 12
            last_button = [InlineKeyboardButton(text="NEXT", callback_data="SHOW_TIME_NEXT")]
            if context.user_data.get(NEXT):
                start_index = 12
                end_index = len(available_time_list)
                last_button = [InlineKeyboardButton(text="BACK", callback_data="SHOW_TIME")]
            
            start_number = int(available_time_list[start_index])
            end_number = int(available_time_list[end_index-1])
            row = (end_number-start_number)/2+1
            total_array = []
            for item in range(start_index, row+start_index):
                first_num = item
                first_time = available_time_list[first_num]
                first_button_text = convert_am_pm(first_time)
                row_array = []
                first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                row_array.append(first_button)
                second_num = first_num+row
                if second_num < len(available_time_list):
                    second_time = available_time_list[second_num]
                    second_button_text = convert_am_pm(second_time)
                    second_button = InlineKeyboardButton(text=second_button_text+" UTC", callback_data=second_time)
                    row_array.append(second_button)
                total_array.append(row_array)
            
            total_array.append(last_button)
            keyboard = total_array
        else:
            start_index = 0
            start_number = int(available_time_list[start_index])
            end_index = len(available_time_list)
            end_number = int(available_time_list[end_index-1])
            row = int((end_number-start_number)/2)+1
            total_array = []
            for item in range(start_index, row+start_index):
                first_num = item
                first_time = available_time_list[first_num]
                first_button_text = convert_am_pm(first_time)
                row_array = []
                first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                row_array.append(first_button)
                second_num = first_num+row
                if second_num < len(available_time_list):
                    second_time = available_time_list[second_num]
                    second_button_text = convert_am_pm(second_time)
                    second_button = InlineKeyboardButton(text=second_button_text+" UTC", callback_data=second_time)
                    row_array.append(second_button)
                total_array.append(row_array)
            
            keyboard = total_array
        time_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose TIME", reply_markup=time_markup)

        return SHOW_HOUR
    else:
        await query.edit_message_text(text="Sorry There is no available ad for today")

        return END

async def show_hour(update, context):
    query = update.callback_query
    await query.answer()
    command = query.data
    if "SHOW_TIME" in command:
        status = command.replace("SHOW_TIME", "")
        if status == "_NEXT":
            context.user_data[NEXT] = True
        else:
            context.user_data[NEXT] = False
        
        await show_time(update, context)
    else:
        context.user_data['time'] = command
        keyboard = [
            [InlineKeyboardButton(text="2 Hours - 0.075 ETH / 0.45 BNB", callback_data=2)],
            [InlineKeyboardButton(text="4 Hours - 0.075 ETH / 0.45 BNB", callback_data=4)],
            [InlineKeyboardButton(text="8 Hours - 0.075 ETH / 0.45 BNB", callback_data=8)],
            [InlineKeyboardButton(text="12 Hours - 0.075 ETH / 0.45 BNB", callback_data=12)],
            [InlineKeyboardButton(text="24 Hours - 0.075 ETH / 0.45 BNB", callback_data=24)],
        ]
        hour_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose HOUR", reply_markup=hour_markup)

        return FINAL

async def finalize(update, context):
    query = update.callback_query
    await query.answer()
    username = update.effective_user.username
    context.user_data['hours'] = query.data
    context.user_data['username'] = username
    new_advertise(context.user_data)
    await query.edit_message_text(text="Thank you for purchase ad")
    context.user_data[NEXT] = False
    context.user_data['time'] = None
    context.user_data['hours'] = None
    context.user_data['username'] = None

    return END

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
            await send_telegram_message(chat_id, payload_txt)
    elif command == 'shill':
        payload = await user_shillmaster(user_id, username, chat_id, param)
        payload_txt = payload['text']
        is_new = payload['is_new']
        await send_telegram_message(chat_id, payload_txt)
        if is_new:
            await send_telegram_message(leaderboard_id, payload_txt)

async def cancel(update, context):
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END

loop = asyncio.get_event_loop()
task = loop.create_task(leaderboard())

if __name__ == '__main__':
    ad_handler = ConversationHandler(
        entry_points=[CommandHandler("advertise", advertise)],
        states={
            SHOW_TIME: [CallbackQueryHandler(show_time)],
            SHOW_HOUR: [CallbackQueryHandler(show_hour)],
            FINAL: [CallbackQueryHandler(finalize)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(ad_handler)
    application.add_handler(CommandHandler("emptydb", empty_database))
    application.add_handler(MessageHandler(filters.TEXT, shil_command))
    application.run_polling()

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass
