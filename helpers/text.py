from .format import format_price, percent
import db

def start_text():
    text = " ShillMasterBot Commands: \n\n"
    text += "<em>/shillcontract_address</em> : Add a project recommendation by providing its contract address; the bot tracks the project's performance since your suggestion.\n\n"
    text += "<em>/shillmaster@Username</em> : View the recommendation history and performance metrics of a specific user.\n\n"
    text += "<em>/remove_warning@Username</em> : Revoke a user's rug-shilling warning; two warnings result in an automatic group ban.\n\n"
    text += "<em>/unban@Username</em> : Unban the user who shilled two rugs.\n\n"
    text += "<em>/advertise</em> : Book advertising for your project to be displayed under the leaderboards."

    return text

def invoice_text(invoice):
    text = "✌ New Invoice ✌\n\nYour Invoice ID is:\n<code>"+str(invoice['hash'])+"</code>\n\n"
    text += "Please send "+str(invoice['quantity'])+" "+str(invoice['symbol'])+" to\n<code>"+str(invoice['address'])+"</code>\nwithin 30 minutes\n"
    text += "After completing the payment, kindly enter '/invoice' in the chat to secure your advertisement..\n"
    
    return text

def shillmaster_text(new_user_token, username, current_marketcap, project):
    
    text = ""
    if new_user_token:
        text = f"🎉 @{username} shilled\n"
        text += f"<code>{project['token']}</code>\n<a href='{project['pair_url']}' >{project['symbol']}</a>: Current marketcap: ${format_price(current_marketcap)}"
    else:
        marketcap_percent = current_marketcap/float(project['marketcap'])
        text = f"<a href='{project['pair_url']}' >{project['symbol']}</a> Already Shared marketcap: ${format_price(project['marketcap'])}\n"
        text += f"Currently: ${format_price(current_marketcap)} ({str(round(marketcap_percent, 2))}x)\n"
        if float(current_marketcap)< float(project['ath']):
            text += f"ATH: ${format_price(project['ath'])} ({percent(project['ath'], project['marketcap'])}x)\n"
        text += "\n"
    
    return text

def shillmaster_status_text(user, projects):
    return_txt = f"📊 Shillmaster stats for @{user['fullname']} 📊\n\n"
    index = 1
    for project in projects:
        pair = db.Pair.find_one({"pair_address": project['pair_address']})
        if pair != None:
            if index > 1:
                return_txt  += "=======================\n"
            if project['status'] == "active":
                return_txt += "<a href='"+project['pair_url']+"' >"+project['symbol']+"</a> Shared marketcap: $"+format_price(project['marketcap'])+"\n"
                return_txt += f"Currently: ${format_price(pair['marketcap'])} ({percent(pair['marketcap'], project['marketcap'])}x)\n"
                if float(pair['marketcap'])< float(project['ath']):
                    return_txt += f"ATH: ${format_price(project['ath'])} ({percent(project['ath'], project['marketcap'])}x)\n"
            elif project['status'] == "removed":
                return_txt += f"<a href='{project['pair_url']}' >{project['symbol']}</a> Shared marketcap: ${format_price(project['marketcap'])}\n"
                return_txt += "Currently: Liquidity removed\n"
            index += 1
    
    return return_txt