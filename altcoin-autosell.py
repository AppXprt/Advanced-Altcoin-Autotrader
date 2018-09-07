#!/usr/bin/python
#-*- coding: ASCII -*-
import os
import sys
import time
import dataset
import numpy
import math
import requests
#import pandas

import func
import dataset
import argparse
import exchange_api
import logging

from pprint import pprint
from poloniex import Poloniex
#from fbprophet import Prophet
from decimal import Decimal
#from movingaverages import BotIndicators 

logging.getLogger("requests").setLevel(logging.WARNING)

try:
    import configparser
except ImportError:
    # Python 2.7 compatibility
    import ConfigParser
    configparser = ConfigParser
    
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
   
global StartTime, BalFile, TransFile, Polo, Balance, Get, markets, poll_delay, PriceDB, TradeDB, exchanges, exchange, target_currencies, CurrencyPairs, CurrencyPair, TimeSpan, line

LatestRateUp = []; LatestRateDown = []; LatestRateUpAvg = []; LatestRateDownAvg = []; 
LatestRateUpDBAvg = []; LatestRateDownDBAvg = []; LatestRateUpDB_Last_Price = []; LatestRateDownDB_Last_Price = [];
LatestRateEq = []; LatestRateEqAvg = []; LatestRateEqDBAvg = []; LatestRateEqDB_Last_Price = []; LatestRateEqDB_Last_Price = []; Best_Profits_Buying = {}; Best_Profits_Selling = {};

Poloniex_Minimum_Trades_Buy = {"USDT_XRP": .5, "USDT_LTC": .5, "USDT_DASH": .5, "USDT_BTC": .5, "BTC_LTC": .0001, "BTC_ETH": .0001}
Poloniex_Minimum_Trades_Sell = {"BTC_LTC":.0001}

best_base_sell = ''
best_alt_sell = ''
best_base_buy = ''
best_alt_buy = ''

best_profits_buying_pair = ''
best_profits_selling_pair = ''

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

