import logging
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import bot_token
from controller.ad_controller import (
    new_advertise,
    check_available_time,
    create_invoice,
    complete_invoice,
    edit_advertise,
    check_available_hour,
    get_active_advertise,
    get_invoice
)
from bot import (
    help,
    shill_token_save,
    shill_token_status,
    remove_user_warning,
    user_unblock,
    _send_message,
    _leaderboard
)
from helper import convert_am_pm
import asyncio

logging.basicConfig(level=logging.DEBUG)

application = ApplicationBuilder().token(bot_token).build()
NEXT = map(chr, range(10, 22))
SHOW_HOUR, SHOW_TIME = map(chr, range(8, 10))
TEXT_TYPING = map(chr, range(8, 10))
URL_TYPING = map(chr, range(8, 10))
COOSE_TOKEN = map(chr, range(8, 10))
PAYMENT = map(chr, range(8, 10))
HASH_TYPING = map(chr, range(8, 10))
TRAN_TYPING = map(chr, range(8, 10))
END = ConversationHandler.END

async def start(update, context):
    chat_id = update.effective_chat.id
    asyncio.get_event_loop().create_task(help(chat_id))

async def leaderboard():
    while True:
        asyncio.get_event_loop().create_task(_leaderboard())
        await asyncio.sleep(100)

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

async def cancel(update, context):
    context.user_data[NEXT] = False
    context.user_data['time'] = None
    context.user_data['hours'] = None
    context.user_data['text'] = None
    context.user_data['url'] = None
    context.user_data['username'] = None
    context.user_data['advertise_id'] = None
    context.user_data['invoice_id'] = None
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return END

