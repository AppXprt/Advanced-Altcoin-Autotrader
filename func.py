#!/usr/bin/python
#-*- coding: ASCII -*-
import os
import sys
import time
import math
import dataset
import numpy
import exchange_api

from poloniex import Poloniex
from decimal import Decimal

global LogFile, ErrFile, Default

LogFile = "FaMLoG-"+time.strftime("%Y%m%d-%H%M%S")+".txt"
ErrFile = "FaMLoG-Error.txt"
Default = sys.stdout    
StartTime = time

Polo = Poloniex("8Z96WF3Q-CUV390KL-59AZ31CQ-GZOIUULT", "bbb8edd76c9bb47585d26316e17015116a138cea7a7218d87f99388ecfd6c57d5c5125a98387ad53263dd3c9152d258fb4a479f2f97275fbbddc22f390d2323f")
TimeSpan = 150

def get_group_balances(Balances, Currencies):
    for Currency in Currencies:
        balances = Get_Balance(Balances, Currency)
    return balances
   
def Get_Info_From_History(CurrencyPair, ExTradeHistory, ExTradeHistAmount):
	THInfoDict = {}
	THInfoList = []
	THPair = CurrencyPair
	for ExTrade in ExTradeHistory:        
		THRate = ExTrade[u'rate']
		THAmt = ExTrade[u'amount']
		THType = ExTrade[u'type']
		THDate = time.mktime(time.strptime(ExTrade[u'date'], "%Y-%m-%d %H:%M:%S"))
		#THDirection = Currency_Trending_Up_Down_DB('Exchange', CurrencyPair, TimeSpan)
		THDict = {'currencypair': CurrencyPair, 'rate': THRate, 'amount': THAmt, 'type': THType, 'date': THDate} 
		THInfoList.append(THDict)
	return THInfoList

def Get_Prices_From_History(ExTradeHistory):
    THRateList = [] 
    for ExTrade in ExTradeHistory:
        THRate = ExTrade['rate']
        THRateList.append(THRate)  
    return THRateList
	
def checkEqual2(iterator):
    return len(set(iterator)) <= 1 

#def Check_Last_Trade_price(self, OrderType, CurrencyPair):
#    TradeDB = dataset.connect('sqlite:///Exchange.db') 
#    for Order in db[OrderType]:
#        print(OrderType['price'])

def Insert_Order_to_DB(Database, OrderType, InsertPair, Price, Amount, DateTimeof, Status, OrderID):
    #Order DB's are Orders_Complete, #Orders_Canceled, #Orders_Open
    print "InsertPair:", InsertPair
    DB='sqlite:///'+Database+'.db'
    OrderDB = dataset.connect(DB)
    table = OrderDB[InsertPair]
    print "Inserting into "+DB+" DB for", InsertPair, "..."
    table.insert(dict(ordertype=OrderType, currencypair=InsertPair, price=Price, amount=Amount, datetime=DateTimeof, status=Status, orderid=OrderID))

def Insert_Trade_to_DB(OrderType, CurrencyPair, Price, Amount, DateTimeof, Status):
	TradeDB = dataset.connect('sqlite:///Trade.db')
	table = TradeDB[OrderType]
	table.insert(dict(ordertype=OrderType, currencypair=CurrencyPair, price=Price, amount=Amount, datetime=DateTimeof, status=Status))
  
def Insert_ExTrade_to_DB(OrderType, CurrencyPair, Price, Amount, DateTimeof):
    ExchangeDB = dataset.connect('sqlite:///Exchange.db')
    if (OrderType == 'Average'):
        table = ExchangeDB['Averages']
    else:
        table = ExchangeDB[CurrencyPair]
    table.insert(dict(ordertype=OrderType, currencypair=CurrencyPair, price=Price, amount=Amount, datetime=DateTimeof))
   
def Insert_Price_Array_to_DB(ExcInfo):
    db = 'sqlite:///Exchange.db'
    DB = dataset.connect(db)
    table = DB['Exchange']
    for Info in ExcInfo:
        table.insert(dict(ordertype=Info['type'], currencypair=Info['currencypair'], price=Info['rate'], amount=Info['amount'], datetime=Info['date']))
        #table.insert(dict(ordertype=OrderType, currencypair=CurrencyPair, price=Price, amount=Amount, datetime=DateTimeof))
    print "Prices for", Info['currencypair'], "written successfully!"     
           

