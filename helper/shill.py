from pydantic import BaseModel

class Shill(BaseModel):
    username: str = None
    token: str
    url: str
    symbol: str
    marketcap: str
    ath: str
    current_marketcap: str
    percent: str
    created_at: str