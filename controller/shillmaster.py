from operator import attrgetter
from datetime import datetime
from sqlalchemy import desc
from config import Session
from model.tables import Project, Pair
from helper import (
    format_number_string,
    return_percent,
    current_marketcap,
    get_token_pairs,
    cryptocurrency_info
)
from helper.emoji import emojis
import time

db = Session()

async def user_shillmaster(token, username, user_id):
    try:
        pairs = await get_token_pairs(token)
        filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == token.lower()]
        if len(filtered_pairs) > 0:
            pair = max(filtered_pairs, key=attrgetter('liquidity.usd'))
            bot_txt = ''
            marketcap_info = await cryptocurrency_info(token)
            circulating_supply = 0
            marketcap = pair.fdv
            coin_marketcap_id = None
            if marketcap_info != None:
                for key in marketcap_info:
                    currency_info = marketcap_info[key]
                    coin_marketcap_id=currency_info['id']
                    if currency_info['self_reported_circulating_supply'] != None:
                        circulating_supply = currency_info['self_reported_circulating_supply']

            if circulating_supply != 0:
                marketcap = circulating_supply*pair.price_usd
            
            pair_project = db.query(Project).filter(Project.username == username).filter(Project.token == token).first()
            pair_token = db.query(Pair).filter(Pair.token == token).first()
            if pair_token != None:

                pair_token.marketcap = str(marketcap)
                pair_token.updated_at = datetime.now()
                db.commit()
            else:
                pair_token = Pair(
                    token=token,
                    symbol=pair.base_token.symbol,
                    pair_url=pair.url,
                    marketcap=str(marketcap),
                    coin_market_id=coin_marketcap_id
                )
                db.add(pair_token)
                db.commit()

            if pair_project != None:
                if float(marketcap)>float(pair_project.ath_value):
                    pair_project.ath_value = str(marketcap)
                    db.commit()
                marketcap_percent = marketcap/float(pair_project.marketcap)
                bot_txt = emojis['dizzy']+" ["+pair_project.token_symbol+"]("+pair.url+") Already Shared marketcap: $"+format_number_string(pair_project.marketcap)+"\n"
                bot_txt += emojis['point_right']+" Currently: $"+format_number_string(marketcap)+" ("+str(round(marketcap_percent, 2))+"x)\n"
                if float(marketcap)< float(pair_project.ath_value):
                    bot_txt += emojis['point_right']+" ATH: $"+format_number_string(pair_project.ath_value)+" ("+return_percent(pair_project.ath_value, pair_project.marketcap)+"x)\n"
                bot_txt += "\n"
            else:
                project = Project(
                    username=username,
                    user_id=user_id,
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

def clear_database():
    db.query(Pair).delete()
    db.query(Project).delete()