def Remove_Order_from_DB(Database, CurrencyPair, Info):
    db ='sqlite:///'+Database+'.db'
    print "Connecting to", Database
    DB = dataset.connect(db)
    table = DB[CurrencyPair]
    print "Looking up", Info['orderNumber'], "in", CurrencyPair
    remove = table.delete(orderid=Info['orderNumber'])
    return remove

    #{u'orderNumber': u'120028128840', u'margin': 0, u'amount': u'1.51578227', u'rate': u'0.00016213', u'date': u'2018-02-03 13:59:53', u'total': u'0.00024575', u'type': u'sell', u'startingAmount': u'1.51578227'}
    








#drop_column(name)[source]
#Drop the column name.

#table.drop_column('created_at')
#find(*_clauses, **kwargs)[source]
#Perform a simple search on the table.

#Simply pass keyword arguments as filter.

#results = table.find(country='France')



def check_db_for_last_avg(DB, CurrencyPair):
   #print "Finding Last DB Average for", CurrencyPair
   if(DB == "Trade"):
	   db = dataset.connect('sqlite:///Trade.db')
   if(DB == "Exchange"):
	   db = dataset.connect('sqlite:///Exchange.db')
   if(db[CurrencyPair]):
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
   else:
       return 0
   
def check_db_table_exists_or_create(DB, CurrencyPair):
    
    if(DB == "Trade"):
        db = dataset.connect('sqlite:///Trade.db')
    if(DB == "Exchange"):
        db = dataset.connect('sqlite:///Exchange.db')
        
    table = db[CurrencyPair]
    if(db[CurrencyPair]):
        return table   
    else:
        table.insert(dict(ordertype='', amount=0, datetime=0))
    return table
     
def check_db_for_last_price(DB, CurrencyPair):
    if(DB == "Trade"):
        db = dataset.connect('sqlite:///Trade.db')
    if(DB == "Trends"):
        db = dataset.connect('sqlite:///Trends.db')
    if(DB == "Exchange"):
        db = dataset.connect('sqlite:///Exchange.db')

    lastprice = 0

    if(db[CurrencyPair]):
   
        if(db[CurrencyPair]):
            tables = db[CurrencyPair]
            tablecount = tables.count()
            rowid = 0
            for row in tables:
	            rowid = rowid+1
	            if(rowid == tablecount):
		            #otype = row['ordertype']   
		            lastprice = row['price']
    return lastprice


def check_most_active_coin(polltime):
    db = dataset.connect('sqlite:///Exchange.db')
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

def Convert_Amt_USDT(Amt, CurrencyPair, Market):
    if(Market != "USDT"):
        ExLastTrade = 0
        #CurrencyPair = "USDT_"+str(alt)
        CurrencyPair = "USDT_" + Market
        ExTradeHistory = Get_Trade_History(CurrencyPair, 600)
        if ExTradeHistory:
            ExTradeInfo = Get_Info_From_History(CurrencyPair, ExTradeHistory, 1)    
            ExLastTrade = ExTradeInfo[0]['rate']
            print "Conversion Rate:", ExLastTrade
            conversion = float(ExLastTrade) * float(Amt)
    else:
        CurrencyPair = CurrencyPair.replace(Market, 'USDT')
        ExTradeHistory = Get_Trade_History(CurrencyPair, 600)
        if ExTradeHistory:
            ExTradeInfo = Get_Info_From_History(CurrencyPair, ExTradeHistory, 1)    
            ExLastTrade = ExTradeInfo[0]['rate']
            #if(ExLastTrade): print "ExLastTrade USDT:", ExLastTrade
            print "Conversion Rate:", ExLastTrade
            conversion = float(Amt)
    return conversion

def Convert_Base_to_USDT(CurrencyPair, Market):

    ExLastTrade = 0
    
    if(Market != "USDT"):
             
        CurrencyPair = "USDT_" + Market
        ExTradeHistory = Get_Trade_History(CurrencyPair, 600)
        if ExTradeHistory:
            ExTradeInfo = Get_Info_From_History(CurrencyPair, ExTradeHistory, 1)    
            ExLastTrade = ExTradeInfo[0]['rate']
            #if(ExLastTrade): print "ExLastTrade USDT:", ExLastTrade
    else:
        CurrencyPair = CurrencyPair.replace(Market, 'USDT')
        ExTradeHistory = Get_Trade_History(CurrencyPair, 600)
        if ExTradeHistory:
            ExTradeInfo = Get_Info_From_History(CurrencyPair, ExTradeHistory, 1)    
            ExLastTrade = ExTradeInfo[0]['rate']
            #if(ExLastTrade): print "ExLastTrade USDT:", ExLastTrade
    return ExLastTrade

