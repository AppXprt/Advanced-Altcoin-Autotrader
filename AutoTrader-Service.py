 #!/usr/bin/env python

import argparse
import urllib
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
import json

#import pandas

import func
import dataset
import argparse
import exchange_api
import logging
import logging.handlers

from pprint import pprint
from poloniex import Poloniex
#from fbprophet import Prophet
from decimal import Decimal
#from movingaverages import BotIndicators 
import socket
import threading
import SocketServer
import BaseHTTPServer


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'
   INCREASE = '\u25B2'
   DECREASE = '\u25BC' 

try:
    import configparser
except ImportError:
    # Python 2.7 compatibility
    import ConfigParser
    configparser = ConfigParser

parser = argparse.ArgumentParser(description='Script to auto-sell altcoins.')
parser.add_argument('-c', '--config', dest='config_path', default='.altcoin-autosell.config',
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

global StartTime, BalFile, TransFile, Polo, Balance, Get, markets, poll_delay, PriceDB, TradeDB, exchanges, exchange, target_currencies, CurrencyPairs, CurrencyPair, TimeSpan, line, most_active_coin

LatestRateUp = []; LatestRateDown = []; LatestRateUpAvg = []; LatestRateDownAvg = []; 
LatestRateUpDBAvg = []; LatestRateDownDBAvg = []; LatestRateUpDB_Last_Price = []; LatestRateDownDB_Last_Price = [];
LatestRateEq = []; LatestRateEqAvg = []; LatestRateEqDBAvg = []; LatestRateEqDB_Last_Price = []; LatestRateEqDB_Last_Price = []; Best_Profits_Buying = {}; Best_Profits_Selling = {};

#**EDIT MIN VALUES FOR REAL!!**#
Poloniex_Minimum_Trades_Buy = {"USDT_XRP": .0001, "USDT_LTC": .0001, "USDT_DASH": .0001, "USDT_BTC": .0001, "BTC_LTC": .0001, "BTC_ETH": .0001}
Poloniex_Minimum_Trades_Sell = {"BTC_LTC":.0001}

best_base_sell = ''
best_alt_sell = ''
best_base_buy = ''
best_alt_buy = ''

best_profits_buying_pair = ''
best_profits_selling_pair = ''
#ExcBal = ""
best_sell_usdt = 0
best_buy_usdt = 0
buy_amount_usdt = 0
sell_amount_usdt = 0
best_buy_rate = 0
best_sell_rate = 0
sell_amount = 0
buy_amount = 0
selling_amount = 0
buying_amount = 0
diff_perc_sell = 0
diff_perc_buy = 0
bal_perc_buy = 0
bal_perc_sell = 0
buying_diff = 0
selling_diff = 0
sell_invest_percent = 0
buy_invest_percent = 0
buying_fee = 1.0025
selling_fee = 1.0015

line = "                                                                              "    
StartTime = time

BalFile = "Balances.txt"
TransFile = "Transactions.txt"
TimeSpan = 30
Polo = Poloniex("8Z96WF3Q-CUV390KL-59AZ31CQ-GZOIUULT", "bbb8edd76c9bb47585d26316e17015116a138cea7a7218d87f99388ecfd6c57d5c5125a98387ad53263dd3c9152d258fb4a479f2f97275fbbddc22f390d2323f")

poll_delay = (config.getint('General', 'poll_delay') if
             config.has_option('General', 'poll_delay') else TimeSpan)
             
request_delay = (config.getint('General', 'request_delay') if
                config.has_option('General', 'request_delay') else 1)

Exchanges = ["Polo"] ### Exchange API Classes from Modules
Exchanges = [Exchange for Exchange in Exchanges if Exchange is not None]

if not Exchanges:
    func._Log('\nNo Exchange sections defined!')
    sys.exit(1) ### Log and Exit if no Exchanges defined above or in config

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        #Response = {}
        parsed = urlparse.urlparse(self.path)
        query = parsed.query
        arguments = urlparse.parse_qs(query)

        if (parsed.path != "/AutoTrader"):
            self.send_error(404, "Improper GET Path Issued!")
            return
       
        if(arguments['pass'] == [""]):
            self._set_headers()

            if(arguments['method'] == ["returnBalances"]):
                #print Exchange
                Response = eval(Exchange).returnBalances()

                #print "Server Side Response Type before Return:", type(Response)
                self.wfile.write(Response)
                return Response
                
            if(arguments['method'] == ["active"]):
                most_active_pair = func.check_most_active_coin(poll_delay)
                most_active_coin = most_active_pair[0]
                Response = most_active_coin
                self.wfile.write(Response)
                return Response
            
            #if(arguments['method'] == [""]):
            #self.wfile.write(Response)
            return Response
        else:
            self.send_error(404, "Invalid Pass/Key!")
            return
        

    def do_POST(self):
        parsed = urlparse.urlparse(self.path)
        query = parsed.query
        arguments = urlparse.parse_qs(query)
        self._set_headers()
        if (parsed.path != "/AutoTrader"):
            print "Unauthorized Request!"
            self.send_error(403, "Unauthorized")
            return
        print "Arguments:", arguments
        print "Arguments Type:", type(arguments)    
        if 'pass' in arguments:
            print arguments['pass']
            if(arguments['pass'] == ['gen0cide']):
                print "Request Authorized!"
                if 'method' in arguments:
                    print "Method:", arguments['method']
                    if(arguments['method'] == ['Buy'] or arguments['method'] == ['buy']):
                        print "Buy Issued!"

                    if(arguments['method'] == ['Sell'] or arguments['method'] == ['sell']):
                        print "Sell Issued!"
          
                Response = parsed.query # Confirm / return order with order ID # or something?
                #print "Response before Return:", Response
                self.wfile.write(Response)  #Actual Return the Console uses
                return Response
            else:
                print "Unauthorized Request!"
                self.send_error(403, "Unauthorized!")
                return
        else:
            print "Unauthorized Request!"
            self.send_error(403, "Unauthorized!")
            return

# Create ONE socket.
addr = ('', 8080)
sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(addr)
sock.listen(5)

# Launch HTTP listener thread.
class Thread(threading.Thread):
    def __init__(self, i):
        threading.Thread.__init__(self)
        self.i = i
        self.daemon = True
        self.start()
    def run(self):
        httpd = BaseHTTPServer.HTTPServer(addr, Handler, False)

        # Prevent the HTTP server from re-binding every handler.
        # https://stackoverflow.com/questions/46210672/
        httpd.socket = sock
        httpd.server_bind = self.server_close = lambda self: None

        httpd.serve_forever()

[Thread(i) for i in range(1)]
# Loop forever, doing something useful hopefully:
while True:
    
    for Exchange in Exchanges:
        #Best_Profits_Selling = {}
        #Best_Profits_Buying = {}
        bal_perc_buy = 0
        bal_perc_sell = 0
        buying_fee = .25
        selling_fee = .15
        diff_perc_buy = 0
        diff_perc_sell = 0
        buy_amount_usdt = 0
        sell_amount_usdt = 0

        print color.BOLD+color.BLUE+"Processing Started for Exchange:", Exchange,"..."+color.END
                       
        try:
            ExcBal = eval(Exchange).returnBalances()
            tarprint = ""; sorprint = ""   
            
            Markets = func.Get_DB_Markets() 
            print color.BOLD+color.BLUE+"Exchange Identified! Analyzing", len(Markets), "Total Markets In The AutoTrader Database.",color.END
  
            m = 0

            for Market in Markets:
                m = m + 1
                print color.BOLD+color.BLUE+"Moving Into Target Market [", m ,"of", len(Markets), "]:", Market
                
                CurrencyPairs = []
                Base_Currency = Market               
                Alt_Currencies = func.Get_DB_Market_Currency_Alt(Market)
                
                for Alt_Currency in Alt_Currencies:
                  
                    CurrencyPairs.append(Base_Currency+"_"+Alt_Currency)
                
                Base_Balance = func.Get_Balance(ExcBal, Base_Currency)
                
                for CurrencyPair in CurrencyPairs:
                    B1 = Market; B2 = "_"
                    loc1 = CurrencyPair.find(B1); loc2 = CurrencyPair.find(B2)

                    Alt_Currency = CurrencyPair[loc2+1:]
                    Alt_Balance = func.Get_Balance(ExcBal, Alt_Currency)
                    
                    print color.BOLD+color.BLUE+"Now Working Asset Currency:", Alt_Currency, "\nIn Pair:", CurrencyPair, " As Child of Pairings:", CurrencyPairs, " In Parent Market:", Market, color.END
                    ExTradeInfo = False; ExTradeDict = False; ExTradeHistAmount = 15
                  
                    DB_Last_Price_Avg_Str = func.check_db_for_last_avg('Exchange', CurrencyPair)
                    DB_Last_Price_Avg = float(DB_Last_Price_Avg_Str)

                    DB_Last_Price_Str = func.check_db_for_last_price('Exchange', CurrencyPair)
                    DB_Last_Price = float(DB_Last_Price_Str)

                    Base_Currency_USDT_Price = float(func.Convert_Base_to_USDT(CurrencyPair, Market))
                    Alt_Currency_USDT_Price = float(func.Convert_Alt_to_USDT(CurrencyPair, Market))
                    
                    Ex_Trade_Prices = []
                    
                    #****************
                    # Past & Recent Rate Variables 
                    #***********
                  
                    Ex_Recent_Buy_Orders = []
                    Ex_Recent_Sell_Orders = []
                    Ex_Past_Buy_Orders = []
                    Ex_Past_Sell_Orders = []
                    ExTradeType = 'Any'

                    #*****************

                    ExTradeHistory = func.Get_Trade_History(CurrencyPair, TimeSpan)
                    if ExTradeHistory:
                        ExTradeInfo = func.Get_Info_From_History(CurrencyPair, ExTradeHistory, ExTradeHistAmount)

                    if ExTradeInfo:
                        
                        Ex_Recent_Sell_Orders = []
                        Ex_Recent_Buy_Orders = []

                        ExLastTrade = ExTradeInfo[0]
                        #print ExTradeInfo
                        #func.Insert_ExTrade_to_DB(ExTrade['type'], ExTrade['currencypair'], ExTrade['rate'], ExTrade['amount'], ExTrade['date'])                        
                        for ExTrade in ExTradeInfo:
                            
                            Ex_Recent_Sell_Orders = []
                            Ex_Recent_Buy_Orders = []

                            #****************
       #****#               # Sort & Compare/Test: Past & Recent Average Order Rates
                            #************

                         #***** SORT 
                            ExTradeType = ExTrade['type']
                            if(ExTradeType == 'sell'):
                                Ex_Recent_Sell_Orders.append(ExTrade['rate'])
                            else:
                                Ex_Recent_Buy_Orders.append(ExTrade['rate'])
                         #******************
                      
                            Ex_Trade_Prices.append(ExTrade['rate'])
#                            func.Insert_ExTrade_to_DB(ExTrade['type'], ExTrade['currencypair'], ExTrade['rate'], ExTrade['amount'], ExTrade['date'])                        

                          #****** COMPARE/TEST (Outside of Sorting Loop)
                            
                            # Compare Past & Recent Order Rates by Actual Rate Differences & Trigger Percentage Differences
                            # Future Tests -> Determine if either the Rate Difference or the Percentage Difference is enough to trigger a Buy or Sell regardless
                             
                             #if (Recent Buy Order Rate AVG - Past Order Rate AVG)  > 0    (Getting more expensive to buy so we want to check if we should sell)
                                # Check if we should Sell this iteration
                                 #TRIGGER if: the difference percentage((recent sell order rate - past sell order rate)/past sell rate) < 10% (0.1) 
                                    #Attempt SELL Order of a smaller percentage of asset to acquire the market currency
                                 #TRIGGER elif: the difference percentage((recent sell order rate - past sell order rate)/past sell rate) < 20% (0.20) 
                                    #Attempt SELL scalable to each trigger....

                             #else (rate to buy is decreasing so we might want to buy again)                           
                                # Check if we should Buy this iteration
                                 #TRIGGERS!!                      
                            
                            # Compare Past & Recent Order USDT $ Amounts by Actual USDT $ Amount Differences & Trigger Percentage Differences


        
                          #*******************

                        #Alt_USDT_Price = func.Convert_Alt_to_USDT(CurrencyPair, Market)
                        FloatRates = map(float,Ex_Trade_Prices)                                
                        ExTime = time.time()
                        ExListCount = len(FloatRates)

                        # Ex_Recent_Sell_Orders
                        # Ex_Recent_Buy_Orders
                        #
                        #if(Ex_Recent_Sell_Orders[len(Ex_Recent_Sell_Orders)-1] != 0):
                        #    SellLatestRate = Ex_Recent_Sell_Orders[len(Ex_Recent_Sell_Orders)-1]
                        #    SellCheapRate = min(Ex_Recent_Sell_Orders)
                        #    SellHighRate = max(Ex_Recent_Sell_Orders)
                        #    SellPriceAvg = numpy.mean(Ex_Recent_Sell_Orders)
                        #if(Ex_Recent_Buy_Orders[len(Ex_Recent_Buy_Orders)-1] != 0):
                        #    BuyLatestRate = Ex_Recent_Buy_Orders[len(Ex_Recent_Buy_Orders)-1]
                        #    BuyCheapRate = min(Ex_Recent_Buy_Orders)
                        #    BuyHighRate = max(Ex_Recent_Buy_Orders)
                        #    BuyPriceAvg = numpy.mean(Ex_Recent_Buy_Orders)

                        if(FloatRates[len(FloatRates)-1] != 0):
                            LatestRate = FloatRates[len(FloatRates)-1]
                            CheapRate = min(FloatRates)
                            HighRate = max(FloatRates)
                            PriceAvg = numpy.mean(FloatRates)
                                                 
                        m = 0
                        Decimal_Latest_Price = Decimal(LatestRate)           

                        for FloatRate in FloatRates:
                            
                            m = m + 1                            
                            DecimalFloatRate = Decimal(FloatRate)

                            if (m != len(FloatRates)):                                                        
                                if (DecimalFloatRate == Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.YELLOW+'='+str(FloatRate)+color.END+', '
                                    sys.stdout.write(ColorRate)
                                elif (DecimalFloatRate < Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.GREEN+'v'+str(FloatRate)+color.END+', '
                                    sys.stdout.write(ColorRate)
                                else: #(DecimalFloatRate > Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.RED+'^'+str(FloatRate)+color.END+', '
                                    sys.stdout.write(ColorRate)
                            else:
                                if (DecimalFloatRate == Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.YELLOW+'='+str(FloatRate)+color.END
                                    sys.stdout.write(ColorRate)
                                elif (DecimalFloatRate < Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.GREEN+'v'+str(FloatRate)+color.END
                                    sys.stdout.write(ColorRate)
                                else: #(DecimalFloatRate > Decimal_Latest_Price):
                                    ColorRate = color.BOLD+color.RED+'^'+str(FloatRate)+color.END
                                    sys.stdout.write(ColorRate)                                

                        print "\nWriting Price Array to DB...\n"
                        func.Insert_Price_Array_to_DB(ExTradeInfo)
                        func.Insert_ExTrade_to_DB('Average', CurrencyPair, PriceAvg, ExListCount, ExTime)                                
                        print "\nWriting Average Price of"+color.BLUE, PriceAvg, color.END+"to DB for"+color.BLUE, CurrencyPair, color.END
                        print "\nWriting Latest Price of"+color.BLUE, LatestRate,color.END+"to DB for"+color.BLUE, CurrencyPair, color.END

                        Base_Balance = func.Get_Balance(ExcBal, Base_Currency)
                        Alt_Balance = func.Get_Balance(ExcBal, Alt_Currency)

                        print "Last Price From The Database:", DB_Last_Price
                        print "Latest Price from Exchange:", LatestRate
                        print "Base Currency Price in USDT:", Base_Currency_USDT_Price
                        print "Alt Currency Price in USDT:", Alt_Currency_USDT_Price     
                        
                        print "Balance for", Base_Currency,":", Base_Balance;
                        print "Balance for", Alt_Currency,":", Alt_Balance; 
                       
                        #print "\n"

                        # Integrate risk assesment checks for profitability accounting for:
                        # 
                        # [X] percentage of differences, 
                        # [X] last traded rate by us (Trade Database),
                        # [X] Balance > Min Balance && 
                        # [-] Amount of Potential Profit 
                        # 
                        # Allowing us to calculate our total target Balance willing to trade for this target currency
                        
                ##--------- RISK ASSESMENT ----------##
                        ## Risk is going to be based on the weight of the values of each affected variable:

                        if(float(Alt_Balance) > float(0.00000000)):
                            print "Current Asset Balance:", Alt_Balance                            

                        if(float(Base_Balance) > float(0.00000000)):
                            print "Current Base Balance:", Base_Balance
                        
                        if((float(Alt_Balance) > float(0.00000000)) or (float(Base_Balance) > float(0.00000000))): # **check to fix!!!

                            Ex_last_price = float(func.check_db_for_last_price('Exchange', CurrencyPair))
                            Tr_last_price = float(func.check_db_for_last_price('Trade', CurrencyPair))

                            if(Tr_last_price):
                                print "Last Trade Value of Asset Currency (", CurrencyPair, "):", Tr_last_price
                            else:
                                Tr_last_price = Ex_last_price
                                #print "Setting Last Trade to last Exchange Price for", CurrencyPair, ":", Tr_last_price

                            #print "Last Exchange Price for", CurrencyPair, ":", Ex_last_price
                            if(float(Ex_last_price) > float(Tr_last_price)):
                                print "\nExchange Rate Is Higher Than The Last Trade Rate!\n" , Ex_last_price, " > " , Tr_last_price
                                
                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                                    
                                    print "... Deciding whether to sell the Asset (", Alt_Currency, ") to gain (", Base_Currency, ") ...]\n"

                                    selling_diff = abs(func.Calc_Diff(Tr_last_price, Ex_last_price))
                                    print "Difference of the Most-Recent-Exchange and Previous-Trade Values: ", selling_diff

                                    selling_diff_market_perc = (selling_diff /((Tr_last_price+Ex_last_price)/2))
                                    print "Difference of Both Values as a Percentage: %", selling_diff_market_perc
                                        
                                    selling_diff_usdt = abs(func.Convert_Amt_USDT(selling_diff, CurrencyPair, Market))
                                    print "Difference of Both Amounts : $", selling_diff_usdt

                                    diff_perc_sell = abs(func.Calc_Diff_Perc(Ex_last_price, (Tr_last_price * selling_fee)))
                                    print "Percentage of Difference of Both. Expressed: %", (diff_perc_sell * 100), " Actual: ", diff_perc_sell 

                                    print "Added Percent Multiplier to Difference with Fee. Expressed: %", (float(diff_perc_buy + .5) * 100), " Actual: ", float(diff_perc_buy + .5)  

                                    sell_invest_percent = abs(float(selling_diff_market_perc) + float(selling_diff_market_perc * 0.5))
                                    print "Suggested Sell Investment's Percentage Multiplier. Expressed: %", (sell_invest_percent * 100), " Actual: ", sell_invest_percent

                                    if((float(Alt_Balance) > float(0.00000000))):
                                        if(sell_invest_percent != 0):
                                            sell_amount = (float(Alt_Balance) * float(sell_invest_percent))
                                        else:
                                            print "Suggested Sell Investment's Percentage Multiplier is still Zero!"
                                    else:
                                        sell_amount = 0

                                    sell_amount_usdt = func.Convert_Amt_USDT(sell_amount, CurrencyPair, Market)
                                    print "Suggested Actual Currency Selling Amount: ", float(sell_amount)
                                    print "Suggested Selling Amount in USDT: $", sell_amount_usdt
                                else:
                                    
                                    print "\n**ERROR!: [1] Skipping Individual Currencies with Zero Balance!**\n"
                                    
                                    
                            elif(float(Ex_last_price) < float(Tr_last_price)):
                                print "\nExchange Rate Lower than last Trade Rate!\n" , Ex_last_price, " < " , Tr_last_price
                                
                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                                    
                                    print "... Deciding whetherto attempt buying the Market (", Base_Currency, ") with our Asset (", Alt_Currency, ") ...]\n"

                                    buying_diff = abs(func.Calc_Diff(Tr_last_price, Ex_last_price))   
                                    print "Difference in Both Prices:", buying_diff
   
                                    buying_diff_market_perc = abs(buying_diff / ((Tr_last_price+Ex_last_price)/2))
                                    print "Percent Difference in Both Prices: %", buying_diff_market_perc

                                    buying_diff_usdt = abs(func.Convert_Amt_USDT(buying_diff, CurrencyPair, Market))
                                    print "USDT Difference in Both Prices: $", buying_diff_usdt
                                    
                                    buying_fee = (float(1.0015) * float(Base_Balance))
                                    print "Buying Fee as Percentage: %", buying_fee 

                                    diff_perc_buy = abs(func.Calc_Diff_Perc(Ex_last_price, (Tr_last_price * buying_fee)))
                                    print "Percentage of Difference of Both Without Fee Expressed: %", (diff_perc_buy * 100), " Actual: ", diff_perc_buy 

                                    print "Fee Percentage Multiplier applied to Difference. Expressed: %", (float(diff_perc_buy + .5) * 100), " Actual: ", float(diff_perc_buy + .5)  

                                    buy_invest_percent = (float(diff_perc_buy) + float(diff_perc_buy + .5)) 
                                    print "Total Suggested Investment Percentage of Buying. Expressed: %", (buy_invest_percent * 100), " Actual: ", buy_invest_percent

                                    if(float(Base_Balance) > float(0.00000000)):
                                        if(buy_invest_percent != 0):
                                            buy_amount = abs(float(Base_Balance) * float(buy_invest_percent))
                                        else:
                                            buy_amount = 0
                                            print "**ERROR!: [11] Suggested Investment Percentage Multiplier is Zero!"
                                        
                                    #Buying_Amt_Final = float(buy_amount / CheapRate)
                                    buy_amount_usdt = func.Convert_Amt_USDT(buy_amount, CurrencyPair, Market)
                                    print "Suggested Buying Actual Currency Amount:", float(buy_amount)
                                    print "USDT Value if Total Suggested Currency Amount is Purchased: $", buy_amount_usdt
                                else:
                                    print "\n**ERROR!: [2] Skipping Individual Currencies with Zero Balance!\n"        

                    ### LOGIC DECISIONS FOR FINAL DETERMINATION TO CREATE A BUY OR SELL ORDER:

                            if(sell_amount_usdt > best_sell_usdt): # Take Sell_Invest_Perc * 
                                
                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                                    #bal_perc_sell = sell_invest_percent
                                    best_sell_usdt = sell_amount_usdt
                                    #print "Difference of Sell Percentage:", sell_invest_percent
                                    
                       #*#Selling Alt to get Market/Base

                                    if(CurrencyPair in Poloniex_Minimum_Trades_Sell):
                                        
                                        Selling_Min_Amt = float(Poloniex_Minimum_Trades_Sell[CurrencyPair])
                                        print "Selling Minimum Currency Amount: ", Selling_Min_Amt
                                    else:
                                        Selling_Min_Amt = 0
                                        print "\nNOTICE: No Recorded Selling Minimum!\n"

                                    Selling_Amt_Final = abs(float(Alt_Balance) * float(sell_invest_percent))
                                    #Selling_Amt_Final = float(sell_amount / HighRate)

                                    #print "\nFinal Selling Amount:", Selling_Amt_Final
                                    #print "\nSelling Minimum:", Selling_Min_Amt

                                    if((Selling_Amt_Final >= Selling_Min_Amt)):
                                        if(Selling_Amt_Final <= Alt_Balance):
                                            print "\nPosting a Sell Order for", Selling_Amt_Final, " of ", ALt_Currency, " to acquire ", Base_Currency, " in ", CurrencyPair
                                            Best_Profits_Selling = {"Currency_Pair": CurrencyPair, "Amount": Selling_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": HighRate, "Perc_Diff": diff_perc_sell, "Minimum": Selling_Min_Amt}
                                        else:  #(Selling_Amt_Final > Alt_Balance)
                                            Selling_Amt_Final = Alt_Balance
                                            print "\nPosting a Sell Order for", Selling_Amt_Final, " of ", ALt_Currency, " to acquire ", Base_Currency, " in ", CurrencyPair
                                            Best_Profits_Selling = {"Currency_Pair": CurrencyPair, "Amount": Selling_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": HighRate, "Perc_Diff": diff_perc_sell, "Minimum": Selling_Min_Amt}
                                    else:
                                        print "\nNOTICE: Not Posting Trade! Under Minimum Trade Amount! Suggested:", Selling_Amt_Final
                                else:
                                    print "\n**ERROR!: [3] Skipping Individual Currencies with Zero Balance!\n"

                            elif(buy_amount_usdt > best_buy_usdt):

                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                                    #bal_perc_buy = buy_invest_percent
                                    best_buy_usdt = buy_amount_usdt                           
                                    #print "Difference of Buy Percentage:", buy_invest_percent

                                    #Buying Market with Alt

                                    if(CurrencyPair in Poloniex_Minimum_Trades_Buy):
                                        Buying_Min_Amt = float(Poloniex_Minimum_Trades_Buy[CurrencyPair])
                                        print "Buying Minimum:", Buying_Min_Amt
                                    else:
                                        Buying_Min_Amt = 0
                                        print "\nNOTICE: No Recorded Buying Minimum!\n"
    
                                    Buying_Amt_Final = abs(float(Base_Balance) * float(buy_invest_percent))
                                    #Buying_Amt_Final = float(buy_amount / CheapRate)

                                    #print "Setting Buy Amount for", Alt_Currency, "at", Buying_Amt_Final, "out of", Alt_Balance
                                    #print "\nFinal Buying Amount:", Buying_Amt_Final
                                    #print "\nBuying Min:", Buying_Min_Amt
                                    
                                    if(Buying_Amt_Final >= Buying_Min_Amt):

                                  ###!?!!!?!*** <(_ TRIGGERS _)> IMPLEMENTATION VARIABLES?!?! ***!?!!!?!###

                                        if(Buying_Amt_Final <= Base_Balance):
                                            print "\nPlacing a Buy Order of", Buying_Amt_Final, " for ", Alt_Currency, " with ", Base_Currency, "in", CurrencyPair, "at", CheapRate
                                            Best_Profits_Buying = {"Currency_Pair": CurrencyPair, "Amount": Buying_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": CheapRate, "Perc_Diff": diff_perc_buy, "Minimum": Buying_Min_Amt}
                                        else:  #(Buying_Amt_Final > Base_Balance)
                                            Buying_Amt_Final = Base_Balance
                                            print "\Placing a Buy Order of", Buying_Amt_Final, "(ALL OUR BASE!) for ", Alt_Currency, " with ", Base_Currency, "in", CurrencyPair, "at", CheapRate
                                            Best_Profits_Buying = {"Currency_Pair": CurrencyPair, "Amount": Buying_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": CheapRate, "Perc_Diff": diff_perc_buy, "Minimum": Buying_Min_Amt}
                                    else:
                                        print "\nNot Setting Trade! Error: Under Minimum Trade Amount! Suggested: ", Buying_Amt_Final
                                else:
                                    print "\n*** ERROR!: [4] Skipping Individual Currencies with Zero Balance!\n"
                        else:
                            print "\n*** NOTICE!: [7] Skipping Individual Currencies with Zero Balance!\n"

          # ! START ! ###:[*'*'*~ OLD CODE 'BUY OR SELL?' EARLY DECISION BLOCK! ~*'*'*]:###

                        ##if(float(Alt_Balance) > float(0.00000000)):
                        ##    print "Alt Bal:", Alt_Balance                            

                        ##if(float(Base_Balance) > float(0.00000000)):
                        ##    print "Base Bal:", Base_Balance
                        
                        #if((float(Alt_Balance) > float(0.00000000)) or (float(Base_Balance) > float(0.00000000))):

                        #    Ex_last_price = float(func.check_db_for_last_price('Exchange', CurrencyPair))
                        #    Tr_last_price = float(func.check_db_for_last_price('Trade', CurrencyPair))

                        #    if(Tr_last_price):
                        #        print "Last Trade Price for", CurrencyPair, ":", Tr_last_price
                        #    else:
                        #        Tr_last_price = Ex_last_price
                        #        #print "Setting Last Trade to last Exchange Price for", CurrencyPair, ":", Tr_last_price

                        #    #print "Last Exchange Price for", CurrencyPair, ":", Ex_last_price
                        #    if(float(Ex_last_price) > float(Tr_last_price)):
                        #        if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                        #            print "\nExchange Rate Higher than last Trade Rate!\n", Ex_last_price, Tr_last_price
                        #            #Selling Alt to get Market/Base

                        #            selling_diff = func.Calc_Diff(Ex_last_price, Tr_last_price)
                        #            print "Difference in Both Prices:", selling_diff

                        #            selling_diff_market_perc = selling_diff / Ex_last_price
                        #            print "Percent Difference in Both Prices:", selling_diff_market_perc
                                        
                        #            selling_diff_usdt = func.Convert_Amt_USDT(selling_diff, CurrencyPair, Market)
                        #            print "USDT Difference in Both Prices:", selling_diff_usdt

                        #            diff_perc_sell = func.Calc_Diff_Perc(Ex_last_price, Tr_last_price) * selling_fee
                        #            #print "Percentage of Difference in Both:", diff_perc_sell

                        #            sell_invest_percent = float(diff_perc_sell * 1.5)
                        #            print "Invest Percentage for Selling:", sell_invest_percent

                        #            if( float(Alt_Balance) > float(0.00000000) ):
                        #                if(bal_perc_sell != 0):
                        #                    sell_amount = float(Alt_Balance) * float(bal_perc_sell)
                        #                else:
                        #                    sell_amount = float(Alt_Balance) * float(sell_invest_percent)
                        #            else:
                        #                sell_amount = 0

                        #            sell_amount_usdt = func.Convert_Amt_USDT(sell_amount, CurrencyPair, Market)
                        #            print "Sell Amount:", sell_amount
                        #            print "Sell Amount in USDT:", sell_amount_usdt
                        #        else:
                        #            print "\n1Skipping Individual Currencies with Zero Balance!\n"
                        #    if(float(Ex_last_price) < float(Tr_last_price)):

                        #        if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                        #            print "\nExchange Rate Lower than last Trade Rate!\n", Ex_last_price, Tr_last_price
                        #            #Buying Alt with Market/Base

                        #            buying_diff = func.Calc_Diff(Tr_last_price, Ex_last_price)   
                        #            print "Difference in Both Prices:", buying_diff
   
                        #            buying_diff_market_perc = buying_diff / Ex_last_price
                        #            print "Percent Difference in Both Prices:", buying_diff_market_perc

                        #            buying_diff_usdt = func.Convert_Amt_USDT(buying_diff, CurrencyPair, Market)
                        #            print "USDT Difference in Both Prices:", buying_diff_usdt

                        #            diff_perc_buy = func.Calc_Diff_Perc(Tr_last_price, Ex_last_price) * buying_fee                   
                        #            #print "Percentage of Difference in Both:", diff_perc_buy
                        #            buy_invest_percent = float(diff_perc_buy * 1.5)
                        #            print "Invest Percentage for Buying:", buy_invest_percent

                        #            if(float(Base_Balance) > float(0.00000000)):
                        #                if(bal_perc_buy != 0):
                        #                    buy_amount = float(Base_Balance) * float(bal_perc_buy)
                        #                else:
                        #                    buy_amount = float(Base_Balance) * float(buy_invest_percent)
                        #            else:
                        #                buy_amount = 0
                        #            Buying_Amt_Final = float(buy_amount / CheapRate)
                        #            buy_amount_usdt = func.Convert_Amt_USDT(buy_amount, CurrencyPair, Market)
                        #            print "Buy Amount:", buy_amount
                        #            print "Buy Amount in USDT:", buy_amount_usdt
                        #        else:
                        #            print "\n2Skipping Individual Currencies with Zero Balance!\n"        

                        #    if(sell_amount_usdt > best_sell_usdt): # Take Sell_Invest_Perc * 
                                
                        #        if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                        #            bal_perc_sell = sell_invest_percent
                        #            best_sell_usdt = sell_amount_usdt
                        #            #print "Difference of Sell Percentage:", sell_invest_percent
                        #            #Selling Alt to get Market/Base

                        #            if(CurrencyPair in Poloniex_Minimum_Trades_Sell):
                        #                Selling_Min_Amt = float(Poloniex_Minimum_Trades_Sell[CurrencyPair])
                        #                print "Selling Minimum:", Selling_Min_Amt
                        #            else:
                        #                Selling_Min_Amt = 0
                        #                print "Selling Minimum:", Selling_Min_Amt

                        #            sell_amount = float(Alt_Balance) * float(bal_perc_sell)
                        #            Selling_Amt_Final = float(sell_amount / HighRate)

                        #            print "\nFinal Selling Amount:", Selling_Amt_Final
                        #            print "\nSelling Min:", Selling_Min_Amt

                        #            if((Selling_Amt_Final >= Selling_Min_Amt)):
                        #                print "\nSetting a Sell at", Selling_Amt_Final, "for", Base_Currency, "in", CurrencyPair, "at", HighRate
                        #                Best_Profits_Selling = {"Currency_Pair": CurrencyPair, "Amount": Selling_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": HighRate, "Perc_Diff": diff_perc_sell, "Minimum": Selling_Min_Amt}
                        #            else:
                        #                print "\nNot Setting Trade under Minimum Trade Amount:", Selling_Amt_Final
                        #        else:
                        #            print "\n3Skipping Individual Currencies with Zero Balance!\n"


                        #    elif(buy_amount_usdt > best_buy_usdt):

                        #        if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                        #            bal_perc_buy = buy_invest_percent
                        #            best_buy_usdt = buy_amount_usdt                           
                        #            #print "Difference of Buy Percentage:", buy_invest_percent
                        #            #Buying Market with Alt

                        #            if(CurrencyPair in Poloniex_Minimum_Trades_Buy):
                        #                Buying_Min_Amt = float(Poloniex_Minimum_Trades_Buy[CurrencyPair])
                        #                print "Buying Minimum:", Buying_Min_Amt
                        #            else:
                        #                Buying_Min_Amt = 0
                        #                print "Buying Minimum:", Buying_Min_Amt
    
                        #            buy_amount = float(Base_Balance) * float(buy_invest_percent)
                        #            Buying_Amt_Final = float(buy_amount / CheapRate)

                        #            #print "Setting Buy Amount for", Alt_Currency, "at", Buying_Amt_Final, "out of", Alt_Balance
                        #            #print "\nFinal Buying Amount:", Buying_Amt_Final
                        #            #print "\nBuying Min:", Buying_Min_Amt
                        #            if(Buying_Amt_Final >= Buying_Min_Amt):
                        #                print "\nSetting a Buy at", Buying_Amt_Final, "for", Alt_Currency, "in", CurrencyPair, "at", CheapRate
                        #                Best_Profits_Buying = {"Currency_Pair": CurrencyPair, "Amount": Buying_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": CheapRate, "Perc_Diff": diff_perc_buy, "Minimum": Buying_Min_Amt}
                        #            else:
                        #                print "\nNot Setting Trade under Minimum Trade Amount:", Buying_Amt_Final
                        #        else:
                        #            print "\n4Skipping Individual Currencies with Zero Balance!\n"
                        #else:
                        #    print "\nSkipping Currency Pairs with Zero Balance!\n"

            # ! END ! #:#!#[*'*'*~ OLD CODE 'BUY OR SELL?' EARLY DECISION BLOCK! ~*'*'*]#!#:##

            if(Best_Profits_Selling):
                print Best_Profits_Selling
                best_profits_selling_pair = Best_Profits_Selling["Currency_Pair"]
                Selling_Amt = Best_Profits_Selling["Amount"]
                Selling_Base = Best_Profits_Selling["Base_Currency"]
                Selling_Alt = Best_Profits_Selling["Alt_Currency"]
                Selling_Price = Best_Profits_Selling["Rate"]
                Selling_Min = Best_Profits_Selling["Minimum"]
                Selling_Perc_Diff = Best_Profits_Selling["Perc_Diff"]
                print "Selling Amount:", Selling_Amt

            if(Best_Profits_Buying):    
                print Best_Profits_Buying
                best_profits_buying_pair = Best_Profits_Buying["Currency_Pair"]
                Buying_Amt = Best_Profits_Buying["Amount"]
                Buying_Base = Best_Profits_Buying["Base_Currency"]
                Buying_Alt = Best_Profits_Buying["Alt_Currency"]
                Buying_Price = Best_Profits_Buying["Rate"]
                Buying_Min = Best_Profits_Buying["Minimum"]
                Buying_Perc_Diff = Best_Profits_Buying["Perc_Diff"]
                print "Buying Amount:", Buying_Amt

            if(Best_Profits_Buying and Best_Profits_Selling):
                print "Best Profits Options Set!"
                if(best_profits_buying_pair == best_profits_selling_pair):
                    if(bal_perc_buy > bal_perc_sell):
                        if(float(Buying_Amt) >= float(Buying_Min)):
                            if(float(Buying_Amt) > float(0.00000000)):
                                print "\n1Selling ",Buying_Amt," of ",Buying_Alt," with ",Buying_Base,' @ ',Buying_Price,'for a total of:', Buying_Amt
                                #Polo.sell(best_profits_buying_pair, Buying_Price, Buying_Amt)
                                func.Insert_Trade_to_DB('sell', best_profits_buying_pair, Buying_Price, Buying_Amt, time.time())
                            else:
                                print "Not Enough in Balance for Trade!", Buying_Amt, Buying_Min    
                        else: 
                            print "1Trade", Buying_Amt, "doesn't Meet Minimum Requirements of", Buying_Min, "or nothing to Trade!"
                    else:
                        if(float(Selling_Amt) >= float(Selling_Min)):
                            if(float(Selling_Amt) > float(0.00000000)):
                                print "\n2Buying ",Selling_Amt," of ",Selling_Alt," in ",Selling_Base,' @ ', Selling_Price,'for a total of:', Selling_Amt
                                #Polo.buy(best_profits_selling_pair, Selling_Price, Selling_Amt)
                                func.Insert_Trade_to_DB('buy', best_profits_selling_pair, Selling_Price, Selling_Amt, time.time())
                            else:
                                print "Not Enough in Balance for Trade!", Selling_Amt, Selling_Min                     
                        else: 
                            print "2Trade", Selling_Amt, "doesn't Meet Minimum Requirements of", Selling_Min, "or nothing to Trade!"
                
            elif((Best_Profits_Buying) or (Best_Profits_Selling)):
                if(Best_Profits_Selling):
                    print "Not Empty!"
                    if(float(Buying_Amt) >= float(Buying_Min)):
                        if(float(Buying_Amt) > float(0.00000000)):
                            print "\n3Selling ",Buying_Amt," of ",Buying_Alt," with ", Buying_Base,' @ ',Buying_Price,'for a total of:', Buying_Amt
                            #Polo.sell(best_profits_buying_pair, Buying_Price, Buying_Amt)
                            func.Insert_Trade_to_DB('sell', best_profits_buying_pair, Buying_Price, Buying_Amt, time.time())
                        else:
                            print "Not Enough in Balance for Trade!", Buying_Amt, Buying_Min    
                    else: 
                        print "3Trade", Buying_Amt, "doesn't Meet Minimum Requirements of", Buying_Min, "or nothing to Trade!"
                else:
                    print "Best_Profits_Buying seems to be Empty!"

                if(Best_Profits_Selling):
                    print "Not Empty!"
                    if(float(Selling_Amt) >= float(Selling_Min)):
                        if(float(Selling_Amt) > float(0.00000000)):
                            print "\n4Buying ",Selling_Amt," of ",Selling_Alt," with ", Selling_Base,' @ ',Selling_Price,'for a total of:', Selling_Amt     
                            #Polo.buy(best_profits_selling_pair, Selling_Price, Selling_Amt)
                            func.Insert_Trade_to_DB('buy', best_profits_selling_pair, Selling_Price, Selling_Amt, time.time())
                        else:
                            print "Not Enough in Balance for Trade!", Alt_Balance, Base_Balance, Selling_Amt, Selling_Min 
                    else: 
                        print "4Trade", Selling_Amt, "doesn't Meet Minimum Requirements of", Selling_Min, "or nothing to Trade!"            
                else:
                    print "Best_Profits_Selling seems to be Empty!"
            else:
                print "No Buying or Selling Options Set!"


            print color.UNDERLINE+color.BOLD+line+color.END+""    
            most_active_pair = func.check_most_active_coin(poll_delay)
            most_active_coin = most_active_pair[0]
            active_count = most_active_pair[1]
            
            print color.UNDERLINE+color.BOLD+"\nMost Active Pair:\n\n"+color.END+color.BOLD+color.BLUE+most_active_coin+color.END+" with"+color.BOLD+color.BLUE, active_count, color.END+"transactions in last"+color.BLUE, TimeSpan, color.END+"seconds."  
            print "\nCheapest Rate:", color.BOLD+color.BLUE, CheapRate, color.END  ## List
            print "\nLatest Rate:", color.BOLD+color.BLUE, LatestRate, color.END

            Ex_last_price = float(func.check_db_for_last_price('Exchange', most_active_coin))
            print "\nLast Price from Exchange:", color.BOLD+color.BLUE, Ex_last_price, color.END
            print "Cheap Pairs: ", LatestRateDown

            print "Best_Profits_Selling:", Best_Profits_Selling
            print "Best_Profits_Buying:", Best_Profits_Buying

            markets = CurrencyPairs
            currencyindex = 0
        
        
    ##+++++++++++!!!!!!!!!!!!      CODE? THERE IS NO CODE       !!!!!!!!!!!+++++++++++++++##        
        except exchange_api.ExchangeException as e:
            #func._Log('Failed to get %s balances: %s', Exchange.GetName(), e)
            continue
                
        print "\n\nSleeping for",poll_delay,"\n"
        time.sleep(poll_delay)
