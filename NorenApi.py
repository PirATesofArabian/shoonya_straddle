import json
import requests
import threading
import websocket
import logging
import enum
import datetime
import hashlib
import time
from time import sleep
from datetime import datetime as dt
logger = logging.getLogger(__name__)
import config
import json
profiledetails=""
class ProductType:
    Delivery = 'C'
    Intraday = 'I'
    Normal   = 'M'
    CF       = 'M'

class FeedType:
    TOUCHLINE = 1    
    SNAPQUOTE = 2
    
class PriceType:
    Market = 'MKT'
    Limit = 'LMT'
    StopLossLimit = 'SL-LMT'
    StopLossMarket = 'SL-MKT'

class BuyorSell:
    Buy = 'B'
    Sell = 'S'
    
def reportmsg(msg):
    #print(msg)
    logger.debug(msg)

def reporterror(msg):
    #print(msg)
    logger.error(msg)

def reportinfo(msg):
    #print(msg)
    logger.info(msg)

class NorenApi:
    __service_config = {
      'host': 'http://wsapihost/',
      'routes': {
          'authorize': '/QuickAuth',
          'logout': '/Logout',
          'forgot_password': '/ForgotPassword',
          'watchlist_names': '/MWList',
          'watchlist': '/MarketWatch',
          'watchlist_add': '/AddMultiScripsToMW',
          'watchlist_delete': '/DeleteMultiMWScrips',
          'placeorder': '/PlaceOrder',
          'modifyorder': '/ModifyOrder',
          'cancelorder': '/CancelOrder',
          'exitorder': '/ExitSNOOrder',
          'orderbook': '/OrderBook',
          'tradebook': '/TradeBook',          
          'singleorderhistory': '/SingleOrdHist',
          'searchscrip': '/SearchScrip',
          'TPSeries' : '/TPSeries',     
          'optionchain' : '/GetOptionChain',     
          'holdings' : '/Holdings',
          'limits' : '/Limits',
          'positions': '/PositionBook',
          'scripinfo': '/GetSecurityInfo',
          'getquotes': '/GetQuotes',
      },
      'websocket_endpoint': 'wss://wsendpoint/',
      'eoddata_endpoint' : 'http://eodhost/'
    }

    def __init__(self):
        self.__service_config['host'] = 'https://shoonyatrade.finvasia.com/NorenWClientTP/' #host
        self.__service_config['websocket_endpoint'] = 'wss://shoonyatrade.finvasia.com/NorenWSTP/' #websocket
        self.__service_config['eoddata_endpoint'] = 'https://shoonya.finvasia.com/chartApi/getdata/' #eodhost

        self.__websocket = None
        self.__websocket_connected = False
        self.__ws_mutex = threading.Lock()
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__subscribe_callback = None
        self.__order_update_callback = None
        self.__market_status_messages_callback = None
        self.__exchange_messages_callback = None
        self.__oi_callback = None
        self.__dpr_callback = None
        self.__subscribers = {}
        self.__market_status_messages = []
        self.__exchange_messages = []

    def __ws_run_forever(self):
        
        while True:
            try:
                self.__websocket.run_forever( ping_interval=3,  ping_payload='{"t":"h"}')
            except Exception as e:
                logger.warning(f"websocket run forever ended in exception, {e}")
            
            sleep(0.1) # Sleep for 100ms between reconnection.

    def __ws_send(self, *args, **kwargs):
        while self.__websocket_connected == False:
            sleep(0.05)  # sleep for 50ms if websocket is not connected, wait for reconnection
        with self.__ws_mutex:
            ret = self.__websocket.send(*args, **kwargs)
        return ret

    def __on_close_callback(self, wsapp, close_status_code, close_msg):
        reportmsg(close_status_code)
        reportmsg(wsapp)

        self.__websocket_connected = False
        if self.__on_disconnect:
            self.__on_disconnect()

    def __on_open_callback(self, ws=None):
        self.__websocket_connected = True

        #prepare the data
        values              = { "t": "c" }
        values["uid"]       = self.__username
        values["pwd"]       = self.__password
        values["actid"]     = self.__username
        values["susertoken"]    = self.__susertoken
        values["source"]    = 'API'                

        payload = json.dumps(values)

        reportmsg(payload)
        self.__ws_send(payload)

        #self.__resubscribe()
        

    def __on_error_callback(self, ws=None, error=None):
        if(type(ws) is not websocket.WebSocketApp): # This workaround is to solve the websocket_client's compatiblity issue of older versions. ie.0.40.0 which is used in upstox. Now this will work in both 0.40.0 & newer version of websocket_client
            error = ws
        if self.__on_error:
            self.__on_error(error)

    def __on_data_callback(self, ws=None, message=None, data_type=None, continue_flag=None):
        #print(ws)
        #print(message)
        #print(data_type)
        #print(continue_flag)

        res = json.loads(message)

        if(self.__subscribe_callback is not None):
            if res['t'] == 'tk' or res['t'] == 'tf':
                self.__subscribe_callback(res)
                return
            if res['t'] == 'dk' or res['t'] == 'df':
                self.__subscribe_callback(res)
                return

        if(self.__on_error is not None):
            if res['t'] == 'ck' and res['s'] != 'OK':
                self.__on_error(res)
                return

        if(self.__order_update_callback is not None):
            if res['t'] == 'om':
                self.__order_update_callback(res)
                return

        if self.__on_open:
            if res['t'] == 'ck' and res['s'] == 'OK':
                self.__on_open()
                return


    def start_websocket(self, subscribe_callback = None, 
                        order_update_callback = None,
                        socket_open_callback = None,
                        socket_close_callback = None,
                        socket_error_callback = None,
                        run_in_background=True,
                        market_status_messages_callback = None,
                        exchange_messages_callback = None,
                        oi_callback = None,
                        dpr_callback = None):        
        """ Start a websocket connection for getting live data """
        self.__on_open = socket_open_callback
        self.__on_disconnect = socket_close_callback
        self.__on_error = socket_error_callback
        self.__subscribe_callback = subscribe_callback
        self.__order_update_callback = order_update_callback
        self.__market_status_messages_callback = market_status_messages_callback
        self.__exchange_messages_callback = exchange_messages_callback
        self.__oi_callback = oi_callback
        self.__dpr_callback = dpr_callback
        url = self.__service_config['websocket_endpoint'].format(access_token=self.__susertoken)
        reportmsg('connecting to {}'.format(url))

        self.__websocket = websocket.WebSocketApp(url,
                                                on_data=self.__on_data_callback,
                                                on_error=self.__on_error_callback,
                                                on_close=self.__on_close_callback,
                                                on_open=self.__on_open_callback)
        #th = threading.Thread(target=self.__send_heartbeat)
        #th.daemon = True
        #th.start()
        #if run_in_background is True:
        self.__ws_thread = threading.Thread(target=self.__ws_run_forever)
        self.__ws_thread.daemon = True
        self.__ws_thread.start()
        
    
    def login(self, userid, password, twoFA, vendor_code, api_secret, imei):
        global profiledetails
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['authorize']}" 
        reportmsg(url)

        #Convert to SHA 256 for password and app key
        pwd = hashlib.sha256(password.encode('utf-8')).hexdigest()
        u_app_key = '{0}|{1}'.format(userid, api_secret)
        app_key=hashlib.sha256(u_app_key.encode('utf-8')).hexdigest()
        #prepare the data
        values              = { "source": "API" , "apkversion": "1.0.0"}
        values["uid"]       = userid
        values["pwd"]       = pwd
        values["factor2"]   = twoFA
        values["vc"]        = vendor_code
        values["appkey"]    = app_key        
        values["imei"]      = imei        

        payload = 'jData=' + json.dumps(values)
        reportmsg("Req:" + payload)

        res = requests.post(url, data=payload)
        reportmsg("Reply:" + res.text)

        resDict = json.loads(res.text)
        profiledetails=resDict
        print(resDict)
        if resDict['stat'] != 'Ok':            
            return None
        
        self.__username   = userid
        self.__accountid  = userid
        self.__password   = password
        self.__susertoken = resDict['susertoken']
        f=open('shoonyakey.txt','w')
        f.write(str(resDict['susertoken']))
        f.close()
        return resDict
    def set_token(self):
        enctoken = open('shoonyakey.txt', 'r').read().rstrip()
        self.__susertoken = enctoken
        self.__username   = config.username
        self.__accountid  = config.username
        self.__password   = config.pwd        
    def forgot_password(self, userid, pan, dob):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['forgot_password']}" 
        reportmsg(url)

        #prepare the data
        values              = { "source": "API" }
        values["uid"]       = userid
        values["pan"]       = pan
        values["dob"]       = dob

        payload = 'jData=' + json.dumps(values)
        reportmsg("Req:" + payload)

        res = requests.post(url, data=payload)
        reportmsg("Reply:" + res.text)

        resDict = json.loads(res.text)
        
        if resDict['stat'] != 'Ok':            
            return None
        
        return resDict

    def logout(self):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['logout']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        self.__username   = None
        self.__accountid  = None
        self.__password   = None
        self.__susertoken = None

        return resDict

    def subscribe(self, instrument, feed_type=FeedType.TOUCHLINE):
        values = {}

        if(feed_type == FeedType.TOUCHLINE):
            values['t'] =  't'
        elif(feed_type == FeedType.SNAPQUOTE):
            values['t'] =  'd'
        else:
            values['t'] =  str(feed_type)

        if type(instrument) == list:
            values['k'] = '#'.join(instrument)
        else :
            values['k'] = instrument

        data = json.dumps(values)

        #print(data)
        self.__ws_send(data)

    def unsubscribe(self, instrument, feed_type=FeedType.TOUCHLINE):
        values = {}

        if(feed_type == FeedType.TOUCHLINE):
            values['t'] =  'ut'
        elif(feed_type == FeedType.SNAPQUOTE):
            values['t'] =  'ud'
        
        if type(instrument) == list:
            values['k'] = '#'.join(instrument)
        else :
            values['k'] = instrument

        data = json.dumps(values)

        #print(data)
        self.__ws_send(data)


    def subscribe_orders(self):
        values = {'t': 'o'}
        values['actid'] = self.__accountid        

        data = json.dumps(values)

        reportmsg(data)
        self.__ws_send(data)

    def get_watch_list_names(self):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['watchlist_names']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def get_watch_list(self, wlname):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['watchlist']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["wlname"]    = wlname
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict


    def add_watch_list_scrip(self, wlname, instrument):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['watchlist_add']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["wlname"]    = wlname

        if type(instrument) == list:
            values['scrips'] = '#'.join(instrument)
        else :
            values['scrips'] = instrument
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def delete_watch_list_scrip(self, wlname, instrument):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['watchlist_delete']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["wlname"]    = wlname

        if type(instrument) == list:
            values['scrips'] = '#'.join(instrument)
        else :
            values['scrips'] = instrument
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict


    def place_order(self, buy_or_sell, product_type,
                    exchange, tradingsymbol, quantity, discloseqty,
                    price_type, price=0.0, trigger_price=None,
                    retention='DAY', amo='NO', remarks=None, bookloss_price = 0.0, bookprofit_price = 0.0, trail_price = 0.0):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['placeorder']}" 
        reportmsg(url)
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["actid"]     = self.__accountid
        values["trantype"]  = buy_or_sell
        values["prd"]       = product_type
        values["exch"]      = exchange
        values["tsym"]      = tradingsymbol
        values["qty"]       = str(quantity)
        values["dscqty"]    = str(discloseqty)        
        values["prctyp"]    = price_type
        values["prc"]       = str(price)
        values["trgprc"]    = str(trigger_price)
        values["ret"]       = retention
        values["remarks"]   = remarks
        values["amo"]       = amo
        
        #if cover order or high leverage order
        if product_type == 'H':            
            values["blprc"]       = str(bookloss_price)
            #trailing price
            if trail_price != 0.0:
                values["trailprc"] = str(trail_price)

        #bracket order
        if product_type == 'B':            
            values["blprc"]       = str(bookloss_price)
            values["bpprc"]       = str(bookprofit_price)
            #trailing price
            if trail_price != 0.0:
                values["trailprc"] = str(trail_price)

        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def modify_order(self, orderno, exchange, tradingsymbol, newquantity,
                    newprice_type, newprice=0.0, newtrigger_price=None, bookloss_price = 0.0, bookprofit_price = 0.0, trail_price = 0.0):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['modifyorder']}" 
        print(url)

        #prepare the data
        values                  = {'ordersource':'API'}
        values["uid"]           = self.__username
        values["actid"]         = self.__accountid
        values["norenordno"]    = orderno
        values["exch"]          = exchange
        values["tsym"]          = tradingsymbol
        values["qty"]           = str(newquantity)
        values["prctyp"]        = newprice_type        
        values["prc"]           = str(newprice)

        if (newprice_type == 'SL-LMT') or (newprice_type == 'SL-MKT'):
            if (newtrigger_price != None):
                values["trgprc"] = str(newtrigger_price)
            else:
                reporterror('trigger price is missing')
                return None

        #if cover order or high leverage order
        if bookloss_price != 0.0:            
            values["blprc"]       = str(bookloss_price)
        #trailing price
        if trail_price != 0.0:
            values["trailprc"] = str(trail_price)         
        #book profit of bracket order   
        if bookprofit_price != 0.0:
            values["bpprc"]       = str(bookprofit_price)
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def cancel_order(self, orderno):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['cancelorder']}" 
        print(url)

        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["norenordno"]    = orderno
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        print(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def exit_order(self, orderno, product_type):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['exitorder']}" 
        print(url)

        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["norenordno"]    = orderno
        values["prd"]           = product_type
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None

        return resDict

    def single_order_history(self, orderno):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['singleorderhistory']}" 
        print(url)
        
        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["norenordno"]    = orderno
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        #error is a json with stat and msg wchih we printed earlier.
        if type(resDict) != list:                            
                return None

        return resDict


    def get_order_book(self):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['orderbook']}" 
        reportmsg(url)

        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        
        #error is a json with stat and msg wchih we printed earlier.
        if type(resDict) != list:                            
                return None

        return resDict

    def get_trade_book(self):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['tradebook']}" 
        reportmsg(url)

        #prepare the data
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["actid"]     = self.__accountid
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        
        #error is a json with stat and msg wchih we printed earlier.
        if type(resDict) != list:                            
                return None

        return resDict

    def searchscrip(self, exchange, searchtext):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['searchscrip']}" 
        reportmsg(url)
        
        if searchtext == None:
            reporterror('search text cannot be null')
            return None
        
        values              = {}
        values["uid"]       = self.__username
        values["exch"]      = exchange
        values["stext"]     = searchtext       
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if resDict['stat'] != 'Ok':            
            return None        

        return resDict

    def get_option_chain(self, exchange, tradingsymbol, strikeprice, count=2):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['optionchain']}" 
        reportmsg(url)
        
        
        values              = {}
        values["uid"]       = self.__username
        values["exch"]      = exchange
        values["tsym"]      = tradingsymbol       
        values["strprc"]    = str(strikeprice)
        values["cnt"]       = str(count)       
        
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if resDict['stat'] != 'Ok':            
            return None        

        return resDict

    def get_security_info(self, exchange, token):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['scripinfo']}" 
        reportmsg(url)        
        
        values              = {}
        values["uid"]       = self.__username
        values["exch"]      = exchange
        values["token"]     = token       
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if resDict['stat'] != 'Ok':            
            return None        

        return resDict

    def get_quotes(self, exchange, token):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['getquotes']}" 
        reportmsg(url)        
        
        values              = {}
        values["uid"]       = self.__username
        values["exch"]      = exchange
        values["token"]     = token       
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if resDict['stat'] != 'Ok':            
            return None        

        return resDict

    def get_time_price_series(self, exchange, token, starttime=None, endtime=None):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['TPSeries']}" 
        reportmsg(url)

        #prepare the data
        if starttime == None:
            timestring = time.strftime('%d-%m-%Y') + ' 00:00:00'
            timeobj = time.strptime(timestring,'%d-%m-%Y %H:%M:%S')
            starttime = time.mktime(timeobj)

        #
        values              = {'ordersource':'API'}
        values["uid"]       = self.__username
        values["exch"]      = exchange
        values["token"]     = token
        values["st"] = str(starttime)
        if endtime != None:
            values["et"]   = str(endtime)
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)
        
        #error is a json with stat and msg wchih we printed earlier.
        if type(resDict) != list:                            
                return None

        return resDict

    def get_daily_price_series(self, exchange, tradingsymbol, startdate=None, enddate=None):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['eoddata_endpoint']}" 
        reportmsg(url)

        #prepare the data
        if startdate == None:  
            week_ago = datetime.date.today() - datetime.timedelta(days=7)
            startdate = dt.combine(week_ago, dt.min.time()).timestamp()

        if enddate == None:            
            enddate = dt.now().timestamp()

        #
        values              = {}
        values["uid"]       = self.__username
        values["sym"]      = '{0}:{1}'.format(exchange, tradingsymbol)
        values["from"]     = str(startdate)
        values["to"]       = str(enddate)
        
        #payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        payload = json.dumps(values)
        reportmsg(payload)

        headers = {"Content-Type": "application/json; charset=utf-8"}
        res = requests.post(url, data=payload, headers=headers)
        reportmsg(res)

        if res.status_code != 200:
            return None

        if len(res.text) == 0:
            return None

        resDict = json.loads(res.text)
        
        #error is a json with stat and msg wchih we printed earlier.
        if type(resDict) != list:                            
            return None

        return resDict
        
    def get_holdings(self, product_type = None):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['holdings']}" 
        reportmsg(url)
        
        if product_type == None:
            product_type = ProductType.Delivery
        
        values              = {}
        values["uid"]       = self.__username
        values["actid"]     = self.__accountid
        values["prd"]       = product_type       
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if type(resDict) != list:                            
                return None

        return resDict

    def get_limits(self, product_type = None, segment = None, exchange = None):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['limits']}" 
        reportmsg(url)        
        
        values              = {}
        values["uid"]       = self.__username
        values["actid"]     = self.__accountid
        
        if product_type != None:
            values["prd"]       = product_type       
        
        if product_type != None:
            values["seg"]       = segment       
        
        if product_type != None:
            values["exch"]       = exchange       
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)        

        return resDict

    def get_positions(self):
        config = NorenApi.__service_config

        #prepare the uri
        url = f"{config['host']}{config['routes']['positions']}" 
        reportmsg(url)        
        
        values              = {}
        values["uid"]       = self.__username
        values["actid"]     = self.__accountid
        
        payload = 'jData=' + json.dumps(values) + f'&jKey={self.__susertoken}'
        
        reportmsg(payload)

        res = requests.post(url, data=payload)
        reportmsg(res.text)

        resDict = json.loads(res.text)

        if type(resDict) != list:                            
            return None

        return resDict