def Convert_Alt_to_USDT(CurrencyPair, Market):

    ExLastTrade = 0     

    #CurrencyPair = "USDT_"+str(alt)
    CurrencyPair = CurrencyPair.replace(Market, 'USDT')
    ExTradeHistory = Get_Trade_History(CurrencyPair, 600)
    if ExTradeHistory:
        ExTradeInfo = Get_Info_From_History(CurrencyPair, ExTradeHistory, 1)    
        ExLastTrade = ExTradeInfo[0]['rate']
        #if(ExLastTrade): print "ExLastTrade USDT:", ExLastTrade
    return ExLastTrade
    
def Convert_ExTime(ExTime):
    return time.mktime(time.strptime(ExTime, "%Y-%m-%d %H:%M:%S"))

def Calculate_Time_Limit(Time, Span):
        Limit = int(Time + Span)
        return Limit

def Calculate_TimeSpan(TimeLength):
    TimeSpan = int(time.time()-TimeLength)
    return TimeSpan 
        
def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

    #def returnMarketTradeHist(self, CurrencyPair, TimeLength):
    #       DateTime = int(time.time())
    #       TimeSpan = self.Calculate_TimeSpan(TimeLength)
    #       print color.UNDERLINE+color.BOLD+line+color.END    
    #       print color.UNDERLINE+color.BOLD+CurrencyPair+color.END+":\n", "\nCurrent Time", color.BLUE,DateTime,color.END,"|", TimeLength, "seconds ago:", color.BLUE, TimeSpan,color.END+"\n"
    #       return self.api_query("returnMarketTradeHistory", {'CurrencyPair': CurrencyPair, 'start': TimeSpan, 'end': DateTime})
        
    #LRDDBAVG Difference: 0.0648394216605  or  0.0 %
    
def Calc_Perc(priceone, pricetwo):
    sub = 0
    if((priceone > pricetwo) & (priceone != 0)):
        sub = float(pricetwo/abs(priceone))
    elif((pricetwo > priceone) & (pricetwo != 0)):
        sub = float(priceone/abs(pricetwo))
    perc = float(sub*100.00000000)
    return perc

def Calc_Compare(last_price, latest_price):
    
    compared_price = 0

    if(last_price > latest_price):
        compared_price = (last_price - latest_price)
    if(latest_price > last_price):
        compared_price = (latest_price - last_price)

    return compared_price  

def Calc_Change_Perc(oldprice, newprice):
    sub = 0
    if(oldprice != 0):
        sub = float(abs(newprice - oldprice)/abs(newprice))
    perc = float(sub)

    return perc
        
def Calc_Diff_Perc(oldprice, newprice):
    sub = 0
    if(oldprice != 0):
        sub = float(abs(newprice - oldprice)/((newprice+oldprice)/2))
    perc = float(sub)
    return perc

def Calc_Diff_USDT(priceone, pricetwo):
    if(priceone > pricetwo):
        value = float(priceone - pricetwo)
    else:
        value = float(pricetwo - priceone)
    return value

def Calc_Diff(priceone, pricetwo):
    value = float(abs(pricetwo - priceone))
    return value

def Write_Log(Data):
    FLog = open(LogFile,'a')
    sys.stdout = FLog
    FLog.write(Data)
    FLog.close()
    sys.stdout = Default

def Get_Balance(Balances, MarketID):
    Balance = Balances[MarketID]
    return Balance

def Trim_Balance(Balances, MarketIDs):
    BalanceList=[]
    for MarketID in MarketIDs:
        BalanceList += MarketID+": ",Balances[MarketID]
    return BalanceList

def Return_Exchange_Ticker():
    return Polo.returnTicker()

def Get_Trade_History(CurrencyPair, TimeSpan):
    TimeSpan = Calculate_TimeSpan(TimeSpan)
    ExInfo = Polo.marketTradeHist(CurrencyPair, TimeSpan, int(time.time()))
    return ExInfo
    
def Get_DB_Trends(trending):
    db = dataset.connect('sqlite:///Trends.db')
    Tables_Return = []
    Tables = db[trending]
    for Table in Tables:
        if(Table != 'sqlite_sequence'):
            Tables_Return.append(Table)
    return Tables_Return 

def Get_DB_Markets():
    db = dataset.connect('sqlite:///Markets.db')
    Tables_Return = []
    Tables = db.tables
    for Table in Tables:
        if(Table != 'sqlite_sequence'):
            Tables_Return.append(Table)
    return Tables_Return 
        
def Get_DB_Market_Currency_Alt(Market):
    Markets_Return = []
    db = dataset.connect('sqlite:///Markets.db')
    if(db[Market]):
        Markets_Tables = db[Market]
        for Markets_Table in Markets_Tables:
            Markets_Return.append(Markets_Table['alt'])
        print Markets_Return
  #  else:
  #      print "Market Data Doesn't Exists Yet!"
    return Markets_Return
    
