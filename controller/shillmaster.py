from operator import attrgetter
from sqlalchemy import desc
from config import Session
from model.tables import Project
from helper import (
    format_number_string,
    return_percent,
    current_marketcap,
    get_token_pairs,
    cryptocurrency_info
)
from helper.emoji import emojis

db = Session()

async def user_shillmaster(token, username):
    try:
        pairs = await get_token_pairs(token)
        filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == token.lower()]
        if len(filtered_pairs) > 0:
            pair = max(filtered_pairs, key=attrgetter('liquidity.usd'))
            bot_txt = ''
            marketcap_info = await cryptocurrency_info(token)
            circulating_supply = 0
            marketcap = pair.fdv
            if marketcap_info != None:
                for key in marketcap_info:
                    currency_info = marketcap_info[key]
                    if currency_info['self_reported_circulating_supply'] != None:
                        circulating_supply = currency_info['self_reported_circulating_supply']

            if circulating_supply != 0:
                marketcap = circulating_supply*pair.price_usd
            
            token_pair = db.query(Project).filter(Project.username == username).filter(Project.token == token).first()
            if token_pair != None:
                if float(marketcap)>float(token_pair.ath_value):
                    token_pair.ath_value = str(marketcap)
                    db.commit()
                marketcap_percent = marketcap/float(token_pair.marketcap)
                bot_txt = emojis['dizzy']+" ["+token_pair.token_symbol+"]("+pair.url+") Already Shared marketcap: $"+format_number_string(token_pair.marketcap)+"\n"
                bot_txt += emojis['point_right']+" Currently: $"+format_number_string(marketcap)+" ("+str(round(marketcap_percent, 2))+"x)\n"
                if float(marketcap)< float(token_pair.ath_value):
                    bot_txt += emojis['point_right']+" ATH: $"+format_number_string(token_pair.ath_value)+" ("+return_percent(token_pair.ath_value, token_pair.marketcap)+"x)\n"
                bot_txt += "\n"
            else:
                project = Project(
                    username=username,
                    url=pair.url,
                    token=token,
                    token_symbol=pair.base_token.symbol,
                    marketcap=marketcap,
                    ath_value=marketcap
                )
                db.add(project)
                db.commit()
                bot_txt = emojis['tada']+" @"+username+" shilled\n"
                bot_txt += emojis['point_right']+" "+token+"\n"+emojis['point_right']+" [" + pair.base_token.symbol+"]("+pair.url+")- Current marketcap: $"+format_number_string(marketcap)
 
        return bot_txt
    except:
        bot_txt="There is no liquidity for this token"
        return bot_txt

async def get_user_shillmaster(user):
    return_txt = "❗ There is not any shill yet for "+user
    username = user.replace("@", "")
    user_shills = db.query(Project).filter(Project.username == username).order_by(desc(Project.created_at)).limit(5).all()
    if len(user_shills)>0:
        return_txt = emojis['frog']+" Shillmaster stats for "+user+" "+emojis['frog']+"\n\n"
        for project in user_shills:
            return_txt += emojis['frog']+" ["+project.token_symbol+"]("+project.url+") Shared marketcap: $"+format_number_string(project.marketcap)+"\n"
            current_info = await current_marketcap(project)
            if float(current_info['marketcap'])>float(project.ath_value):
                project.ath_value = current_info['marketcap']
                db.commit()
            if current_info['is_liquidity']:
                return_txt += emojis['point_right']+" Currently: $"+format_number_string(current_info['marketcap'])+" ("+str(round(current_info['percent'], 2))+"x)\n"
                if float(current_info['marketcap'])< float(project.ath_value):
                    return_txt += emojis['point_right']+" ATH: $"+format_number_string(project.ath_value)+" ("+return_percent(project.ath_value, project.marketcap)+"x)\n"
                return_txt += "\n"
            else:
                return_txt += "Currently: LIQUIDITY REMOVED / HONEYPOT"

    return return_txt