async def advertise(update, context):
    chat_id = update.effective_chat.id
    text = "If you want to advertise your project or services under the leaderboards, click the button below."
    keyboard = [
        [InlineKeyboardButton(text="Book an Ad", callback_data=str(SHOW_TIME))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await _send_message(chat_id, text, reply_markup, True)

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
            
            row = int((end_index-start_index+1)/2)
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
            cancel_button = [InlineKeyboardButton(text="CANCEL", callback_data="CANCEL_CONV")]
            keyboard.append(cancel_button)
        time_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="When do you want the advertisement to begin being displayed?", reply_markup=time_markup)

        return SHOW_HOUR
    else:
        await query.edit_message_text(text="Sorry there are no available ads for today.")

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
    elif "CANCEL_CONV" in command:
        await query.edit_message_text(text="Bye! I hope we can talk again some day.")

        return END
    else:
        context.user_data['time'] = command
        hours_array = check_available_hour(int(command))
        keyboard = []
        for hour in hours_array:
            budget_text = ""
            if hour == 2:
                budget_text = "2 Hours - 0.075 ETH / 0.45 BNB"
            elif hour == 4:
                budget_text = "4 Hours - 0.13 ETH / 0.78 BNB"
            elif hour == 8:
                budget_text = "8 Hours - 0.2 ETH / 1.2 BNB"
            elif hour == 12:
                budget_text = "12 Hours - 0.3 ETH / 1.8 BNB"
            elif hour == 24:
                budget_text = "24 Hours - 0.5 ETH / 3 BNB"
            single_hour_array = [InlineKeyboardButton(text=budget_text, callback_data=hour)]
            keyboard.append(single_hour_array)

        hour_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose", reply_markup=hour_markup)

        return COOSE_TOKEN

async def choose_token(update, context):
    query = update.callback_query
    keyboard=[]
    await query.answer()
    hours = int(query.data)
    context.user_data['hours'] = hours
    if hours==2:
        keyboard = [
            [
                InlineKeyboardButton(text="0.075 ETH", callback_data="0.075ETH"),
                InlineKeyboardButton(text="0.45 BNB", callback_data="0.45BNB")
            ],
        ]
    elif hours==4:
        keyboard = [
            [
                InlineKeyboardButton(text="0.13 ETH", callback_data="0.13ETH"),
                InlineKeyboardButton(text="0.78 BNB", callback_data="0.78BNB")
            ],
        ]
    elif hours == 8:
        keyboard = [
            [
                InlineKeyboardButton(text="0.2 ETH", callback_data="0.2ETH"),
                InlineKeyboardButton(text="1.2 BNB", callback_data="1.2BNB")
            ],
        ]
    elif hours == 12:
        keyboard = [
            [
                InlineKeyboardButton(text="0.3 ETH", callback_data="0.3ETH"),
                InlineKeyboardButton(text="1.8 BNB", callback_data="1.8BNB")
            ],
        ]
    elif hours==24:
        keyboard = [
            [
                InlineKeyboardButton(text="0.5 ETH", callback_data="0.5ETH"),
                InlineKeyboardButton(text="3 BNB", callback_data="3BNB")
            ],
        ]
    cancel_button = [InlineKeyboardButton(text="CANCEL", callback_data="CANCEL_CONV")]
    keyboard.append(cancel_button)
    token_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Please choose", reply_markup=token_markup)

    return PAYMENT

async def payment(update, context):
    query = update.callback_query
    await query.answer()
    param = query.data
    if "CANCEL_CONV" in param:
        await query.edit_message_text(text="Bye! I hope we can talk again some day.")

        return END
    else:
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

        text = "✌ New Invoice ✌\n\nYour Invoice ID is:\n<code>"+str(invoice['hash'])+"</code>\n\n"
        text += "Please send "+str(invoice['quantity'])+" "+str(invoice['symbol'])+" to\n<code>"+str(invoice['address'])+"</code>\nwithin 30 minutes\n"
        text += "After completing the payment, kindly enter '/invoice' in the chat to secure your advertisement..\n"

        await query.edit_message_text(text=text, parse_mode='HTML')

        context.user_data[NEXT] = False
        context.user_data['time'] = None
        context.user_data['hours'] = None
        context.user_data['username'] = None

        return END

async def invoice(update, context):
    chat_id = update.effective_chat.id
    text = "Please Enter your invoice ID\n"
    await _send_message(chat_id, text, "", True)

    return HASH_TYPING

async def save_hash_input(update, context):
    hash = update.message.text
    username = update.effective_user.username
    invoice = get_invoice(hash, username)
    chat_id = update.effective_chat.id
    if invoice != None:
        context.user_data['invoice_id'] = invoice['_id']
        text = "Perfect. Now Please input your transaction ID"
        await context.bot.send_message(chat_id=chat_id, text=text)
        return TRAN_TYPING
    else:
        text = "Sorry, We can not find your Invoice."
        await context.bot.send_message(chat_id=chat_id, text=text)
        return END

async def save_transaction_input(update, context):
    transaction = update.message.text
    context.user_data['transaction'] = transaction
    is_complete = complete_invoice(context.user_data)
    chat_id = update.effective_chat.id
    if is_complete:
        await context.bot.send_message(chat_id=chat_id, text="Payment Accepted\nProvide text for the button ad, up to a maximum of 30 characters.")

        return TEXT_TYPING
    else:
        await context.bot.send_message(chat_id=chat_id, text="Payment can not be Accepted\nPlease Make correct payment.")

        return END

async def save_text_input(update, context):
    context.user_data['text'] = update.message.text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Provide ad URL: Share the link to be accessed when the advertisement is clicked. This can be Telegram group or the Project's website.")

    return URL_TYPING

async def save_url_input(update, context):
    context.user_data['url'] = update.message.text
    chat_id = update.effective_chat.id
    advertise = edit_advertise(context.user_data)
    start_date = advertise['start'].strftime('%d/%m/%Y')
    start_time_str = advertise['start'].strftime('%H')
    start_time = convert_am_pm(start_time_str)
    await context.bot.send_message(chat_id=chat_id, text="Ad purchase confirmation✅\nThank you for purchasing an advertisement. Your ad will go live at: "+start_date+" "+start_time)
    context.user_data['text'] = None
    context.user_data['url'] = None
    context.user_data['transaction'] = None
    context.user_data['invoice_id'] = None
    return END

loop = asyncio.get_event_loop()
task = loop.create_task(leaderboard())

if __name__ == '__main__':
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(MessageHandler(filters.Regex("/shill0x(s)?"), shill))
    application.add_handler(MessageHandler(filters.Regex("/shill 0x(s)?"), shill))
    application.add_handler(MessageHandler(filters.Regex("/shillmaster@(s)?"), shillmaster))
    application.add_handler(MessageHandler(filters.Regex("/shillmaster @(s)?"), shillmaster))
    application.add_handler(MessageHandler(filters.Regex("/remove_warning@(s)?"), remove_warning))
    application.add_handler(MessageHandler(filters.Regex("/remove_warning @(s)?"), remove_warning))
    application.add_handler(MessageHandler(filters.Regex("/unban@(s)?"), unban))
    application.add_handler(MessageHandler(filters.Regex("/unban @(s)?"), unban))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("advertise", advertise)],
        states={
            SHOW_TIME: [CallbackQueryHandler(show_time)],
            SHOW_HOUR: [CallbackQueryHandler(show_hour)],
            COOSE_TOKEN: [CallbackQueryHandler(choose_token)],
            PAYMENT: [CallbackQueryHandler(payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("invoice", invoice)],
        states={
            HASH_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_hash_input)],
            TRAN_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_transaction_input)],
            TEXT_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_text_input)],
            URL_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_url_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    application.run_polling()

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass