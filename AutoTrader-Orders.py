 #!/usr/bin/env python
import argparse
import urllib
import urllib2
import urlparse
import sys
import time  # this is only being used as part of the example
import os
import sys
import time
import dataset
import numpy
import math
import requests

import func
import dataset
import argparse
import exchange_api
import logging
import logging.handlers

from pprint import pprint
from poloniex import Poloniex
from decimal import Decimal

import socket
import threading
import SocketServer
import BaseHTTPServer

try:
    import configparser
except ImportError:
    # Python 2.7 compatibility
    import ConfigParser
    configparser = ConfigParser

parser = argparse.ArgumentParser(description='Script to auto-sell altcoins.')
parser.add_argument('-c', '--config', dest='config_path', default='~/.altcoin-autosell.config',
                help='path to the configuration file')
args = parser.parse_args()

config = configparser.RawConfigParser()
try:
    config_path = os.path.expanduser(args.config_path)
    func._Log('\nUsing config from "%s".', config_path)
    with open(config_path) as config_file:
         config.readfp(config_file)
except IOError as e:
    func._Log('Failed to read config: %s', e)
    sys.exit(1)

global StartTime, BalFile, TransFile, Polo, Balance, Get, markets, poll_delay, PriceDB, TradeDB, exchanges, exchange, target_currencies, CurrencyPairs, CurrencyPair, TimeSpan, line

#**EDIT MIN VALUES FOR REAL!!**#
Poloniex_Minimum_Trades_Buy = {"USDT_XRP": .0001, "USDT_LTC": .0001, "USDT_DASH": .0001, "USDT_BTC": 1, "BTC_LTC": .0001, "BTC_ETH": .0001}
Poloniex_Minimum_Trades_Sell = {"BTC_LTC":.0001, "BTC_XRP":.0001}

Error_Unauth = "Unauthorized Request"
Error_Invalid = "Invalid Method"
Error_Custom = ""

line = "                                                                              "    
StartTime = time
TimeSpan = 300
Order_Limit = 20

Polo = Poloniex("8Z96WF3Q-CUV390KL-59AZ31CQ-GZOIUULT", "bbb8edd76c9bb47585d26316e17015116a138cea7a7218d87f99388ecfd6c57d5c5125a98387ad53263dd3c9152d258fb4a479f2f97275fbbddc22f390d2323f")

poll_delay = (config.getint('General', 'poll_delay') if
             config.has_option('General', 'poll_delay') else TimeSpan)
             
request_delay = (config.getint('General', 'request_delay') if
                config.has_option('General', 'request_delay') else 1)

Exchanges = ["Polo"] ### Exchange API Classes from Modules
Exchanges = [Exchange for Exchange in Exchanges if Exchange is not None]

def place_buy(currencyPair, rate, amount):
    print "Placing a Buy Order for",amount, currencyPair, "at a price of", rate
    Order = eval(Exchange).buy(currencyPair, rate, amount)
    print Order
    return Order

def place_sell(currencyPair, rate, amount):
    print "Placing a Sell Order for",amount, currencyPair, "at a price of", rate
    Order = eval(Exchange).sell(currencyPair, rate, amount)
    print Order
    return Order

def cancel_order(CurrencyPair, Info, Order_TimeStamp):
    eval(Exchange).cancelOrder(Info['orderNumber'])
    print "Canceled on Exchange..."
    func.Remove_Order_from_DB("Orders_Open", CurrencyPair, Info)
    print "Removed from Open Orders DB..."
    func.Insert_Order_to_DB("Orders_Canceled", Info['type'], CurrencyPair, Info['rate'], Info['amount'], Order_TimeStamp, "Canceled", Info['orderNumber'])
    print "Added to Canceled Orders DB..."  

#def Complete_Order(orderNumber):
#    eval(Exchange).

