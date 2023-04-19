from telegram.ext import (
    ApplicationBuilder
)
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from controller.sm_controller import user_shillmaster, get_user_shillmaster, add_warn, remove_warn, get_user_warn
from controller.lb_controller import get_broadcast, token_update, add_ban_user, get_baned_user, remove_ban_user, update_leaderboard
from controller.ad_controller import get_active_advertise
from config import bot_token, leaderboard_id
from helper.emoji import emojis
from helper import (
    start_text,
    get_params,
    convert_am_str,
    convert_am_time
)

application = ApplicationBuilder().token(bot_token).build()

async def _send_message(chat_id, text, reply_markup="", disable_preview=False):
    if reply_markup == "":
        result = await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_web_page_preview=disable_preview,
                parse_mode='HTML'
            )
        return result
    else:
        result = await application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_preview,
                parse_mode='HTML'
            )
        return result

async def _block_user(user):
    await application.bot.ban_chat_member(chat_id=user['chat_id'], user_id=user['user_id'])
    add_ban_user(user)
    remove_warn(user['username'])

async def _unblock_user(user, context):
    await context.bot.unban_chat_member(chat_id=user['chat_id'], user_id=user['user_id'])
    remove_ban_user(user)

async def _leaderboard():
    black_list = await token_update()
    black_users = black_list['black_users']
    black_liquidities = black_list['black_liquidities']
    if len(black_users)>0:
        for user in black_users:
            await _block_user(user)
    
    if len(black_liquidities)>0:
        for black_liquidity in black_liquidities:
            text = "<a href='"+black_liquidity['url']+"' >"+black_liquidity['symbol']+"</a> LIQUIDITY REMOVED\n"
            text += "❌ "+black_liquidity['token']+"\n"
            if len(black_liquidity['users'])>0:
                text += "\nShilled by: "
                for black_username in black_liquidity['users']:
                    text += "@"+black_username+", "

            await _send_message(leaderboard_id, text, "", True)

    broadcasts = get_broadcast()
    advertise = get_active_advertise()
    reply_markup=""
    if advertise != None:
        keyboard = [
            [InlineKeyboardButton(text=emojis['bangbang']+emojis['dog']+" "+advertise['text']+" "+emojis['dog']+emojis['bangbang'], url=advertise['url'])],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

    for item in broadcasts:
        text = item['text']
        text += "<code>UTC:"+datetime.utcnow().strftime("%d/%m/%y")+" "+convert_am_time(datetime.utcnow().strftime("%H"))+":"+datetime.utcnow().strftime("%M")+" "+convert_am_str(datetime.utcnow().strftime("%H"))+"</code>"
        if "message_id" in item:
            try:
                if reply_markup =="":
                    await application.bot.edit_message_text(
                        chat_id=item['chat_id'],
                        message_id=item['message_id'],
                        text=text,
                        disable_web_page_preview=True,
                        parse_mode='HTML'
                    )
                else:
                    await application.bot.edit_message_text(
                        chat_id=item['chat_id'],
                        message_id=item['message_id'],
                        text=text,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            except:
                result = await _send_message(item['chat_id'], text, reply_markup, True)
                update_leaderboard(item['_id'], {"message_id": result['message_id']})
        else:
            result = await _send_message(item['chat_id'], text, reply_markup, True)
            update_leaderboard(item['_id'], {"message_id": result['message_id']})

async def help(chat_id):
    text = start_text()
    await _send_message(chat_id=chat_id, text=text)

async def shill_token_save(receive_text, chat_id, user_id, username):
    param = get_params(receive_text, "/shill")
    param = param.replace("@", "")
    response = await user_shillmaster(user_id, username, chat_id, param)
    # is_rug = response['is_rug']
    # if is_rug:
    #     user_warn = add_warn(username, user_id, chat_id)
    #     text = response['text'] + "\n\n@"+username+" warned: "+str(user_warn['count'])+" Project Rugged ❌"
    #     if user_warn['count'] > 1:
    #         text = response['text'] + "\n\n@"+username+" Banned: Posted "+str(user_warn['count'])+" Rugs ❌"
    #         await _block_user(user_warn)

    #     return await _send_message(chat_id, text)

    # payload_txt = response['text']
    # is_new = response['is_new']
    # if is_new:
    #     await _send_message(leaderboard_id, payload_txt)
    
    # return await _send_message(chat_id, payload_txt)

async def shill_token_status(receive_text, chat_id):
    param = get_params(receive_text, "/shillmaster")
    param = param.replace("@", "")
    payload_txt = await get_user_shillmaster(param)
    has_warn = get_user_warn(param)
    if has_warn != None:
        payload_txt += "\n⚠️ Has 1 Warning ⚠️"
    
    return await _send_message(chat_id, payload_txt)

async def remove_user_warning(receive_text, chat_id, user_id, context):
    param = get_params(receive_text, "/remove_warning")
    param = param.replace("@", "")
    member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if member['status'] == "creator":
        text = remove_warn(param)
        return await _send_message(chat_id, text)
    else:
        text = "Only admin can remove user's warn"
        return await _send_message(chat_id, text)
    
async def user_unblock(receive_text, chat_id, user_id, context):
    param = get_params(receive_text, "/unban")
    param = param.replace("@", "")
    member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if member['status'] == "creator":
        baned_user = get_baned_user(param)
        text = "@"+param+" is not banned"
        if baned_user != None:
            text = "@"+baned_user['username']+" is now unbanned ✅"
            _unblock_user(baned_user, context)
        return await _send_message(chat_id, text)
    else:
        text = "Only admin can unban user"
        return await _send_message(chat_id, text)