def Average_DB_TimeSpan(DB, CurrencyPair, TimeSpan):
    if(DB == "Trade"):
        db = dataset.connect('sqlite:///Trade.db')
    if(DB == "Exchange"):
        db = dataset.connect('sqlite:///Exchange.db')
    if(db[CurrencyPair]):
        pricearray = []
        tables = db[CurrencyPair]
        tablecount = tables.count()
        price=0; count=0; dbtime=0; starttime = time.time()
        timediff=starttime-TimeSpan
        for row in tables:
            dbtime = row['datetime']
            #print "Database Time:", dbtime, "Start Time:", starttime, "Time Difference:", timediff, "Polltime", polltime
            if(dbtime >= timediff):
                count = count+1
                if(count == 1):
                    pricearray = [price]
                else:
                    price = row['price']
                    pricearray.append(price)

        arrayaverage = numpy.mean(map(float,pricearray))
        return arrayaverage
    else:
        return 0

def Currency_Trending_Up_Down_DB(DB, CurrencyPair, TimeSpan):
    if(DB == "Trade"):
        db = dataset.connect('sqlite:///Trade.db')
    if(DB == "Trend"):
        db = dataset.connect('sqlite:///Trend.db')            
    if(DB == "Exchange"):
        db = dataset.connect('sqlite:///Exchange.db')
    if(db[CurrencyPair]):    
        tables = db[CurrencyPair]
        tablecount = tables.count()
        up=0; down=0; prevprice=0; price=0; count=0; dbtime=0; starttime = time.time()
        timediff=starttime-TimeSpan
        for row in tables:
            dbtime = row['datetime']
            #print "Database Time:", dbtime, "Start Time:", starttime, "Time Difference:", timediff, "Polltime", polltime
            if(dbtime >= timediff):
                count = count+1
                price = row['price']
                if(count == 1):
                    prevprice = price
                if(prevprice > price):
                    up = up + 1
                if(prevprice < price):
                    down = down + 1                    
        if(up > down):
            return "Up"
        else:
            return "Down"          
    else:
        return "NULL"
        
def Currency_Trending_Buy_Sell_DB(DB, CurrencyPair, TimeSpan):
    if(DB == "Trade"):
        db = dataset.connect('sqlite:///Trade.db')
    if(DB == "Trend"):
        db = dataset.connect('sqlite:///Trend.db')                
    if(DB == "Exchange"):
        db = dataset.connect('sqlite:///Exchange.db')
    if(db[CurrencyPair]):    
        tables = db[CurrencyPair]
        tablecount = tables.count()
        buy=0; sell=0; prevtype=0; otype=0; count=0; dbtime=0; starttime = time.time()
        timediff=starttime-TimeSpan
        for row in tables:
            dbtime = row['datetime']
            #print "Database Time:", dbtime, "Start Time:", starttime, "Time Difference:", timediff, "Polltime", polltime
            if(dbtime >= timediff):
                count = count+1
                otype = row['ordertype']
                if otype:
                    prevtype = otype
                    if(prevtype == "buy"):
                        buy = buy + 1
                    if(prevtype == "sell"):
                        sell = sell + 1
        if(buy > sell):
            return "Buy"
        else:
            return "Sell"
    else:
        return "Market Data Doesn't Exists Yet!"


def _FormatFloat(number):
    return ('%.8f' % number).rstrip('0').rstrip('.')

def _Log(message, *args):
    print('%s: %s' % (LogFile, message % args))

def _LoadExchangeConfig(config, target_currencies, source_currencies, exchange_class, *keys):
    if not config.has_section(exchange_class.GetName()):
        return None
    args = {}
    for key in keys:
        if not config.has_option(exchange_class.GetName(), key):
            _Log('Missing %s.%s.', exchange_class.GetName(), key)
            return None
        args[key] = config.get(exchange_class.GetName(), key)

    try:
        exchange = exchange_class(**args)
    except exchange_api.ExchangeException as e:
        _Log('Failed to create %s instance: %s', exchange_class.GetName(), e)
        return None

    currencies = set(exchange.GetCurrencies())

    print "Exchange Currencies",currencies

    if not (currencies & set(target_currencies)):
        _Log('%s does not list any target_currencies, disabling.', exchange.GetName())
        return None
    elif source_currencies and not (currencies & set(source_currencies)):
        _Log('%s does not list any source_currencies, disabling.', exchange.GetName())
        return None
    else:
        _Log('Monitoring %s.', exchange_class.GetName())
        return exchange

	