if not Exchanges:
    func._Log('\nNo Exchange sections defined!')
    sys.exit(1) ### Log and Exit if no Exchanges defined above or in config

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        query = parsed.query
        arguments = urlparse.parse_qs(query)
        self._set_headers()
        if (parsed.path != "/Orders"):
            self.send_error(404, Error_Unauth)
            return
        if 'pass' in arguments:
            if(arguments['pass'] == ["gen0cide"]):
                if 'method' in arguments:
                    Response = Error_Invalid
                    if(arguments['method'] == ["returnBalances"]):
                        #print Exchange
                        Response = eval(Exchange).returnBalances()
                        #print "Server Side Response Type before Return:", type(Response)
                        self.wfile.write(Response)
                        return Response
                    
                    if(arguments['method'] == ["active"]):
                        print "Checking Most Active Pair..."
                        most_active_pair = func.check_most_active_coin(poll_delay)
                        most_active_coin = most_active_pair[0]
                        Response = most_active_coin
                        self.wfile.write(Response)
                        return Response

                    self.send_error(404, "Invalid Method!")
                    return

                else:
                    self.send_error(404, "Invalid Method!")
                    return
        else:
            self.send_error(403, Error_Unauth)
            return

    def do_POST(self):
        print "In POST:",self.path
        parsed = urlparse.urlparse(self.path)
        print "Parsed:", parsed
        query = parsed.query
        print "Query:", query
        arguments = urlparse.parse_qs(query)
        print "Arguments:", arguments
        Response = "NULL"
        self._set_headers()
        if (parsed.path != "/Orders"):
            print Error_Unauth
            self.send_error(403, Error_Unauth)
            return
        if 'pass' in arguments:
            if(arguments['pass'] == ['gen0cide']):
                if 'method' in arguments:
                    method = arguments['method']
                    if(method == ['order']):                     # Order Function:
                        if 'ordertype' in arguments:
                            ordertype = arguments['ordertype']
                            if 'currencypair' in arguments:
                                CurrencyPair = arguments['currencypair'][0]
                                print "\nCurrencyPair:", CurrencyPair                                  
                                if 'amount' in arguments:
                                    Amount = arguments['amount'][0]
                                    if 'price' in arguments:
                                        Price = arguments['price'][0]
                                        #Markets = func.Get_DB_Markets()
                                        #Base_Balance = func.Get_Balance(ExcBal, Base_Currency)
                                        #Alt_Balance = func.Get_Balance(ExcBal, Alt_Currency)
                                        #Base_Currency_USDT_Price = float(func.Convert_Base_to_USDT(CurrencyPair, Market))
                                        #Alt_Currency_USDT_Price = float(func.Convert_Alt_to_USDT(CurrencyPair, Market))

                                        if(ordertype == ['Buy'] or ordertype == ['buy']):
                                            if CurrencyPair in Poloniex_Minimum_Trades_Buy:
                                                Buying_Min_Amt = Poloniex_Minimum_Trades_Buy[CurrencyPair]
                                                if(float(Amount) >= float(Buying_Min_Amt)):
                                                    print "Buying CurrencyPair:", CurrencyPair
                                                    Response = place_buy(CurrencyPair, Price, Amount)
                                                    orderNumber = Response['orderNumber']
                                                    print "Order:", Order
                                                    func.Insert_Order_to_DB("Orders_Open", "Buy", CurrencyPair, Price, Amount, time.time(), "Open", orderNumber)
                                                    print "Order", Response, "Placed."
                                                    self.wfile.write(Response)
                                                    return Response
                                                else:
                                                    Response = "Insufficient Buying Amount:", arguments['amount']
                                                    self.wfile.write(Response)
                                                    return Response

                                        if(ordertype == ['Sell'] or ordertype == ['sell']):
                                            if CurrencyPair in Poloniex_Minimum_Trades_Sell:                                        
                                                Selling_Min_Amt = Poloniex_Minimum_Trades_Sell[CurrencyPair]
                                                print "Amount:", Amount
                                                if(float(arguments['amount'][0]) >= float(Selling_Min_Amt)): 
                                                    print "Selling CurrencyPair:", CurrencyPair
                                                    Response = place_sell(CurrencyPair, Price, Amount)
                                                    orderNumber = Response['orderNumber']
                                                    func.Insert_Order_to_DB("Orders_Open", "Sell", CurrencyPair, Price, Amount, time.time(), "Open", orderNumber)
                                                    self.wfile.write(Response)
                                                    return Response
                                                else:
                                                    Response = "Insufficient Selling Amount:", arguments['amount']
                                                    self.wfile.write(Response)
                                                    return Response

                                            return Response
                                    else:
                                        Error_Custom = "1 No Price in Request!"
                                        print Error_Custom
                                        self.send_error(404, Error_Custom)
                                        return
                                else:
                                    Error_Custom = "2 No Amount in Request!"
                                    print Error_Custom
                                    self.send_error(404, Error_Custom)
                                    return
                            else:
                                Error_Custom = "3 No CurrencyPair in Request!"
                                print Error_Custom
                                self.send_error(404, Error_Custom)
                                return
                        else:
                            Error_Custom = "4 No Order Type in Request!"
                            print Error_Custom
                            self.send_error(404, Error_Custom)
                            return
                    #else:
                    #    Error_Custom = "5 Invalid Order Type in Request!"
                    #    print Error_Custom
                    #    self.send_error(403, Error_Custom)
                    #    return
                    ###
                    # Password Protected POST Test Function
                    print method
                    if(method == ['test']):                     
                        Response = "Test!"
                        self.wfile.write(Response)
                        return Response
                        
                    ### Other POST Functions Go Here...

                    else:
                        Error_Custom = "6 Invalid Method in Request!"
                        print Error_Custom
                        self.send_error(403, Error_Custom)
                        return
                else:
                    Error_Custom = "7 No Method in Request!"
                    print Error_Custom
                    self.send_error(403, Error_Custom)
                    return
            else:
                Error_Custom = "8 Invalid Password!"
                print Error_Custom
                self.send_error(403, Error_Custom)
                return
        else:
            Error_Custom = "9 Invalid Password!"
            print Error_Custom
            self.send_error(403, Error_Custom)
            return

