import requests
import pandas as pd
from datetime import datetime as dt
headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    }

indices=['BANKNIFTY','NIFTY']


def fetch(payload):
        try:
            output = requests.get(payload,headers=headers).json()
        except ValueError:
            s =requests.Session()
            output = s.get("http://nseindia.com",headers=headers)
            output = s.get(payload,headers=headers).json()
        return output

def scrap(symbol):
    payload = fetch('https://www.nseindia.com/api/option-chain-indices?symbol='+symbol)
    return payload

def listt(symbol):
    payload = scrap(symbol)
    payload = pd.DataFrame({'Date':payload['records']['expiryDates']})
    return payload

def present():
    present_exp=str(listt("BANKNIFTY")['Date'][0])
    present_exp=present_exp.replace("-","").upper()
    return present_exp

print(f"The current expiry is {present()}")
