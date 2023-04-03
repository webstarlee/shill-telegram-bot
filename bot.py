from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    MessageHandler,
    filters
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from controller.shillmaster import user_shillmaster, get_user_shillmaster
from controller.leaderboard import all_time, past_week, global_reset, update_token
from config import bot_token, group_id, leaderboard_id
from helper.emoji import emojis
import asyncio

application = ApplicationBuilder().token(bot_token).build()

async def leaderboard_update():
    while True:
        black_list = await update_token()
        if len(black_list)>0:
            for user_id in black_list:
                await application.bot.ban_chat_member(chat_id=group_id, user_id=user_id)
        global_reset()
        all_text = all_time()
        two_week = past_week(14)
        one_week = past_week(7)
        keyboard = [
            [InlineKeyboardButton(text=emojis['bangbang']+emojis['dog']+" SHILL ON GRIMACE GROUP "+emojis['dog']+emojis['bangbang'], url="https://t.me/sh13shilBot")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await application.bot.edit_message_text(chat_id=leaderboard_id, message_id=2, text=all_text, disable_web_page_preview=True, reply_markup=reply_markup, parse_mode='MARKDOWN')
        await application.bot.edit_message_text(chat_id=leaderboard_id, message_id=9, text=two_week, disable_web_page_preview=True, reply_markup=reply_markup, parse_mode='MARKDOWN')
        await application.bot.edit_message_text(chat_id=leaderboard_id, message_id=10, text=one_week, disable_web_page_preview=True, reply_markup=reply_markup, parse_mode='MARKDOWN')
        await asyncio.sleep(600)

async def start(update, context):
    chat_id = update.effective_chat.id
    start_text = emojis['v']+" Here is Bot Start "+emojis['v']+"\n\n"+emojis['point_right']+" First step shill token\nExample:\n"
    start_text += "/shill0x6f3277ad0782a7DA3eb676b85a8346A100BF9C1c\n\n"
    start_text += "You can check user's shill stats like below:\n/shillmaster@aleekk0\n\nYou can test"
    await context.bot.send_message(chat_id=chat_id, text=start_text)

def sepatate_command(text):
    command = ''
    if "shillmaster" in text:
        command='shillmaster'
    elif 'shill' in text:
        command='shill'
    param = text.replace(command, '')
    param = param.strip()
    return {'command':command, 'param': param}

async def shil_command(update, context):
    receive_text = update.message.text
    receive_text = receive_text.replace('/', '')
    command_param = sepatate_command(receive_text)
    command = command_param['command']
    param = command_param['param']
    username = update.effective_user.username
    user_id = update.effective_user.id
    payload_txt = ""
    diable_preview = False
    if command == 'shill':
        payload_txt = await user_shillmaster(param, username, user_id)
    elif command == 'shillmaster':
        payload_txt = emojis['warning']+" Please specify username like below.\n/shillmaster@username\n"
        if param != '':
            payload_txt = await get_user_shillmaster(param)
        diable_preview = True

    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text=payload_txt, disable_web_page_preview=diable_preview, parse_mode='MARKDOWN')

loop = asyncio.get_event_loop()
task = loop.create_task(leaderboard_update())

if __name__ == '__main__':
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CallbackQueryHandler(ad_button))
    application.add_handler(MessageHandler(filters.TEXT, shil_command))
    application.run_polling()

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass
