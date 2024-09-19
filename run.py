#!/usr/bin/env python3
import asyncio
import logging
import math
import os
import re

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from metaapi_cloud_sdk import MetaApi
from prettytable import PrettyTable
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler, CallbackContext

# MetaAPI Credentials
API_KEY = os.environ.get("API_KEY")
ACCOUNT_ID = os.environ.get("ACCOUNT_ID")

# Telegram Credentials
TOKEN = os.environ.get("TOKEN")
TELEGRAM_USER = os.environ.get("TELEGRAM_USER")

# Heroku Credentials
APP_URL = os.environ.get("APP_URL")

# Port number for Telegram bot web hook
PORT = int(os.environ.get('PORT', '8443'))


# Enables logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# possibles states for conversation handler
CALCULATE, TRADE, DECISION = range(3)

# allowed FX symbols
SYMBOLS = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'BTCUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD', 'NOW', 'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'XAGUSD', 'XAUUSD']

# RISK FACTOR
RISK_FACTOR = float(os.environ.get("RISK_FACTOR"))


# Helper Functions
def ParseSignal(update: Update, context: CallbackContext) -> dict:
    """Starts process of parsing signal and entering trade on MetaTrader account.

    Arguments:
        signal: trading signal

    Returns:
        a dictionary that contains trade signal information
    """

    signal = update.effective_message.text
    trade = {}
    broker = 'vantage'
    firstTP = []
    secondTP = []
    stoploss = []
    Entryposition = -1
    firstentry = False
    OrderLater = False
    OrderTypeExists = False
    SymbolExists = False
    
    #for line in signal.splitlines():
     #   if len(line.strip()) == 0 :
      #      continue
            
        #update.effective_message.reply_text(line)
    #update.effective_message.reply_text("check what Order type")
    #update.effective_message.reply_text(signal)
    
    #check what Order type:
    if('Buy Limit'.lower() in signal.lower() or 'Buylimit'.lower() in signal.lower()):
        trade['OrderType'] = 'Buy Limit'
        OrderLater = True
        OrderTypeExists = True
    elif('Sell Limit'.lower() in signal.lower() or 'Selllimit'.lower() in signal.lower()):
        trade['OrderType'] = 'Sell Limit'
        OrderLater = True
        OrderTypeExists = True
    elif('Buy Stop'.lower() in signal.lower() or 'Buystop'.lower() in signal.lower()):
        trade['OrderType'] = 'Buy Stop'
        OrderLater = True
        OrderTypeExists = True
    elif('Sell Stop'.lower() in signal.lower() or 'Sellstop'.lower() in signal.lower()):
        trade['OrderType'] = 'Sell Stop'
        OrderLater = True
        OrderTypeExists = True
    elif('Buy'.lower() in signal.lower()):
        trade['OrderType'] = 'Buy'
        trade['Entry'] = 'NOW'
        update.effective_message.reply_text("in Buy")
        OrderTypeExists = True
    elif('Sell'.lower() in signal.lower()):
        trade['OrderType'] = 'Sell'
        trade['Entry'] = 'NOW'
        OrderTypeExists = True
    else:
        update.effective_message.reply_text("no signal found")
        
    update.effective_message.reply_text(trade['OrderType'])
    
    #check which Symbol:
    if('Dow'.lower() in signal.lower()):
        Entryposition = signal.lower().find('dow')
        OrderTypeExists = True
    elif('US30'.lower() in signal.lower()):
        Entryposition = signal.lower().find('us30')
        OrderTypeExists = True
    elif('US 30'.lower() in signal.lower()):
        Entryposition = signal.lower().find('us 30')
        OrderTypeExists = True
    else: 
        Entryposition = -1        
    if(Entryposition != -1):
        if(broker == 'vantage'):
            trade['Symbol'] = 'DJ30'
            trade['PositionSize'] = 0.4
            SymbolExists = True
            #update.effective_message.reply_text("in DJ30")
        #find Dow Entry
        firstentry = re.findall('\d+\.\d+|\d+', signal[Entryposition:])[0]
        if(OrderLater == True):
            trade['Entry'] = float(firstentry)
        Entryposition = -1

    elif('Nasdaq'.lower() in signal.lower()):
        Entryposition = signal.lower().find('nasdaq')
    elif('Nas'.lower() in signal.lower()):
        Entryposition = signal.lower().find('nas')
    elif('US100'.lower() in signal.lower()):
        Entryposition = signal.lower().find('us100')
    elif('US 100'.lower() in signal.lower()):
        Entryposition = signal.lower().find('us 100')
    else: 
        Entryposition = -1
    if(Entryposition != -1):
        if(broker == 'vantage'):
            trade['Symbol'] = 'NAS100'
            trade['PositionSize'] = 0.4
            SymbolExists = True
        #find Nas Entry
        firstentry = re.findall('\d+\.\d+|\d+', signal[Entryposition:])[0]
        if(OrderLater == True):
            trade['Entry'] = float(firstentry)
        Entryposition = -1

    elif('BTCUSD'.lower() in signal.lower()):
        Entryposition = signal.lower().find('btcusd')
    else: 
        Entryposition = -1
    if(Entryposition != -1):
        if(broker == 'vantage'):
            trade['Symbol'] = 'BTCUSD'
            trade['PositionSize'] = 0.1
            SymbolExists = True
        firstentry = re.findall('\d+\.\d+|\d+', signal[Entryposition:])[0]
        if(OrderLater == True):
            trade['Entry'] = float(firstentry)
        Entryposition = -1
        
    #elif('Gold'.lower() or 'XAUUSD'.lower() or 'US100'.lower() or 'US 100'.lower() in signal.lower()):
    #    if(broker == 'vantage'):
    #        trade['Symbol'] = 'NAS100'
    if(SymbolExists != True):
        update.effective_message.reply_text("no known symbol found")

    update.effective_message.reply_text("Entry:")
    update.effective_message.reply_text(firstentry)
    
    #check TP:
    if(signal.lower().find('tp1') != -1):
        TPposition = signal.lower().find('tp1')
        firstTP = re.findall('\d+\.\d+|\d+', signal[TPposition:])[1]
        firstTPpos = signal.lower().find(firstTP)
        textafterfirstTP = signal[firstTPpos:].splitlines()[0]
        if('pips'.lower() in textafterfirstTP.lower()):
            firstTP = firstTP
        else:
            firstTP = float(firstTP) - float(firstentry)
        #update.effective_message.reply_text("line after TP number")
        #update.effective_message.reply_text(firstTPpips)
    elif(signal.lower().find('tp 1') != -1):
        TPposition = signal.lower().find('tp 1')
        firstTP = re.findall('\d+\.\d+|\d+', signal[TPposition:])[1]
        firstTPpos = signal.lower().find(firstTP)
        textafterfirstTP = signal[firstTPpos:].splitlines()[0]
        if('pips'.lower() in textafterfirstTP.lower()):
            firstTP = firstTP/10.
        else:
            firstTP = float(firstTP) - float(firstentry)
    else: 
        TPposition = signal.lower().find('tp')  
        firstTP = re.findall('\d+\.\d+|\d+', signal[TPposition:])[0]
        firstTPpos = signal.lower().find(firstTP)
        textafterfirstTP = signal[firstTPpos:].splitlines()[0]
        if('pips'.lower() in textafterfirstTP.lower()):
            firstTP = firstTP/10.
        else:
            firstTP = float(firstTP) - float(firstentry)
    if(TPposition == -1):
        update.effective_message.reply_text("no TP found, TP +60 used")
        firstTP = 60
    else:
        update.effective_message.reply_text("TP1 = ")
        update.effective_message.reply_text(firstTP)
        trade['TP1'] = firstTP
        
    #check second TP:
        if(signal.lower().find('tp2') != -1):
            TPposition2 = signal.lower().find('tp2')
            secondTP = re.findall('\d+\.\d+|\d+', signal[TPposition2:])[1]
            #secondTPpos = signal.lower().find(secondTP)
            textaftersecondTP = signal[TPposition2:].splitlines()[0]
            update.effective_message.reply_text("textaftersecondTP 1:")
            update.effective_message.reply_text(textaftersecondTP)
            if('pips'.lower() in textaftersecondTP.lower()):
                secondTP = secondTP/10.
            else:
                secondTP = float(secondTP) - float(firstentry)
                
        elif(signal.lower().find('tp 2') != -1):
            TPposition2 = signal.lower().find('tp 2')
            secondTP = re.findall('\d+\.\d+|\d+', signal[TPposition2:])[1]
            #secondTPpos = signal.lower().find(secondTP)
            textaftersecondTP = signal[TPposition2:].splitlines()[0]
            update.effective_message.reply_text("textaftersecondTP 2:")
            update.effective_message.reply_text(textaftersecondTP)
            if('pips'.lower() in textaftersecondTP.lower()):
                secondTP = secondTP/10.
            else:
                secondTP = float(secondTP) - float(firstentry)
        else: 
            TPposition2 = signal.lower()[TPposition:].find('tp')
            update.effective_message.reply_text(TPposition)
            update.effective_message.reply_text(TPposition2)
            secondTP = re.findall('\d+\.\d+|\d+', signal[TPposition2:])[0]
            #secondTPpos = signal.lower().find(secondTP)
            textaftersecondTP = signal[TPposition2:].splitlines()[0]
            update.effective_message.reply_text("textaftersecondTP 3:")
            update.effective_message.reply_text(textaftersecondTP)
            if('pips'.lower() in textaftersecondTP.lower()):
                secondTP = secondTP/10.
            else:
                update.effective_message.reply_text(secondTP)
                update.effective_message.reply_text(firstentry)
                secondTP = float(secondTP) - float(firstentry)
                
        if(TPposition2 != -1):
            update.effective_message.reply_text("TP2 = ")
            update.effective_message.reply_text(secondTP)
            trade['TP2'] = secondTP
        else: 
            update.effective_message.reply_text("no TP2 defined, use 1000 pips")
            secondTP = 100
            trade['TP2'] = secondTP
            
        
    #check SL:
    SLposition = signal.lower().find('sl')
    #update.effective_message.reply_text(SLposition)
    if(SLposition == -1):
        update.effective_message.reply_text("No SL, use 800 pips")
        trade['StopLoss'] = 80.
    else:
        stoploss = re.findall('\d+\.\d+|\d+', signal[SLposition:])[0]
        textafterSL = signal[SLposition:].splitlines()[0]
        if('pips'.lower() in textafterSL.lower()):
            stoploss = stoploss/10.
        else:
            stoploss = float(firstentry) - float(stoploss)
        update.effective_message.reply_text("SL = ")
        update.effective_message.reply_text(stoploss)
        trade['StopLoss'] = stoploss
    
    #update.effective_message.reply_text("You entered that message:")
    update.effective_message.reply_text(trade)

    #check, if everthing is there
    if(OrderTypeExists != True or SymbolExists != True):
        trade = {}

    return trade

