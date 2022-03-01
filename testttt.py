#Use at your own risk , I am not responsible for any or your profit or Loss in stock market
#telegram_id = https://t.me/Atwoz029lengthis8
#shoonya_api telegram group= https://t.me/shoonyaapi

import datetime
from datetime import date
import pandas as pd 
from datetime import timedelta
from datetime import datetime as dt
import time
import requests
import sys
from datesexp import *
from NorenApi import NorenApi
shoonya=NorenApi()
shoonya.set_token()

expiry=f"{present()[:-4]}22"

def strikes():
	
	global strike_ce_fin,strike_pe_fin
	closee=float(shoonya.get_quotes('NSE',f"{fut}")['lp'])
	ce= f"{round(closee/100)*100}CE" 
	pe= f"{round(closee/100)*100}PE" 
	strike_ce_fin=f"BANKNIFTY{expiry}C{ce[:-2]}"
	strike_pe_fin=f"BANKNIFTY{expiry}P{pe[:-2]}"
	return strike_ce_fin,strike_pe_fin

#In below , I=Intraday , u can change to M for delivery 
#buy_option is of stoploss limit order and sell orders are of marker orders

def buy_option(symbol,quantity,price,triggerprice):
	return shoonya.place_order(buy_or_sell='B',product_type='I',exchange="NFO", tradingsymbol=symbol, quantity=quantity, discloseqty=0,price_type='SL-LMT', price=price, trigger_price=triggerprice,retention='DAY', amo='NO', remarks=None, bookloss_price = 0.0, bookprofit_price = 0.0, trail_price = 0.0)
def sell_option(symbol,quantity):
	return shoonya.place_order(buy_or_sell='S',product_type='I',
        exchange="NFO", tradingsymbol=symbol, quantity=quantity, discloseqty=0,
        price_type='MKT', price=0.0, trigger_price=None,
        retention='DAY', amo='NO', remarks=None, bookloss_price = 0.0, bookprofit_price = 0.0, trail_price = 0.0)

def ltp(symbol):
	return shoonya.get_quotes('NFO',f"{symbol}")['lp']

fut='Nifty Bank' 
name=f'NSE:{fut}'

#make it to true if you want to put live orders in account
#otherwise you can keep it to False , it will just print the update 

live_trading=True
lot=1
s=False
data={}
while True:
	try:
		if str(dt.now().strftime('%X'))>str(datetime.time(10,58,58)):	
			try:
				data[name]
			except:
				print("Let's start")
				data[name]={'date':dt.now().strftime("%d-%m-%Y"),
				'Entryprice_ce':None,
				'Entryprice_pe':None,
				'ce_sl':None,
				'pe_sl':None,
				'quantity':lot*25,
				}
			strikes()
			ce_ltp=float(ltp(strike_ce_fin))
			pe_ltp=float(ltp(strike_pe_fin)) 
			if live_trading:
				sell_option(strike_ce_fin,data[name]['quantity'])
				sell_option(strike_pe_fin,data[name]['quantity'])
			data[name]['Entry']=True
			data[name]['Entryprice_ce']=ce_ltp
			data[name]['Entryprice_pe']=pe_ltp

		 	#change the stoploss for ce leg accordingly 
		 	#change the stoplosss for pe leg accordingly
		 	#here i have used 30% as sl
			
			data[name]['ce_sl']=round(round(data[name]['Entryprice_ce']*1.30/0.05)*0.05,2)
			data[name]['pe_sl']=round(round(data[name]['Entryprice_pe']*1.30/0.05)*0.05,2) 
			update=f"Straddle placed in {strike_ce_fin}-{data[name]['Entryprice_ce']} {strike_pe_fin }-{data[name]['Entryprice_pe']} at {dt.now().strftime('%X')}"
			print(update)
			s=True
		if s:
			if live_trading:

				#keeping a 1% buffer as trigger price ,can change as you wish
				
				buy_option(strike_ce_fin,data[name]['quantity'],round(round(data[name]['ce_sl']*1.01/0.05)*0.05,2),data[name]['ce_sl']) 
				buy_option(strike_pe_fin,data[name]['quantity'],round(round(data[name]['pe_sl']*1.01/0.05)*0.05,2),data[name]['pe_sl'])
			print("placed stoploss orders")
			sys.exit()
	except Exception as e:
		print("error",e)
		time.sleep(5)