addr = ('', 8081)
sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(addr)
sock.listen(5)

class Thread(threading.Thread):
    def __init__(self, i):
        threading.Thread.__init__(self)
        self.i = i
        self.daemon = True
        self.start()

    def run(self):
        #print "Thread:", i
        httpd = BaseHTTPServer.HTTPServer(addr, Handler, False)
        # Prevent the HTTP server from re-binding every handler.
        # https://stackoverflow.com/questions/46210672/
        httpd.socket = sock
        httpd.server_bind = self.server_close = lambda self: None
        httpd.serve_forever()

[Thread(i) for i in range(10)]
while True:
    #Process Open/Completed Orders, Cancel Old Ones, Insert all to Respective DB (Orders_Open, Orders_Completed, Orders_Canceled)
    print "\nChecking All Open Orders..."
    Orders = eval(Exchange).returnOpenOrders(currencyPair='all')
    for Order in Orders:
        if (len(Orders[Order]) != 0):
            Info = Orders[Order][0]
            print Order,":",Info
            CurrencyPair = Order

#{u'orderNumber': u'120028128840', u'margin': 0, u'amount': u'1.51578227', u'rate': u'0.00016213', u'date': u'2018-02-03 13:59:53', u'total': u'0.00024575', u'type': u'sell', u'startingAmount': u'1.51578227'}

            Order_TimeStamp = func.Convert_ExTime(Info['date'])
            Order_TimeLimit = func.Calculate_Time_Limit(Order_TimeStamp, Order_Limit)
            
            
            if(int(time.time()) >= Order_TimeLimit):
                print "Cancelling Order after "+str(Order_Limit)+" seconds:", Order_TimeLimit
                print "Order Originally Issued:          ", Order_TimeStamp
                print "Current GMT Time:                 ", int(time.time())         
                print Info['orderNumber']   

                try:
                    Order_Trade_Hist = eval(Exchange).returnOrderTrades(Info['orderNumber'])
                    print "Trade History of Order:", Order_Trade_Hist        
                except Exception, e:
                    print e.__class__, ":", e
                                   
#               def Insert_Order_to_DB(Database, OrderType, CurrencyPair, Price, Amount, DateTimeof, Status):
#               {u'orderNumber': u'119926376694', u'margin': 0, u'amount': u'1.52478083', u'rate': u'0.00014403', u'date': u'2018-02-03 08:30:11', u'total': u'0.00021961', u'type': u'sell', u'startingAmount': u'1.52478083'}
                cancel_order(CurrencyPair, Info, Order_TimeStamp)


#   Can Do Other Stuff Here Regarding Orders and Processing Order History for new DB's?
        

    time.sleep(15)
        
