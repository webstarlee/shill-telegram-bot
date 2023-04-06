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
from controller.ad_controller import (
    new_advertise,
    check_available_time,
    create_invoice,
    complete_invoice,
    edit_advertise,
    check_available_hour,
    get_active_advertise
)
from config import bot_token, leaderboard_id, Session
from helper.emoji import emojis
from helper import sepatate_command, check_table_exist, start_text, convert_am_pm
import asyncio

application = ApplicationBuilder().token(bot_token).build()
db = Session()
NEXT = map(chr, range(10, 22))
SHOW_HOUR, SHOW_TIME = map(chr, range(8, 10))
FINAL = map(chr, range(8, 10))
ASK_TEXT = map(chr, range(8, 10))
ASK_URL = map(chr, range(8, 10))
TEXT_TYPING = map(chr, range(8, 10))
URL_TYPING = map(chr, range(8, 10))
COOSE_TOKEN = map(chr, range(8, 10))
PAYMENT = map(chr, range(8, 10))
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
        advertise = get_active_advertise()
        reply_markup=""
        if advertise != None:
            keyboard = [
                [InlineKeyboardButton(text=emojis['bangbang']+emojis['dog']+" "+advertise.text+" "+emojis['dog']+emojis['bangbang'], url=advertise.url)],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        if len(broadcasts)>0:
            for item in broadcasts:
                broadcast = db.query(Leaderboard).filter(Leaderboard.id == item.id).first()
                if broadcast != None:
                    if broadcast.message_id:
                        try:
                            if reply_markup =="":
                                await application.bot.edit_message_text(
                                    chat_id=broadcast.chat_id,
                                    message_id=broadcast.message_id,
                                    text=broadcast.text,
                                    disable_web_page_preview=True,
                                    parse_mode='MARKDOWN'
                                )
                            else:
                                await application.bot.edit_message_text(
                                    chat_id=broadcast.chat_id,
                                    message_id=broadcast.message_id,
                                    text=broadcast.text,
                                    disable_web_page_preview=True,
                                    reply_markup=reply_markup,
                                    parse_mode='MARKDOWN'
                                )
                        except:
                            result = await send_telegram_message(broadcast.chat_id, broadcast.text, reply_markup, True)
                            broadcast.message_id = result['message_id']
                            db.commit()
                    else:
                        result = await send_telegram_message(broadcast.chat_id, broadcast.text, reply_markup, True)
                        broadcast.message_id = result['message_id']
                        db.commit()

        await asyncio.sleep(600)

async def start(update, context):
    chat_id = update.effective_chat.id
    text = start_text()
    await send_telegram_message(chat_id, text)

async def advertise(update, context):
    chat_id = update.effective_chat.id
    text = "If you want to advertise your project or services under the leaderboards, click the button below."
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
            
            row = int((len(available_time_list)+1)/2)
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
            end_index = len(available_time_list)
            row = int((len(available_time_list)+1)/2)
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
        await query.edit_message_text(text="When do you want the advertisement to begin being displayed?", reply_markup=time_markup)

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
        hours_array = check_available_hour(int(command))
        keyboard = []
        for hour in hours_array:
            budget_text = ""
            if hour == 2:
                budget_text = "2 Hours - 0.005 ETH / 0.01 BNB"
            elif hour == 4:
                budget_text = "4 Hours - 0.01 ETH / 0.02 BNB"
            elif hour == 8:
                budget_text = "8 Hours - 0.02 ETH / 0.04 BNB"
            elif hour == 12:
                budget_text = "12 Hours - 0.04 ETH / 0.08 BNB"
            elif hour == 24:
                budget_text = "24 Hours - 0.08 ETH / 0.16 BNB"
            single_hour_array = [InlineKeyboardButton(text=budget_text, callback_data=hour)]
            keyboard.append(single_hour_array)

        hour_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose HOUR", reply_markup=hour_markup)

        return COOSE_TOKEN

async def choose_token(update, context):
    query = update.callback_query
    keyboard=[]
    await query.answer()
    hours = int(query.data)
    print("hours: ", hours)
    context.user_data['hours'] = hours
    if hours==2:
        print("call here 2")
        keyboard = [
            [
                InlineKeyboardButton(text="0.015 ETH", callback_data="0.001ETH"),
                InlineKeyboardButton(text="0.09 BNB", callback_data="0.003BNB")
            ],
        ]
    elif hours==4:
        keyboard = [
            [
                InlineKeyboardButton(text="0.015 ETH", callback_data="0.001ETH"),
                InlineKeyboardButton(text="0.09 BNB", callback_data="0.003BNB")
            ],
        ]
    elif hours == 8:
        keyboard = [
            [
                InlineKeyboardButton(text="0.015 ETH", callback_data="0.001ETH"),
                InlineKeyboardButton(text="0.09 BNB", callback_data="0.003BNB")
            ],
        ]
    elif hours == 12:
        keyboard = [
            [
                InlineKeyboardButton(text="0.015 ETH", callback_data="0.001ETH"),
                InlineKeyboardButton(text="0.09 BNB", callback_data="0.003BNB")
            ],
        ]
    elif hours==24:
        keyboard = [
            [
                InlineKeyboardButton(text="0.015 ETH", callback_data="0.001ETH"),
                InlineKeyboardButton(text="0.09 BNB", callback_data="0.003BNB")
            ],
        ]
    token_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Please choose Token", reply_markup=token_markup)

    return PAYMENT

async def payment(update, context):
    query = update.callback_query
    await query.answer()
    param = query.data
    symbol=""
    quantity=""
    if "ETH" in param:
        symbol = "ETH"
        quantity = param.replace("ETH", "")

    if "BNB" in param:
        symbol = "BNB"
        quantity = param.replace("BNB", "")
    
    username = update.effective_user.username
    context.user_data['username'] = username
    advertise = new_advertise(context.user_data)
    invoice = create_invoice(advertise, symbol, quantity)

    text = "Please send "+str(invoice.quantity)+" "+str(invoice.symbol)+" to\n<pre>"+str(invoice.address)+"</pre>\nwithin 30 minutes\n"
    text += "After Complete payment, you will get message for next step.\n\n"
    text += "I am waiting your payment."

    await query.edit_message_text(text=text, parse_mode='HTML')
    is_complete = False
    index=0
    while True:
        index += 1
        is_complete = complete_invoice(invoice)
        if is_complete:
            break

        if index == 400:
            break
        await asyncio.sleep(10)

    if is_complete:
        context.user_data['advertise_id'] = advertise.id
        context.user_data['invoice_id'] = invoice.id
        await query.edit_message_text(text="Payment Accepted\nProvide text for the button ad, up to a maximum of 30 characters.")

        return TEXT_TYPING
    else:
        context.user_data[NEXT] = False
        context.user_data['time'] = None
        context.user_data['hours'] = None
        context.user_data['text'] = None
        context.user_data['url'] = None
        context.user_data['username'] = None
        return END

async def save_text_input(update, context):
    context.user_data['text'] = update.message.text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Provide ad URL: Share the link to be accessed when the advertisement is clicked. This can be Telegram group or the Project's website.")

    return URL_TYPING

async def save_url_input(update, context):
    context.user_data['url'] = update.message.text
    chat_id = update.effective_chat.id
    edit_advertise(context.user_data)
    await context.bot.send_message(chat_id=chat_id, text="Ad purchase confirmation: Thank you for purchasing an advertisement.")
    context.user_data[NEXT] = False
    context.user_data['time'] = None
    context.user_data['hours'] = None
    context.user_data['text'] = None
    context.user_data['url'] = None
    context.user_data['username'] = None
    context.user_data['advertise_id'] = None
    context.user_data['invoice_id'] = None
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
    context.user_data[NEXT] = False
    context.user_data['time'] = None
    context.user_data['hours'] = None
    context.user_data['text'] = None
    context.user_data['url'] = None
    context.user_data['username'] = None
    context.user_data['advertise_id'] = None
    context.user_data['invoice_id'] = None
    await update.message.reply_text(
        "Bye! I hope we can talk again some day."
    )

    return END

loop = asyncio.get_event_loop()
task = loop.create_task(leaderboard())

if __name__ == '__main__':
    ad_handler = ConversationHandler(
        entry_points=[CommandHandler("advertise", advertise)],
        states={
            SHOW_TIME: [CallbackQueryHandler(show_time)],
            SHOW_HOUR: [CallbackQueryHandler(show_hour)],
            COOSE_TOKEN: [CallbackQueryHandler(choose_token)],
            PAYMENT: [CallbackQueryHandler(payment)],
            TEXT_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_text_input)],
            URL_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_url_input)],
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