while True:
    
    for Exchange in Exchanges:
        #Best_Profits_Selling = {}
        #Best_Profits_Buying = {}
        bal_perc_buy = 0
        bal_perc_sell = 0
        buying_fee = 0.25
        selling_fee = 0.15
        diff_perc_buy = 0
        diff_perc_sell = 0
        buy_amount_usdt = 0
        sell_amount_usdt = 0
        print color.BOLD+color.BLUE+"Working in", Exchange,"Exchange..."+color.END
                       
        try:
            ExcBal = eval(Exchange).returnBalances()
            tarprint = ""; sorprint = ""   
            
            Markets = func.Get_DB_Markets()   
            for Market in Markets:
                
                print color.BOLD+color.BLUE+"Working in", Market, "Market of", Markets,color.END
                
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
                    
                    print color.BOLD+color.BLUE+"Working with ", Alt_Currency, "in", CurrencyPair, "in", CurrencyPairs, color.END
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
                  
                    Ex_Present_Buy_Orders = []
                    Ex_Present_Sell_Orders = []
                    Ex_Past_Buy_Orders = []
                    Ex_Past_Sell_Orders = []
                    ExTradeType = 'Any'

                    #*****************

                    ExTradeHistory = func.Get_Trade_History(CurrencyPair, TimeSpan)
                    if ExTradeHistory:
                        ExTradeInfo = func.Get_Info_From_History(CurrencyPair, ExTradeHistory, ExTradeHistAmount)

                    if ExTradeInfo:
                        ExLastTrade = ExTradeInfo[0]
                        print ExTradeInfo
                        for ExTrade in ExTradeInfo:
                            
                            #****************
                            # Sort & Compare/Test: Past & Recent Average Order Rates
                            #************

                                #***** SORT 
                           # ExTradeType = ExTrade['type']
                           # if(ExTradeType == 'sell'):
                           #     Ex_Recent_Sell_Orders.append(ExTrade['rate'])
                           # else:
                           #     Ex_Recent_Buy_Orders.append(ExTrade['rate'])

                                #******************
                        
                            Ex_Trade_Prices.append(ExTrade['rate'])
                            func.Insert_ExTrade_to_DB(ExTrade['type'], ExTrade['currencypair'], ExTrade['rate'], ExTrade['amount'], ExTrade['date'])                        
                            
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

                        if(FloatRates[len(FloatRates)-1] != 0):
                            LatestRate = FloatRates[len(FloatRates)-1]
                            CheapRate = min(FloatRates)
                            HighRate = max(FloatRates)
                            PriceAvg = numpy.mean(FloatRates)
                                                 
                        Decimal_Latest_Price = Decimal(LatestRate)           
                        for FloatRate in FloatRates:
                            DecimalFloatRate = Decimal(FloatRate)
                            if (DecimalFloatRate == Decimal_Latest_Price):
                                ColorRate = color.BOLD+color.YELLOW+'='+str(FloatRate)+color.END+', '
                                sys.stdout.write(ColorRate)
                            if (DecimalFloatRate < Decimal_Latest_Price):
                                ColorRate = color.BOLD+color.GREEN+'v'+str(FloatRate)+color.END+', '
                                sys.stdout.write(ColorRate)
                            if (DecimalFloatRate > Decimal_Latest_Price):
                                ColorRate = color.BOLD+color.RED+'^'+str(FloatRate)+color.END+', '
                                sys.stdout.write(ColorRate)     
                       
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
                        print "\n"

                        # Integrate risk assesment checks for profitability accounting for fee's, percentage of 
                        # differences, last traded rate by us (Trade Database), Balance, and Amount of Potential Profit in Below Code
                        # Allowing us to calculate our total target Balance willing to trade for this target currency
                        
                        ##--------- RISK ASSESMENT ----------##
                        ## Risk is going to be based on the weight of the values of each affected variable:

                        #if(float(Alt_Balance) > float(0.00000000)):
                        #    print "Alt Bal:", Alt_Balance                            

                        #if(float(Base_Balance) > float(0.00000000)):
                        #    print "Base Bal:", Base_Balance
                        
                        if((float(Alt_Balance) > float(0.00000000)) or (float(Base_Balance) > float(0.00000000))):

                            Ex_last_price = float(func.check_db_for_last_price('Exchange', CurrencyPair))
                            Tr_last_price = float(func.check_db_for_last_price('Trade', CurrencyPair))

                            if(Tr_last_price):
                                print "Last Trade Price for", CurrencyPair, ":", Tr_last_price
                            else:
                                Tr_last_price = Ex_last_price
                                #print "Setting Last Trade to last Exchange Price for", CurrencyPair, ":", Tr_last_price

                            #print "Last Exchange Price for", CurrencyPair, ":", Ex_last_price
                            if(float(Ex_last_price) > float(Tr_last_price)):
                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                                    print "\nExchange Rate Higher than last Trade Rate!\n", Ex_last_price, Tr_last_price
                                    #Selling Alt to get Market/Base

                                    selling_diff = func.Calc_Diff(Ex_last_price, Tr_last_price)
                                    print "Difference in Both Prices:", selling_diff

                                    selling_diff_market_perc = selling_diff / Ex_last_price
                                    print "Percent Difference in Both Prices:", selling_diff_market_perc
                                        
                                    selling_diff_usdt = func.Convert_Amt_USDT(selling_diff, CurrencyPair, Market)
                                    print "USDT Difference in Both Prices:", selling_diff_usdt

                                    diff_perc_sell = func.Calc_Diff_Perc(Ex_last_price, Tr_last_price) * selling_fee
                                    #print "Percentage of Difference in Both:", diff_perc_sell

                                    sell_invest_percent = float(diff_perc_sell * 1.5)
                                    print "Invest Percentage for Selling:", sell_invest_percent

                                    if( float(Alt_Balance) > float(0.00000000) ):
                                        if(bal_perc_sell != 0):
                                            sell_amount = float(Alt_Balance) * float(bal_perc_sell)
                                        else:
                                            sell_amount = float(Alt_Balance) * float(sell_invest_percent)
                                    else:
                                        sell_amount = 0

                                    sell_amount_usdt = func.Convert_Amt_USDT(sell_amount, CurrencyPair, Market)
                                    print "Sell Amount:", sell_amount
                                    print "Sell Amount in USDT:", sell_amount_usdt
                                else:
                                    print "\n1Skipping Individual Currencies with Zero Balance!\n"
                            if(float(Ex_last_price) < float(Tr_last_price)):

                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):
                                    print "\nExchange Rate Lower than last Trade Rate!\n", Ex_last_price, Tr_last_price
                                    #Buying Alt with Market/Base

                                    buying_diff = func.Calc_Diff(Tr_last_price, Ex_last_price)   
                                    print "Difference in Both Prices:", buying_diff
   
                                    buying_diff_market_perc = buying_diff / Ex_last_price
                                    print "Percent Difference in Both Prices:", buying_diff_market_perc

                                    buying_diff_usdt = func.Convert_Amt_USDT(buying_diff, CurrencyPair, Market)
                                    print "USDT Difference in Both Prices:", buying_diff_usdt

                                    diff_perc_buy = func.Calc_Diff_Perc(Tr_last_price, Ex_last_price) * buying_fee                   
                                    #print "Percentage of Difference in Both:", diff_perc_buy
                                    buy_invest_percent = float(diff_perc_buy * 1.5)
                                    print "Invest Percentage for Buying:", buy_invest_percent

                                    if(float(Base_Balance) > float(0.00000000)):
                                        if(bal_perc_buy != 0):
                                            buy_amount = float(Base_Balance) * float(bal_perc_buy)
                                        else:
                                            buy_amount = float(Base_Balance) * float(buy_invest_percent)
                                    else:
                                        buy_amount = 0
                                    Buying_Amt_Final = float(buy_amount / CheapRate)
                                    buy_amount_usdt = func.Convert_Amt_USDT(buy_amount, CurrencyPair, Market)
                                    print "Buy Amount:", buy_amount
                                    print "Buy Amount in USDT:", buy_amount_usdt
                                else:
                                    print "\n2Skipping Individual Currencies with Zero Balance!\n"        

                            if(sell_amount_usdt > best_sell_usdt): # Take Sell_Invest_Perc * 
                                
                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                                    bal_perc_sell = sell_invest_percent
                                    best_sell_usdt = sell_amount_usdt
                                    #print "Difference of Sell Percentage:", sell_invest_percent
                                    #Selling Alt to get Market/Base

                                    if(CurrencyPair in Poloniex_Minimum_Trades_Sell):
                                        Selling_Min_Amt = float(Poloniex_Minimum_Trades_Sell[CurrencyPair])
                                        print "Selling Minimum:", Selling_Min_Amt
                                    else:
                                        Selling_Min_Amt = 0
                                        print "Selling Minimum:", Selling_Min_Amt

                                    sell_amount = float(Alt_Balance) * float(bal_perc_sell)
                                    Selling_Amt_Final = float(sell_amount / HighRate)

                                    print "\nFinal Selling Amount:", Selling_Amt_Final
                                    print "\nSelling Min:", Selling_Min_Amt

                                    if((Selling_Amt_Final >= Selling_Min_Amt)):
                                        print "\nSetting a Sell at", Selling_Amt_Final, "for", Base_Currency, "in", CurrencyPair, "at", HighRate
                                        Best_Profits_Selling = {"Currency_Pair": CurrencyPair, "Amount": Selling_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": HighRate, "Perc_Diff": diff_perc_sell, "Minimum": Selling_Min_Amt}
                                    else:
                                        print "\nNot Setting Trade under Minimum Trade Amount:", Selling_Amt_Final
                                else:
                                    print "\n3Skipping Individual Currencies with Zero Balance!\n"


                            elif(buy_amount_usdt > best_buy_usdt):

                                if((float(Base_Balance) > float(0.00000000)) or (float(Alt_Balance) > float(0.00000000))):

                                    bal_perc_buy = buy_invest_percent
                                    best_buy_usdt = buy_amount_usdt                           
                                    #print "Difference of Buy Percentage:", buy_invest_percent
                                    #Buying Market with Alt

                                    if(CurrencyPair in Poloniex_Minimum_Trades_Buy):
                                        Buying_Min_Amt = float(Poloniex_Minimum_Trades_Buy[CurrencyPair])
                                        print "Buying Minimum:", Buying_Min_Amt
                                    else:
                                        Buying_Min_Amt = 0
                                        print "Buying Minimum:", Buying_Min_Amt
    
                                    buy_amount = float(Base_Balance) * float(buy_invest_percent)
                                    Buying_Amt_Final = float(buy_amount / CheapRate)

                                    #print "Setting Buy Amount for", Alt_Currency, "at", Buying_Amt_Final, "out of", Alt_Balance
                                    #print "\nFinal Buying Amount:", Buying_Amt_Final
                                    #print "\nBuying Min:", Buying_Min_Amt
                                    if(Buying_Amt_Final >= Buying_Min_Amt):
                                        print "\nSetting a Buy at", Buying_Amt_Final, "for", Alt_Currency, "in", CurrencyPair, "at", CheapRate
                                        Best_Profits_Buying = {"Currency_Pair": CurrencyPair, "Amount": Buying_Amt_Final, "Base_Currency": Base_Currency, "Alt_Currency": Alt_Currency, "Rate": CheapRate, "Perc_Diff": diff_perc_buy, "Minimum": Buying_Min_Amt}
                                    else:
                                        print "\nNot Setting Trade under Minimum Trade Amount:", Buying_Amt_Final
                                else:
                                    print "\n4Skipping Individual Currencies with Zero Balance!\n"
                        else:
                            print "\nSkipping Currency Pairs with Zero Balance!\n"

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

            if(Best_Profits_Buying or Best_Profits_Selling):
                print "Best Profits Options Set!"
                if(best_profits_buying_pair == best_profits_selling_pair):
                    if(bal_perc_buy > bal_perc_sell):
                        if(float(Buying_Amt) >= float(Buying_Min)):
                            if(float(Buying_Amt) > float(0.00000000)): 
                                print "\n1Selling ",Buying_Amt," of ",Buying_Alt," with ",Buying_Base,' @ ',Buying_Price,'for a total of:', Buying_Amt
#                                Polo.sell(best_profits_buying_pair, Buying_Price, Buying_Amt)
                                func.Insert_Trade_to_DB('sell', best_profits_buying_pair, Buying_Price, Buying_Amt, time.time())
                            else:
                                print "Not Enough in Balance for Trade!", Buying_Amt, Buying_Min    
                        else: 
                            print "1Trade", Buying_Amt, "doesn't Meet Minimum Requirements of", Buying_Min, "or nothing to Trade!"
                    else:
                        if(float(Selling_Amt) >= float(Selling_Min)):
                            if(float(Selling_Amt) > float(0.00000000)): 
                                print "\n2Buying ",Selling_Amt," of ",Selling_Alt," in ",Selling_Base,' @ ', Selling_Price,'for a total of:', Selling_Amt
#                                Polo.buy(best_profits_selling_pair, Selling_Price, Selling_Amt)
                                func.Insert_Trade_to_DB('buy', best_profits_selling_pair, Selling_Price, Selling_Amt, time.time())
                            else:
                                print "Not Enough in Balance for Trade!", Selling_Amt, Selling_Min                     
                        else: 
                            print "2Trade", Selling_Amt, "doesn't Meet Minimum Requirements of", Selling_Min, "or nothing to Trade!"
                else:
                    if(Best_Profits_Buying):
                        print "Not Empty!"
                        if(float(Buying_Amt) >= float(Buying_Min)):
                            if(float(Buying_Amt) > float(0.00000000)):
                                print "\n3Selling ",Buying_Amt," of ",Buying_Alt," with ", Buying_Base,' @ ',Buying_Price,'for a total of:', Buying_Amt
 #                               Polo.sell(best_profits_buying_pair, Buying_Price, Buying_Amt)
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
#                                Polo.buy(best_profits_selling_pair, Selling_Price, Selling_Amt)
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

