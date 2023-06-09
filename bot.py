import logging
import threading
import asyncio
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from telegram.error import TimedOut
from helpers.text import start_text, invoice_text
from helpers.contract import is_address
from helpers.format import am_pm_time
from controllers.shillmaster import shillmaster, shillmaster_status
from controllers.database import (
    is_admin,
    db_ban_remove,
    db_warn_update,
    db_setting_select,
    db_ban_insert,
    db_warn_remove,
    db_user_insert,
    db_group_insert,
    db_group_user_insert,
    db_setting_update,
    db_user_warn_remove,
    db_banned_user_select,
    db_task_select,
    db_group_select,
    db_group_update,
    db_group_user_select,
    db_user_update,
    db_warn_select
)
from controllers.advertise import (
    check_available_time,
    check_available_hour,
    new_advertise,
    create_invoice,
    get_invoice,
    complete_invoice,
    edit_advertise,
    get_advertise
)
from controllers.leaderboard import get_broadcasts, token_update, get_removed_pairs
from config import BOT_TOKEN, LEADERBOARD_ID, ALLBOARD_ID

NEXT = map(chr, range(10, 22))
SHOW_TIME, SHOW_HOUR = map(chr, range(8, 10))
COOSE_TOKEN = map(chr, range(8, 10))
PAYMENT = map(chr, range(8, 10))

HASH_TYPING = map(chr, range(8, 10))
TRAN_TYPING = map(chr, range(8, 10))
TEXT_TYPING = map(chr, range(8, 10))
URL_TYPING = map(chr, range(8, 10))

END = ConversationHandler.END

