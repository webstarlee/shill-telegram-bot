from operator import attrgetter
from datetime import datetime
from sqlalchemy import desc
from config import Session
from model.tables import Project, Pair, Leaderboard, Warn
from helper import (
    format_number_string,
    return_percent,
    current_status,
    get_token_pairs,
    cryptocurrency_info,
    go_plus_token_info
)
from helper.emoji import emojis

db = Session()

async def user_shillmaster(user_id, username, chat_id, token):
    try:
        pairs = await get_token_pairs(token)
        filtered_pairs = []
        if len(pairs) > 0:
            filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == token.lower()]

        pair = None
        if len(filtered_pairs) > 0:
            pair = max(filtered_pairs, key=attrgetter('liquidity.usd'))
        
        if pair == None:
            return {"is_rug": True, "reason": "liquidity", "text": "There is no Liquidity for this Token"}
        
        if int(pair.liquidity.usd) < 100:
            project = Project(
                username=username,
                user_id=user_id,
                chat_id=chat_id,
                url=pair.url,
                token=token,
                token_symbol=pair.base_token.symbol,
                marketcap="0",
                ath_value="0",
                status="no_liquidity"
            )
            db.add(project)
            db.commit()
            text = "There is no Liquidity for "+pair.base_token.symbol+" Token"
            return {"is_rug": True, "reason": "liquidity", "text": text}
        
        token_security = await go_plus_token_info(token, pair.chain_id)
        is_honeypot = False
        if token_security != None and token_security['is_honeypot'] == "1":
            is_honeypot = True
        
        if is_honeypot:
            project = Project(
                username=username,
                user_id=user_id,
                chat_id=chat_id,
                url=pair.url,
                token=token,
                token_symbol=pair.base_token.symbol,
                marketcap="0",
                ath_value="0",
                status="honeypot"
            )
            db.add(project)
            db.commit()
            text = pair.base_token.symbol+" Token look like honeypot"
            return {"is_rug": True, "reason": "honeypot", "text": text}

        bot_txt = ''
        is_new = True
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
            is_new = False
            if float(marketcap)>float(pair_project.ath_value):
                pair_project.ath_value = str(marketcap)
                db.commit()
            marketcap_percent = marketcap/float(pair_project.marketcap)
            bot_txt = emojis['dizzy']+" <a href='"+pair.url+"' >"+pair_project.token_symbol+"</a> Already Shared marketcap: $"+format_number_string(pair_project.marketcap)+"\n"
            bot_txt += emojis['point_right']+" Currently: $"+format_number_string(marketcap)+" ("+str(round(marketcap_percent, 2))+"x)\n"
            if float(marketcap)< float(pair_project.ath_value):
                bot_txt += emojis['point_right']+" ATH: $"+format_number_string(pair_project.ath_value)+" ("+return_percent(pair_project.ath_value, pair_project.marketcap)+"x)\n"
            bot_txt += "\n"
        else:
            project = Project(
                username=username,
                user_id=user_id,
                chat_id=chat_id,
                url=pair.url,
                token=token,
                token_symbol=pair.base_token.symbol,
                marketcap=marketcap,
                ath_value=marketcap
            )
            db.add(project)
            db.commit()
            bot_txt = emojis['tada']+" @"+username+" shilled\n"
            bot_txt += emojis['point_right']+" "+token+"\n"+emojis['point_right']+" <a href='"+pair.url+"' >" + pair.base_token.symbol+"</a>- Current marketcap: $"+format_number_string(marketcap)

        return {"is_rug": False, "text": bot_txt, "is_new": is_new}

    except:

        text="There is no liquidity for this token"
        return {"is_rug": True, "reason": "liquidity", "text": text}

def add_warn(username, user_id, chat_id):
    print("add warn user")
    warn_user = db.query(Warn).filter(Warn.username == username).first()
    if warn_user != None:
        current_count = warn_user.count
        current_count = int(current_count)+1
        warn_user.count = current_count
        db.commit()
    else:
        warn_user = Warn(
            username=username,
            user_id=user_id,
            chat_id=chat_id,
            count=1
        )
        db.add(warn_user)
        db.commit()
    
    return warn_user

def remove_warn(username):
    warn_user = db.query(Warn).filter(Warn.username == username).first()
    text = ""
    if warn_user != None:
        db.delete(warn_user)
        db.commit()
        text = "Warning removed from @"+username+" ✅"
    else:
        text = "There is no warn for @"+username+" ✅"
    
    return text

def get_user_warn(username):
    warn_user = db.query(Warn).filter(Warn.username == username).first()
    has_warn = False
    if warn_user != None:
        has_warn = True
    
    return has_warn

async def get_user_shillmaster(user):
    return_txt = "❗ There is not any shill yet for @"+user
    username = user.replace("@", "")
    user_shills = db.query(Project).filter(Project.username == username).order_by(desc(Project.created_at)).limit(5).all()
    if len(user_shills)>0:
        return_txt = "📊 Shillmaster stats for @"+user+" 📊\n\n"
        for project in user_shills:
            if project.status == "active":
                return_txt += "💰 <a href='"+project.url+"' >"+project.token_symbol+"</a> Shared marketcap: $"+format_number_string(project.marketcap)+"\n"
                current_info = await current_status(project)
                
                if current_info['is_liquidity']:
                    if float(current_info['marketcap'])>float(project.ath_value):
                        project.ath_value = current_info['marketcap']
                        db.commit()
                    return_txt += emojis['point_right']+" Currently: $"+format_number_string(current_info['marketcap'])+" ("+str(round(current_info['percent'], 2))+"x)\n"
                    if float(current_info['marketcap'])< float(project.ath_value):
                        return_txt += "🏆 ATH: $"+format_number_string(project.ath_value)+" ("+return_percent(project.ath_value, project.marketcap)+"x)\n"
                    return_txt += "\n"
                else:
                    is_warn = current_info['is_warn']
                    if is_warn:
                        add_warn(username, project.user_id, project.chat_id)
                    return_txt += emojis['point_right']+"Currently: LIQUIDITY REMOVED\n\n"
            
            if project.status == "removed":
                return_txt += "💰 <a href='"+project.url+"' >"+project.token_symbol+"</a> Shared marketcap: $"+format_number_string(project.marketcap)+"\n"
                return_txt += "⚠️ Currently: LIQUIDITY REMOVED\n\n"
                return_txt += "🏆 ATH: $"+format_number_string(project.ath_value)+" ("+return_percent(project.ath_value, project.marketcap)+"x)\n\n"
            
            if project.status == "no_liquidity":
                return_txt += "💰 <a href='"+project.url+"' >"+project.token_symbol+"</a> has no Liquidity\n"
                return_txt += "⚠️ Got Warn with this token\n\n"
            
            if project.status == "honeypot":
                return_txt += "💰 <a href='"+project.url+"' >"+project.token_symbol+"</a> look like Honeypot\n"
                return_txt += "⚠️ Got Warn with this token\n\n"

    return return_txt

def clear_database():
    db.query(Pair).delete()
    db.query(Project).delete()
    db.query(Leaderboard).delete()