def GetTradeInformation(update: Update, trade: dict, balance: float) -> None:
    """Calculates information from given trade including stop loss and take profit in pips, posiition size, and potential loss/profit.

    Arguments:
        update: update from Telegram
        trade: dictionary that stores trade information
        balance: current balance of the MetaTrader account
    """
    update.effective_message.reply_text("in GettradeInfo")
    # calculates the stop loss in pips
    if(trade['Symbol'] == 'XAUUSD'):
        multiplier = 0.1

    elif(trade['Symbol'] == 'XAGUSD'):
        multiplier = 0.001

    elif(trade['Symbol'] == 'BTCUSD'):
        multiplier = 1

    else:
        multiplier = 1

    # calculates the stop loss in pips
    stopLossPips = abs(round((trade['StopLoss'] - trade['Entry']) / multiplier))

    # calculates the position size using stop loss and RISK FACTOR
    # trade['PositionSize'] = math.floor(((balance * trade['RiskFactor']) / stopLossPips) / 10 * 100) / 100
    #trade['PositionSize'] = 0.5 # lot size is in if loop of element


    # calculates the take profit(s) in pips
    takeProfitPips = []
    #for takeProfit in trade['TP']:
    takeProfitPips.append(abs(round((trade['TP1'] - trade['Entry']) / multiplier)))
    
    # creates table with trade information
    table = CreateTable(trade, balance, stopLossPips, takeProfitPips)
    
    # sends user trade information and calculated risk
    update.effective_message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

    return