class ShillmasterBot:

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    def __init__(self):
        logging.info("Shillmaster Bot initialized")
        asyncio.get_event_loop().create_task(self.leaderboard())
        asyncio.get_event_loop().create_task(self.task_schedule())
        
    def split_command(self, receive_text, except_text):
        command = receive_text.replace(except_text, "")
        command = command.replace("@", "")
        command = command.strip()
        return command
    
    def is_group_chat(self, update: Update) -> bool:
        """
        Checks if the message was sent from a group chat
        """
        return update.effective_chat.type in [
            constants.ChatType.GROUP,
            constants.ChatType.SUPERGROUP
        ]
    
    def primary_insert(self, update: Update):
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        user_insert = threading.Thread(target=db_user_insert, args=(user_id, username, first_name, last_name,))
        user_insert.start()
        
        is_group = self.is_group_chat(update)
        if is_group:
            chat_id = update.effective_chat.id
            title = update.effective_chat.title
            group_insert = threading.Thread(target=db_group_insert, args=(chat_id, title,))
            group_insert.start()
            
            group_user_insert = threading.Thread(target=db_group_user_insert, args=(chat_id, user_id,))
            group_user_insert.start()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = start_text()
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
    
    async def _edit_message(self, chat_id, message_id, text, reply_markup):
        try:
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                disable_web_page_preview=True,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except telegram.error.BadRequest as e:
            if str(e).startswith("Message is not modified"):
                return
            
            if str(e).startswith("Chat not found"):
                logging.warning(f'Failed to edit message: {str(e)}')
                return
        except TimedOut:
            logging.warning("Timeout error, will try after 2 second")
            await asyncio.sleep(2)
            try:
                await self.application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.warning(f'Failed to edit message: {str(e)}')
                return

        except Exception as e:
            logging.warning(f'Failed to edit message: {str(e)}')
            return

    async def _leaderboard(self):
        broadcasts = get_broadcasts()
        advertise = get_advertise()
        reply_markup=""
        if advertise != None:
            keyboard = [
                [InlineKeyboardButton(text=f"🐶 ‼ {advertise['text']} ‼ 🐶", url=advertise['url'])],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        for item in broadcasts:
            logging.info(f"Edit Leaderboard message: {item['chat_id']} => {item['message_id']}")
            asyncio.create_task(self._edit_message(item['chat_id'], item['message_id'], item['text'], reply_markup))
            await asyncio.sleep(10)
    
    async def _leaderboard_check_remove(self):
        removed_pairs = get_removed_pairs()
        if len(removed_pairs)>0:
            for removed_pair_text in removed_pairs:
                await asyncio.sleep(5)
                await self.application.bot.send_message(chat_id=LEADERBOARD_ID, text=removed_pair_text, disable_web_page_preview=True, parse_mode='HTML')

    async def leaderboard(self):
        while True:
            # await token_update()
            # await asyncio.sleep(60)
            await self._leaderboard()
            await asyncio.sleep(60)
            await self._leaderboard_check_remove()
            await asyncio.sleep(60)
    
    async def _task_schedule(self):
        tasks = db_task_select()
        if len(tasks) > 0:
            for task in tasks:
                if task['task'] == 'ban':
                    self._block_user(task)
                elif task['task'] == 'unban':
                    self._unblock_user(task)
                await asyncio.sleep(1)
                
    async def task_schedule(self):
        while True:
            await self._task_schedule()
            await asyncio.sleep(10)
            
    async def get_chat_detail(self, chat_id):
        try:
            chat_detail = await self.application.bot.get_chat(chat_id=chat_id)
            return chat_detail
        except telegram.error.BadRequest as e:
            if str(e).startswith("Message is not modified"):
                return None
            
            if str(e).startswith("Chat not found"):
                logging.warning(f'Failed to edit message: {str(e)}')
                return
        except TimedOut:
            logging.warning("Timeout error, will try after 2 second")
            await asyncio.sleep(2)
            try:
                chat_detail = await self.application.bot.get_chat(chat_id=chat_id)
                return chat_detail
            except Exception as e:
                logging.warning(f'Failed to edit message: {str(e)}')
                return None

        except Exception as e:
            logging.warning(f'Failed to edit message: {str(e)}')
            return None
    
    async def group_details(self):
        groups = db_group_select()
        for group in groups:
            grouop_detail = await self.get_chat_detail(group['group_id'])
            if grouop_detail != None:
                group_update = threading.Thread(target=db_group_update, args=(group['group_id'], grouop_detail.title))
                group_update.start()
            await asyncio.sleep(2)
        
        logging.info("Group update complete")
            
    async def get_chat_member(self, chat_id, user_id):
        try:
            chat_detail = await self.application.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            return chat_detail
        except telegram.error.BadRequest as e:
            if str(e).startswith("Message is not modified"):
                return None
            
            if str(e).startswith("Chat not found"):
                logging.warning(f'Failed to edit message: {str(e)}')
                return
        except TimedOut:
            logging.warning("Timeout error, will try after 2 second")
            await asyncio.sleep(2)
            try:
                chat_detail = await self.application.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                return chat_detail
            except Exception as e:
                logging.warning(f'Failed to edit message: {str(e)}')
                return None

        except Exception as e:
            logging.warning(f'Failed to edit message: {str(e)}')
            return None
    
    async def chat_member_detail(self):
        group_users = db_group_user_select()
        index = 1
        for group_user in group_users:
            user_detail = await self.get_chat_member(group_user['group_id'], group_user['user_id'])
            if user_detail != None:
                user_update = threading.Thread(target=db_user_update, args=(user_detail.user,))
                user_update.start()
            await asyncio.sleep(2)
            index += 1
        logging.info("User update complete")
    
    async def _send_message(self, chat_id, text, reply_markup="", disable_preview=False):
        result = await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_preview,
                parse_mode='HTML'
            )
        return result
    
    async def _unblock_user(self, user):
        ban_remove = threading.Thread(target=db_ban_remove, args=(user,))
        ban_remove.start()
        
        await self.application.bot.unban_chat_member(chat_id=user['group_id'], user_id=user['user_id'])

    async def _block_user(self, warn):
        try:
            setting = db_setting_select(warn.group_id)
            if setting['ban_mode']:
                ban_insert = threading.Thread(target=db_ban_insert, args=(warn,))
                ban_insert.start()
                warn_remove = threading.Thread(target=db_warn_remove, args=(warn,))
                warn_remove.start()
                
                await self.application.bot.ban_chat_member(chat_id=warn.group_id, user_id=warn.user_id)
        except Exception:
            return None
    
    async def _shill_token(self, update, token, chat_id, user_id, username):
        logging.info(f"@{username} Shilling token: {token}")
        isaddress = is_address(token)
        if isaddress == False:
            return await self._send_message(chat_id, "Please insert correct token address")
        
        if username == None:
            return None
        
        response = await shillmaster(user_id, username, chat_id, token)
        
        is_group = self.is_group_chat(update)
        text = response['text']
        if response['is_rug'] and response['reason'] == "honeypot":
            user_warn = db_warn_update(user_id, chat_id)
            text += "\n\n@"+username+" warned: "+str(user_warn['count'])+" Token Rugged ❌"
            if user_warn.count > 1 and is_group:
                asyncio.get_event_loop().create_task(self._block_user(user_warn))
        
        keyboard = [
            [InlineKeyboardButton(text="Leaderboard", url="https://t.me/shillmastersleaderboard/150"), InlineKeyboardButton(text="Check Previous Shills", callback_data=f"/check_previous_shill@{username}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        is_new = response['is_new']
        if is_new:
            await self._send_message(ALLBOARD_ID, text)
            group_id = "master"
            setting = db_setting_select(group_id)
            print(setting)
            if setting != None and user_id in setting['top_users']:
                await self._send_message(LEADERBOARD_ID, text)
            
        return await self._send_message(chat_id, text, reply_markup)
    
    async def shill_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        param = self.split_command(receive_text, "/shill")
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        self.primary_insert(update)
        
        asyncio.get_event_loop().create_task(self._shill_token(update, param, chat_id, user_id, username))

        return None
    
    async def _shill_status(self, param, chat_id):
        payload_txt = shillmaster_status(param, chat_id)
        
        return await self._send_message(chat_id, payload_txt, "", True)
    
    async def shill_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        param = self.split_command(receive_text, "/shillmaster")
        self.primary_insert(update)
        asyncio.get_event_loop().create_task(self._shill_status(param, chat_id))
        
        return None

    async def _shillmaster_check(self, param, update: Update):
        chat_id = "master"
        is_group = self.is_group_chat(update)
        if is_group:
            chat_id = update.effective_chat.id
        payload_txt = shillmaster_status(param, chat_id)

        return await update.callback_query.edit_message_text(text=payload_txt, parse_mode='HTML', disable_web_page_preview=True)
    
    async def shillmaster_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        receive_text = query.data
        param = self.split_command(receive_text, "/check_previous_shill")
        param = param.replace("@", "")
        asyncio.get_event_loop().create_task(self._shillmaster_check(param, update))
        print("show shillmaster status")
        return None
    
    async def _shillmode(self, receive_text, chat_id, context: ContextTypes.DEFAULT_TYPE, update: Update):
        param = self.split_command(receive_text, "/shillmode")
        is_group = self.is_group_chat(update)
        is_shill = None
        is_shill_str = "Shillmode Turned On: You have to write /shill in front of the contract address."

        if param.lower() == "off":
            is_shill = False
            is_shill_str = "Shillmode Turned Off: You don't have to write /shill in front of the contract anymore."
        elif param.lower() == "on":
            is_shill = True
            is_shill_str = "Shillmode Turned On: You have to write /shill in front of the contract address."

        if is_shill != None:
            group_id = "master"
            if is_group:
                group_id = chat_id
            
            params = {"shill_mode": is_shill}
            setting_update = threading.Thread(target=db_setting_update, args=(group_id, params,))
            setting_update.start()
            
            return await context.bot.send_message(chat_id=chat_id, text=is_shill_str)
    
        return None
    
    async def shillmode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        iadmin = is_admin(user_id)
        if iadmin:
            asyncio.get_event_loop().create_task(self._shillmode(receive_text, chat_id, context, update))

        return None

    async def _banmode(self, receive_text, chat_id, context: ContextTypes.DEFAULT_TYPE, update: Update):
        param = self.split_command(receive_text, "/banmode")
        is_group = self.is_group_chat(update)
        is_ban = None
        is_ban_str = "Banmode Turned On: I will automatically ban users who shill 2 rugs if the admin doesn't remove the warnings."

        if param.lower() == "off":
            is_ban = False
            is_ban_str = "Banmode Turned Off: I will not ban users automatically; users who share rugs will just collect warnings, which will be displayed in the shillmaster status."
        elif param.lower() == "on":
            is_ban = True
            is_ban_str = "Banmode Turned On: I will automatically ban users who shill 2 rugs if the admin doesn't remove the warnings."

        if is_ban != None:
            group_id = "master"
            if is_group:
                group_id = chat_id

            params = {"ban_mode": is_ban}
            setting_update = threading.Thread(target=db_setting_update, args=(group_id, params,))
            setting_update.start()
            
            return await context.bot.send_message(chat_id=chat_id, text=is_ban_str)

    async def banmode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        iadmin = is_admin(user_id)
        if iadmin:
            asyncio.get_event_loop().create_task(self._banmode(receive_text, chat_id, context, update))

        return None
    
    async def _remove_warning(self, receive_text, chat_id):
        param = self.split_command(receive_text, "/remove_warning")
        user_warn_remove = threading.Thread(target=db_user_warn_remove, args=(param, chat_id,))
        user_warn_remove.start()
        
        return await self._send_message(chat_id, f"✅ Warning removed from @{param}")

    async def remove_warning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        iadmin = is_admin(user_id)
        if iadmin:
            asyncio.get_event_loop().create_task(self._remove_warning(receive_text, chat_id))

        return None
    
    async def _unban(self, receive_text, chat_id, context: ContextTypes.DEFAULT_TYPE):
        param = self.split_command(receive_text, "/unban")
        baned_user = db_banned_user_select(param, chat_id)
        text = "@"+param+" is not banned"
        if baned_user != None:
            text = f"✅ @{param} is now unbanned"
            self._unblock_user(baned_user)
            
        return await self._send_message(chat_id, text)

    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        iadmin = is_admin(user_id)
        if iadmin:
            asyncio.get_event_loop().create_task(self._unban(receive_text, chat_id, context))
        
        return None
    
    async def mode_shill_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        is_group = self.is_group_chat(update)
        group_id = "master"
        if is_group:
            group_id = chat_id
            
        setting = db_setting_select(group_id)
        
        if setting != None and setting['shill_mode'] == False:
            param = self.split_command(receive_text, "/")
            param = param[:42]
            asyncio.get_event_loop().create_task(self._shill_token(update, param, chat_id, user_id, username))

        return None
    
    async def advertise(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = "If you want to advertise your project or services under the leaderboards, click the button below."
        keyboard = [
            [InlineKeyboardButton(text="Book an Ad", callback_data=str(SHOW_TIME))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_message(chat_id, text, reply_markup, True)

        return SHOW_TIME
    
    async def show_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    first_button_text = am_pm_time(first_time)
                    row_array = []
                    first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                    row_array.append(first_button)
                    second_num = first_num+row
                    if second_num < len(available_time_list):
                        second_time = available_time_list[second_num]
                        second_button_text = am_pm_time(second_time)
                        second_button = InlineKeyboardButton(text=second_button_text+" UTC", callback_data=second_time)
                        row_array.append(second_button)
                    total_array.append(row_array)
                
                total_array.append(last_button)
                keyboard = total_array
            else:
                start_index = 0
                row = int((len(available_time_list)+1)/2)
                total_array = []
                for item in range(start_index, row+start_index):
                    first_num = item
                    first_time = available_time_list[first_num]
                    first_button_text = am_pm_time(first_time)
                    row_array = []
                    first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                    row_array.append(first_button)
                    second_num = first_num+row
                    if second_num < len(available_time_list):
                        second_time = available_time_list[second_num]
                        second_button_text = am_pm_time(second_time)
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
    
    async def show_hour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        command = query.data
        if "SHOW_TIME" in command:
            status = command.replace("SHOW_TIME", "")
            if status == "_NEXT":
                context.user_data[NEXT] = True
            else:
                context.user_data[NEXT] = False
            
            await self.show_time(update, context)
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
    
    async def choose_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            
            user_id = update.effective_user.id
            context.user_data['user_id'] = user_id
            advertise = new_advertise(context.user_data)
            invoice = create_invoice(advertise, symbol, quantity)
            
            text = invoice_text(invoice)

            await query.edit_message_text(text=text, parse_mode='HTML')

            context.user_data[NEXT] = False
            context.user_data['time'] = None
            context.user_data['hours'] = None
            context.user_data['user_id'] = None

            return END
    
    async def invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = "Please Enter your invoice ID\n"
        await self._send_message(chat_id, text, "", True)

        return HASH_TYPING
    
    async def save_hash_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _hash = update.message.text
        user_id = update.effective_user.id
        invoice = get_invoice(_hash, user_id)
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
    
    async def save_transaction_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def save_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['text'] = update.message.text
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Provide ad URL: Share the link to be accessed when the advertisement is clicked. This can be Telegram group or the Project's website.")

        return URL_TYPING

    async def save_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['url'] = update.message.text
        chat_id = update.effective_chat.id
        advertise = edit_advertise(context.user_data)
        start_date = advertise['start'].strftime('%d/%m/%Y')
        start_time_str = advertise['start'].strftime('%H')
        start_time = am_pm_time(start_time_str)
        await context.bot.send_message(chat_id=chat_id, text="Ad purchase confirmation✅\nThank you for purchasing an advertisement. Your ad will go live at: "+start_date+" "+start_time)
        context.user_data['text'] = None
        context.user_data['url'] = None
        context.user_data['transaction'] = None
        context.user_data['invoice_id'] = None
        return END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data[NEXT] = False
        context.user_data['time'] = None
        context.user_data['hours'] = None
        context.user_data['text'] = None
        context.user_data['url'] = None
        context.user_data['user_id'] = None
        context.user_data['advertise_id'] = None
        context.user_data['invoice_id'] = None
        await update.message.reply_text("Bye! I hope we can talk again some day.")

        return END
    
    def run(self):
        self.application.add_handler(CommandHandler(["start", "help"], self.start))
        self.application.add_handler(MessageHandler(filters.Regex("^/unban@(s)?"), self.unban))
        self.application.add_handler(MessageHandler(filters.Regex("^/unban @(s)?"), self.unban))
        self.application.add_handler(MessageHandler(filters.Regex("^/banmode@(s)?"), self.banmode))
        self.application.add_handler(MessageHandler(filters.Regex("^0x(s)?"), self.mode_shill_token))
        self.application.add_handler(MessageHandler(filters.Regex("^/shillmode@(s)?"), self.shillmode))
        self.application.add_handler(MessageHandler(filters.Regex("^/shill0x(s)?"), self.shill_token))
        self.application.add_handler(MessageHandler(filters.Regex("^/shill 0x(s)?"), self.shill_token))
        self.application.add_handler(MessageHandler(filters.Regex("^/shillmaster@(s)?"), self.shill_status))
        self.application.add_handler(MessageHandler(filters.Regex("^/shillmaster @(s)?"), self.shill_status))
        self.application.add_handler(MessageHandler(filters.Regex("^/remove_warning@(s)?"), self.remove_warning))
        self.application.add_handler(MessageHandler(filters.Regex("^/remove_warning @(s)?"), self.remove_warning))
        self.application.add_handler(CallbackQueryHandler(self.shillmaster_check, pattern="^/check_previous_shill?"))
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("advertise", self.advertise)],
            states={
                SHOW_TIME: [CallbackQueryHandler(self.show_time)],
                SHOW_HOUR: [CallbackQueryHandler(self.show_hour)],
                COOSE_TOKEN: [CallbackQueryHandler(self.choose_token)],
                PAYMENT: [CallbackQueryHandler(self.payment)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        ))
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("invoice", self.invoice)],
            states={
                HASH_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_hash_input)],
                TRAN_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_transaction_input)],
                TEXT_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_text_input)],
                URL_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_url_input)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        ))
        self.application.run_polling()