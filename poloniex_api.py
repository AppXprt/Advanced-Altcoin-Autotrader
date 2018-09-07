import urllib
import urllib2
import requests
import json
import time
import hmac,hashlib
import uuid
import dataset
#import cryptocompare
from colorama import init
init()

global line
line = "                                                                              "    

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
    
def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))
 
class PoloniexClass:
    def __init__(self, APIKey, Secret):
        self.APIKey = APIKey
        self.Secret = Secret

    def post_process(self, before):
        after = before
 
        # Add timestamps if there isnt one but is a datetime
        if('return' in after):
            if(isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if(isinstance(after['return'][x], dict)):
                        if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
                           
        return after
 
    def api_query(self, command, req={}):
 
        if(command == "returnTicker" or command == "return24Volume"):
            ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/public?command=' + command))
            return json.loads(ret.read())
        elif(command == "returnOrderBook"):
            ret = urllib2.urlopen(urllib2.Request('http://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])))
            return json.loads(ret.read())
        elif(command == "returnMarketTradeHistory"):
            ret = urllib2.urlopen(urllib2.Request('http://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(req['currencyPair']) + '&start=' + str(req['start']) + '&end=' + str(req['end'])))
            return json.loads(ret.read())
        else:
            req['command'] = command
            req['nonce'] = int(time.time()*1000)
            post_data = urllib.urlencode(req)
 
            sign = hmac.new(self.Secret, post_data, hashlib.sha512).hexdigest()
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }
 
            ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/tradingApi', post_data, headers))
            jsonRet = json.loads(ret.read())
            return self.post_process(jsonRet)
 
 
    def returnTicker(self):
        return self.api_query("returnTicker")
 
    def return24Volume(self):
        return self.api_query("return24Volume")
 
    def returnOrderBook (self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})
 
 
    def Calculate_TimeSpan(self, TimeLengthFromNow):
        TimeSpan = int(time.time()-TimeLengthFromNow)
        return TimeSpan 
        
    def returnMarketTradeHist(self, currencyPair, TimeLengthFromNow):
        DateTime = int(time.time())
        TimeSpan = self.Calculate_TimeSpan(TimeLengthFromNow)
        print color.UNDERLINE+color.BOLD+line+color.END    
        print color.UNDERLINE+color.BOLD+currencyPair+color.END+":\n", "\nCurrent Time", color.BLUE,DateTime,color.END,"|", TimeLengthFromNow, "seconds ago:", color.BLUE, TimeSpan,color.END+"\n"
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair, 'start': TimeSpan, 'end': DateTime})
        
    # Returns all of your balances.
    # Outputs:
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def returnBalances(self):
        return self.api_query('returnBalances')
 
    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def returnOpenOrders(self,currencyPair):
        return self.api_query('returnOpenOrders',{"currencyPair":currencyPair})
 
 
    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def returnTradeHistory(self,currencyPair):
        return self.api_query('returnTradeHistory',{"currencyPair":currencyPair})
 
    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def buy(self,currencyPair,rate,amount):
        return self.api_query('buy',{"currencyPair":currencyPair,"rate":rate,"amount":amount})
 
    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def sell(self,currencyPair,rate,amount):
    	  #UUID = uuid.uuid1()
    #self.Insert_Trade_to_DB(UUID, 'Sell', currencypair, rate, amount, time.time(), 'Order')
        return self.api_query('sell',{"currencyPair":currencyPair,"rate":rate,"amount":amount})

        
    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs:
    # succes        1 or 0
    def cancel(self,currencyPair,orderNumber):
        return self.api_query('cancelOrder',{"currencyPair":currencyPair,"orderNumber":orderNumber})
 
    # Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs:
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw',{"currency":currency, "amount":amount, "address":address})
       
    #def Process_Trade_History(self, CurrencyPair, TimeSpan):
    
    def Get_Info_From_History(self, CurrencyPair, CPTradeHistory, CPTradeHistAmount):
        THInfoDict = {}
        THInfoList = []
        THPair = CurrencyPair
        for CPTrade in CPTradeHistory:        
            THRate = CPTrade[u'rate']
            THAmt = CPTrade[u'amount']
            THType = CPTrade[u'type']
            THDate = time.mktime(time.strptime(CPTrade[u'date'], "%Y-%m-%d %H:%M:%S"))
            THDict = {'currencypair': CurrencyPair, 'rate': THRate, 'amount': THAmt, 'type': THType, 'date': THDate} 
            THInfoList.append(THDict)
        #print THInfoList
        return THInfoList

    	
    def Get_Prices_From_History(self, CurrencyPair, CPTradeHistory, CPTradeHistAmount):
        THRateList = []
        for CPTrade in CPTradeHistory:           
            THRate = CPTrade['rate']
            THRateList.append(THRate)  
        return THRateList
        
    def checkEqual2(self, iterator):
       return len(set(iterator)) <= 1 
    
    #def Check_Last_Trade_price(self, OrderType, CurrencyPair):
    #    TradeDB = dataset.connect('sqlite:///Exchange.sql') 
    #    for Order in db[OrderType]:
    #        print(OrderType['price'])
    
       
    def Insert_Trade_to_DB(self, OrderType, currencypair, Price, Amount, DateTimeof, Status):
        TradeDB = dataset.connect('sqlite:///Trade.sql')
        table = TradeDB[OrderType]
        table.insert(dict(ordertype=OrderType, currencypair=currencypair, price=Price, amount=Amount, datetime=DateTimeof, status=Status))
      
    def Insert_Price_to_DB(self, OrderType, currencypair, Price, Amount, DateTimeof):
        ExchangeDB = dataset.connect('sqlite:///Exchange.sql') 
        if (OrderType == 'Average'):
            table = ExchangeDB['Averages']
        else:
            table = ExchangeDB[currencypair]
        table.insert(dict(ordertype=OrderType, currencypair=currencypair, price=Price, amount=Amount, datetime=DateTimeof))

    def check_db_for_last_avg(self, DB, CurrencyPair):
       #print "Finding Last DB Average for", CurrencyPair
       if(DB == "Trade"):
           db = dataset.connect('sqlite:///Trade.sql')
       if(DB == "Exchange"):
           db = dataset.connect('sqlite:///Exchange.sql')
       tables = db["Averages"]
       tablecount = tables.count()
       rowcount = 0
       lastavg = 0
       for row in tables:
           rowcount = rowcount+1
           rowpair = row['currencypair']
           #print "rowpair:", rowpair
           if(rowpair == CurrencyPair):
              #print "Matching Pair: ", rowpair
              lastavg = row['price']
           if(rowcount == tablecount) and (rowpair == CurrencyPair):
              lastavg = row['price']
       return lastavg
            
    #def check_db_for_last_price(self, DB, OrderType, CurrencyPair):
    #    #print "Finding Last DB Price for", CurrencyPair
    ##    if(DB == "Trade"):
    #        db = dataset.connect('sqlite:///Trade.sql')
    #    if(DB == "Exchange"):
	#        db = dataset.connect('sqlite:///Exchange.sql')
        #if (OrderType == 'Average'):
        #    tables = db['Averages']
        #else:
    #    tables = db[CurrencyPair]
    #    tablecount = tables.count()
    #    for row in tables:
    #        random = 0
#lastprice = table['price']
    #    lastprice = row.iloc[tablecount]['price']
    #    return lastprice
     
    def check_db_for_last_price(self, DB, OrderType, CurrencyPair):
        #print "Finding Last DB Price for", CurrencyPair
        if(DB == "Trade"):
            db = dataset.connect('sqlite:///Trade.sql')
        if(DB == "Exchange"):
            db = dataset.connect('sqlite:///Exchange.sql')
        #if (OrderType == 'Average'):
        #    tables = db['Averages']
        #else:
        tables = db[CurrencyPair]
        tablecount = tables.count()
        rowid = 0
        for roww in tables:
            #rowid = row['id']
            rowid = rowid+1
            if(rowid == tablecount):
                #otype = row['ordertype']   
                lastprice = roww['price']
        return lastprice

	 
    def check_most_active_coin(self, polltime):
        db = dataset.connect('sqlite:///Exchange.sql')
        tables = db['Averages']
        tablecount = tables.count()
        amount=0; prevamt=0; count=0; mostactive=0; dbtime=0; starttime = time.time()
        timediff=starttime-polltime
        for row in tables:
            dbtime = row['datetime']
            #print "Database Time:", dbtime, "Start Time:", starttime, "Time Different:", timediff, "Polltime", polltime
            if(dbtime >= timediff):
                amount = row['amount']
                count = count + 1
            
                if(count == 1):
                    #print "Count:", count
                    amount = row['amount']
                    prevamt = amount
                    mostactive = row['currencypair']
                    #print "Previous Amount:", prevamt
                    #print "DB Amount:", amount

                if(amount > prevamt):
                    mostactive = row['currencypair']
                    prevamt = amount
                #if(mostactive == 0):
                #mostactive = 0
        return [mostactive, prevamt]


    #def percentage(self, one, two):
    #    if(one > two):
    #        diff=one-two
    #    else
    #        diff=two-one            
    #    return () / 100.0

#def percentage(part, whole):
#  return 100 * float(part)/float(whole)