def CreateTable(trade: dict, balance: float, stopLossPips: int, takeProfitPips: int) -> PrettyTable:
    """Creates PrettyTable object to display trade information to user.

    Arguments:
        trade: dictionary that stores trade information
        balance: current balance of the MetaTrader account
        stopLossPips: the difference in pips from stop loss price to entry price

    Returns:
        a Pretty Table object that contains trade information
    """

    # creates prettytable object
    table = PrettyTable()
    
    table.title = "Trade Information"
    table.field_names = ["Key", "Value"]
    table.align["Key"] = "l"  
    table.align["Value"] = "l" 

    table.add_row([trade["OrderType"] , trade["Symbol"]])
    table.add_row(['Entry\n', trade['Entry']])

    table.add_row(['Stop Loss', '{} pips'.format(stopLossPips)])

    for count, takeProfit in enumerate(takeProfitPips):
        table.add_row([f'TP {count + 1}', f'{takeProfit} pips'])

    #table.add_row(['\nRisk Factor', '\n{:,.0f} %'.format(trade['RiskFactor'] * 100)])
    table.add_row(['Position Size', trade['PositionSize']])
    
    table.add_row(['\nCurrent Balance', '\n$ {:,.2f}'.format(balance)])
    #table.add_row(['Potential Loss', '$ {:,.2f}'.format(round((trade['PositionSize'] * 10) * stopLossPips, 2))])
    table.add_row(['Potential Loss', '$ {:,.2f}'.format(round(trade['PositionSize'] * stopLossPips, 2))])
    # total potential profit from trade
    totalProfit = 0

    for count, takeProfit in enumerate(takeProfitPips):
        #profit = round((trade['PositionSize'] * 10 * (1 / len(takeProfitPips))) * takeProfit, 2)
        profit = round(trade['PositionSize'] * takeProfit, 2)
        table.add_row([f'TP {count + 1} Profit', '$ {:,.2f}'.format(profit)])
        
        # sums potential profit from each take profit target
        totalProfit += profit

    table.add_row(['\nTotal Profit', '\n$ {:,.2f}'.format(totalProfit)])

    return table

