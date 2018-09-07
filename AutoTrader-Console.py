import os
import cmd
import func
import json
import readline
import requests
import argparse
import urllib
import urllib2
import urlparse
import ast

from urllib2 import URLError
#from requests import Session
from requests import Session, Request
from poloniex import Poloniex

from pprint import pprint
from decimal import Decimal
Proto = "http://"; Server = "127.0.0.1"; Port = ":8080"; PATH = "/AutoTrader"
URL = ''.join([Proto,Server,Port,PATH])

Polo = Poloniex("", "")

Exchanges = ["Polo"] ### Exchange API Classes from Modules
Exchanges = [Exchange for Exchange in Exchanges if Exchange is not None]

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


class Console(cmd.Cmd):

    def __init__(self):
        print "Using", URL, "As API URL for Console."
        cmd.Cmd.__init__(self)
        self.prompt = "AutoTrader> "
        self.intro  = "Welcome to the AutoTrader console!"  ## defaults to None

    def get(self, URL):
        #print URL
        response = {}
        try:
            response = requests.get(URL).text
            #print response
            return response
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'Failed to reach', URL
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code

    def post(self, URL):
        #print URL
        response = {}
        try:
            response = requests.post(URL).text
            print response
            return response
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'Failed to reach', URL
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
    def do_get(self, URL):
        #print URL
        response = {}
        try:
            response = requests.get(URL).text
            print response
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'Failed to reach', URL
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
    
    def do_post(self, URL):
        #print URL
        response = {}
        try:
            response = requests.post(URL).text
            print response
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'Failed to reach', URL
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
    
    def do_buy(self, args):
        print args
        
    def do_active(self, args):
        response = ""
        URL = Proto+Server+Port+PATH+'?method=active&pass=gen0cide'
        try:
            response = Console.get(self, URL)
            print "Most Active Coin:", response
        except Exception, e:
            print e.__class__, ":", e 
            return e
        

    def do_bal(self, args):
        Arguments = {}
        Response = {}
        Read = {}
        Balances = {}
        JBalances = {}
        Balance = ""
        balprint = ''
        Query = 'method=returnBalances'
        URL = Proto+Server+Port+PATH+'?method=returnBalances'
        try:
            Balances = Console.get(self, "http://127.0.0.1:8080/AutoTrader?method=returnBalances&pass=gen0cide")
            Balances = ast.literal_eval(Balances)
            if(args != '' and args != ' '):
                for arg in args:
                    Splice = args.upper().split(' ')
                    Arguments = Splice

                print "Pulling Balance for", Arguments
                for Argument in Arguments:
                    Balance = Balances[Argument]
                    balprint = balprint+'\n'+color.UNDERLINE+color.BOLD+color.BLUE+str(Argument)+':'+color.END+str(Balance)+'\n'
                print balprint
            else:
                Arguments = ['']
                print "Returning All Balances..."
                print Balances

        except Exception, e:
            print e.__class__, ":", e  

    def do_getmarkets(self, args):
        try:
            print Markets
        except Exception, e:
            print e.__class__, ":", e 

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_history(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    def do_quit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    def do_ls(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e


if __name__ == '__main__':
        console = Console()
        console . cmdloop() 