async def ConnectMetaTrader(update: Update, trade: dict, enterTrade: bool):
    """Attempts connection to MetaAPI and MetaTrader to place trade.

    Arguments:
        update: update from Telegram
        trade: dictionary that stores trade information

    Returns:
        A coroutine that confirms that the connection to MetaAPI/MetaTrader and trade placement were successful
    """

    # creates connection to MetaAPI
    api = MetaApi(API_KEY)
    
    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        initial_state = account.state
        deployed_states = ['DEPLOYING', 'DEPLOYED']

        if initial_state not in deployed_states:
            #  wait until account is deployed and connected to broker
            logger.info('Deploying account')
            await account.deploy()

        logger.info('Waiting for API server to connect to broker ...')
        await account.wait_connected()

        # connect to MetaApi API
        connection = account.get_rpc_connection()
        await connection.connect()

        # wait until terminal state synchronized to the local state
        logger.info('Waiting for SDK to synchronize to terminal state ...')
        await connection.wait_synchronized()

        # obtains account information from MetaTrader server
        account_information = await connection.get_account_information()

        update.effective_message.reply_text("Successfully connected to MetaTrader!\nCalculating trade risk ... 🤔")
        update.effective_message.reply_text("trade['Entry']:")
        update.effective_message.reply_text(trade['Entry'])
        # checks if the order is a market execution to get the current price of symbol
        if(trade['Entry'] == 'NOW'):
            price = await connection.get_symbol_price(symbol=trade['Symbol'])
            symspec = await connection.get_symbol_specification(symbol=trade['Symbol'])
            #print(price)
            #print(symspec)
            # uses bid price if the order type is a buy
            if(trade['OrderType'] == 'Buy'):
                trade['Entry'] = float(price['bid'])

            # uses ask price if the order type is a sell
            if(trade['OrderType'] == 'Sell'):
                trade['Entry'] = float(price['ask'])

        update.effective_message.reply_text("GetTradeInformation and enter trade?")
        # produces a table with trade information
        GetTradeInformation(update, trade, account_information['balance'])
        
        update.effective_message.reply_text(enterTrade)
        # checks if the user has indicated to enter trade
        if(enterTrade == True):

            # enters trade on to MetaTrader account
            update.effective_message.reply_text("Entering trade on MetaTrader Account ... 👨🏾‍💻")

            try:
                trade['TP1'] = float(trade['Entry']) + trade['TP1']
                trade['TP2'] = float(trade['Entry']) + trade['TP2']
                trade['StopLoss'] = float(trade['Entry']) - trade['StopLoss']
                        
                # executes buy market execution order
                if(trade['OrderType'] == 'Buy'):
                    result = await connection.create_market_buy_order(trade['Symbol'], trade['PositionSize'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_market_buy_order(trade['Symbol'], trade['PositionSize'], trade['StopLoss'], trade['TP2'])
                    #for takeProfit in trade['TP']:
                    #    result = await connection.create_market_buy_order(trade['Symbol'], trade['PositionSize'], trade['StopLoss'], takeProfit)

                # executes buy limit order
                elif(trade['OrderType'] == 'Buy Limit'):
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP2'])
                # executes buy stop order
                elif(trade['OrderType'] == 'Buy Stop'):
                    result = await connection.create_stop_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP2'])
                # executes sell market execution order
                elif(trade['OrderType'] == 'Sell'):
                    result = await connection.create_market_sell_order(trade['Symbol'], trade['PositionSize'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP2'])
                # executes sell limit order
                elif(trade['OrderType'] == 'Sell Limit'):
                    result = await connection.create_limit_sell_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP2'])
                # executes sell stop order
                elif(trade['OrderType'] == 'Sell Stop'):
                    result = await connection.create_stop_sell_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP1'])
                    result = await connection.create_limit_buy_order(trade['Symbol'], trade['PositionSize'], trade['Entry'], trade['StopLoss'], trade['TP2'])
                # sends success message to user
                update.effective_message.reply_text("Trade entered successfully! 💰")
                
                # prints success message to console
                logger.info('\nTrade entered successfully!')
                logger.info('Result Code: {}\n'.format(result['stringCode']))
            
            except Exception as error:
                logger.info(f"\nTrade failed with error: {error}\n")
                update.effective_message.reply_text(f"There was an issue 😕\n\nError Message:\n{error}")
    
    except Exception as error:
        logger.error(f'Error: {error}')
        update.effective_message.reply_text(f"There was an issue with the connection 😕\n\nError Message:\n{error}")
    
    return

def SendTrade(update: Update, context: CallbackContext) -> None:
    """Parses trade and sends to MetaTrader account.   
    
    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """
    update.effective_message.reply_text("in SendTrade")
    #update.effective_message.reply_text(context.user_data['trade'])
    # checks if the trade has already been parsed or not
    if(context.user_data['trade'] == None):
        update.effective_message.reply_text("trade is None")
        try: 
            # parses signal from Telegram message
            update.effective_message.reply_text("try parsing")
            trade = ParseSignal(update, context)
            
            # checks if there was an issue with parsing the trade
            #if(not(trade)):
            #    raise Exception('Invalid Trade')

            # sets the user context trade equal to the parsed trade
            context.user_data['trade'] = trade
            update.effective_message.reply_text("Trade Successfully Parsed! 🥳\nConnecting to MetaTrader ... \n(May take a while) ⏰")
        
        except Exception as error:
            logger.error(f'Error: {error}')
            errorMessage = f"There was an error parsing this trade 😕\n\nError: {error}\n\nPlease re-enter trade with this format:\n\nBUY/SELL SYMBOL\nEntry \nSL \nTP \n\nOr use the /cancel to command to cancel this action."
            update.effective_message.reply_text(errorMessage)

            # returns to TRADE state to reattempt trade parsing
            return TRADE
    else:
        update.effective_message.reply_text("context.user_data['trade'] is not None")
    
    # attempts connection to MetaTrader and places trade
    asyncio.run(ConnectMetaTrader(update, context.user_data['trade'], True))
    
    # removes trade from user context data
    context.user_data['trade'] = None

    return

# Handler Functions
def PlaceTrade(update: Update, context: CallbackContext) -> int:
    """Parses trade and places on MetaTrader account.   
    
    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    # checks if the trade has already been parsed or not
    if(context.user_data['trade'] == None):

        try: 
            # parses signal from Telegram message
            trade = ParseSignal(update, context)
            update.effective_message.reply_text(trade)
            # checks if there was an issue with parsing the trade
            #if(not(trade)):
             #   raise Exception('Invalid Trade')

            # sets the user context trade equal to the parsed trade
            context.user_data['trade'] = trade
            update.effective_message.reply_text("Trade Successfully Parsed! 🥳\nConnecting to MetaTrader ... \n(May take a while) ⏰")
        
        except Exception as error:
            logger.error(f'Error: {error}')
            errorMessage = f"There was an error parsing this trade 😕\n\nError: {error}\n\nPlease re-enter trade with this format:\n\nBUY/SELL SYMBOL\nEntry \nSL \nTP \n\nOr use the /cancel to command to cancel this action."
            update.effective_message.reply_text(errorMessage)

            # returns to TRADE state to reattempt trade parsing
            return TRADE
    
    # attempts connection to MetaTrader and places trade
    asyncio.run(ConnectMetaTrader(update, context.user_data['trade'], True))
    
    # removes trade from user context data
    context.user_data['trade'] = None

    return ConversationHandler.END

def CalculateTrade(update: Update, context: CallbackContext) -> int:
    """Parses trade and places on MetaTrader account.   
    
    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    # checks if the trade has already been parsed or not
    if(context.user_data['trade'] == None):

        try: 
            # parses signal from Telegram message
            trade = ParseSignal(update, context)
            
            # checks if there was an issue with parsing the trade
            if(not(trade)):
                raise Exception('Invalid Trade')

            # sets the user context trade equal to the parsed trade
            context.user_data['trade'] = trade
            update.effective_message.reply_text("Trade Successfully Parsed! 🥳\nConnecting to MetaTrader ... (May take a while) ⏰")
        
        except Exception as error:
            logger.error(f'Error: {error}')
            errorMessage = f"There was an error parsing this trade 😕\n\nError: {error}\n\nPlease re-enter trade with this format:\n\nBUY/SELL SYMBOL\nEntry \nSL \nTP \n\nOr use the /cancel to command to cancel this action."
            update.effective_message.reply_text(errorMessage)

            # returns to CALCULATE to reattempt trade parsing
            return CALCULATE
    
    # attempts connection to MetaTrader and calculates trade information
    asyncio.run(ConnectMetaTrader(update, context.user_data['trade'], False))

    # asks if user if they would like to enter or decline trade
    update.effective_message.reply_text("Would you like to enter this trade?\nTo enter, select: /yes\nTo decline, select: /no")

    return DECISION

def unknown_command(update: Update, context: CallbackContext) -> None:
    """Checks if the user is authorized to use this bot or shares to use /help command for instructions.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """
    if(not(update.effective_message.chat.username == TELEGRAM_USER)):
        update.effective_message.reply_text("You are not authorized to use this bot! 🙅🏽‍♂️")
        return  

    update.effective_message.reply_text("in unknown")
    context.user_data['trade'] = None
    SendTrade(update, context)
    update.effective_message.reply_text("trade placed")
    
    return


# Command Handlers
def welcome(update: Update, context: CallbackContext) -> None:
    """Sends welcome message to user.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    welcome_message = "Welcome to the FX Signal Copier Telegram Bot! 💻💸\n\nYou can use this bot to enter trades directly from Telegram and get a detailed look at your risk to reward ratio with profit, loss, and calculated lot size. You are able to change specific settings such as allowed symbols, risk factor, and more from your personalized Python script and environment variables.\n\nUse the /help command to view instructions and example trades."
    
    # sends messages to user
    update.effective_message.reply_text(welcome_message)

    return

def help(update: Update, context: CallbackContext) -> None:
    """Sends a help message when the command /help is issued

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    help_message = "This bot is used to automatically enter trades onto your MetaTrader account directly from Telegram. To begin, ensure that you are authorized to use this bot by adjusting your Python script or environment variables.\n\nThis bot supports all trade order types (Market Execution, Limit, and Stop)\n\nAfter an extended period away from the bot, please be sure to re-enter the start command to restart the connection to your MetaTrader account."
    commands = "List of commands:\n/start : displays welcome message\n/help : displays list of commands and example trades\n/trade : takes in user inputted trade for parsing and placement\n/calculate : calculates trade information for a user inputted trade"
    trade_example = "Example Trades 💴:\n\n"
    market_execution_example = "Market Execution:\nBUY GBPUSD\nEntry NOW\nSL 1.14336\nTP 1.28930\nTP 1.29845\n\n"
    limit_example = "Limit Execution:\nBUY LIMIT GBPUSD\nEntry 1.14480\nSL 1.14336\nTP 1.28930\n\n"
    note = "You are able to enter up to two take profits. If two are entered, both trades will use half of the position size, and one will use TP1 while the other uses TP2.\n\nNote: Use 'NOW' as the entry to enter a market execution trade."

    # sends messages to user
    update.effective_message.reply_text(help_message)
    update.effective_message.reply_text(commands)
    update.effective_message.reply_text(trade_example + market_execution_example + limit_example + note)

    return

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation.   
    
    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    update.effective_message.reply_text("Command has been canceled.")

    # removes trade from user context data
    context.user_data['trade'] = None

    return ConversationHandler.END

def error(update: Update, context: CallbackContext) -> None:
    """Logs Errors caused by updates.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """

    logger.warning('Update "%s" caused error "%s"', update, context.error)

    return

def Trade_Command(update: Update, context: CallbackContext) -> int:
    """Asks user to enter the trade they would like to place.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """
    if(not(update.effective_message.chat.username == TELEGRAM_USER)):
        update.effective_message.reply_text("You are not authorized to use this bot! 🙅🏽‍♂️")
        return ConversationHandler.END
    
    # initializes the user's trade as empty prior to input and parsing
    context.user_data['trade'] = None
    
    # asks user to enter the trade
    update.effective_message.reply_text("Please enter the trade that you would like to place.")

    return TRADE

def Calculation_Command(update: Update, context: CallbackContext) -> int:
    """Asks user to enter the trade they would like to calculate trade information for.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """
    if(not(update.effective_message.chat.username == TELEGRAM_USER)):
        update.effective_message.reply_text("You are not authorized to use this bot! 🙅🏽‍♂️")
        return ConversationHandler.END

    # initializes the user's trade as empty prior to input and parsing
    context.user_data['trade'] = None

    # asks user to enter the trade
    update.effective_message.reply_text("Please enter the trade that you would like to calculate.")

    return CALCULATE


def main() -> None:
    """Runs the Telegram bot."""

    updater = Updater(TOKEN, use_context=True)

    # get the dispatcher to register handlers
    dp = updater.dispatcher

    # message handler
    dp.add_handler(CommandHandler("start", welcome))

    # help command handler
    dp.add_handler(CommandHandler("help", help))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("trade", Trade_Command), CommandHandler("calculate", Calculation_Command)],
        states={
            TRADE: [MessageHandler(Filters.text & ~Filters.command, PlaceTrade)],
            CALCULATE: [MessageHandler(Filters.text & ~Filters.command, CalculateTrade)],
            DECISION: [CommandHandler("yes", PlaceTrade), CommandHandler("no", cancel)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # conversation handler for entering trade or calculating trade information
    dp.add_handler(conv_handler)

    # message handler for all messages that are not included in conversation handler
    dp.add_handler(MessageHandler(Filters.text, unknown_command))
    #dp.add_handler(MessageHandler(Filters.text, SendTrade))
    
    # log all errors
    dp.add_error_handler(error)
    
    # listens for incoming updates from Telegram
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=APP_URL + TOKEN)
    updater.idle()

    return


if __name__ == '__main__':
    main()
