# Telegram Bot for KeePass
# 09.02.2023
# installing repository pip install pyTelegramBotAPI
# https://github.com/eternnoir/pyTelegramBotAPI
# https://pypi.org/project/pykeepass/

import logging
import threading
import telebot
from telebot import formatting
from pykeepass import PyKeePass
import random
import string

Passlength=16
TelegramToken=<Telegram Token>
DataFile="data.config"
UserData={}
UserDBPass=''

bot = telebot.TeleBot(TelegramToken, parse_mode=None)
logging.basicConfig(level=logging.INFO)

def ReadConfigFile(): #read user data
    res = {}
    try:
        with open(DataFile,"r") as text:
            for line in text:
                if not line[0]=='#' and not line=='\n': #remove comments and new lines
                    key, value = line.split('=')
                    if len(key)>1 :     
                            if value[-1]=='\n': res[key] = value[:-1]
                            else: res[key] = value
    except:
        logging.error('Error opening config file')
    return res

UserData=ReadConfigFile() # load User settings

def DBOpen(): # load database
    ERR=0 #no error
    logging.info('Opening DB'+UserData['dbFolder']+UserData['dbFile'])
    try:
        kp = PyKeePass(UserData['dbFolder']+UserData['dbFile'], password=UserDBPass) #load db
    except Exception as e: 
        ErrTxt=type(e).__name__ 
        kp=''
        match ErrTxt:
            case 'CredentialsError':
                logging.error('Wrong password')
                ERR=1
            case 'HeaderChecksumError':
                logging.error('database tampering or file corruption')
                ERR=2
            case 'PayloadChecksumError':
                logging.error('corruption during database saving')
                ERR=3
            case _:
                logging.error('other error doring file opening')
                ERR=4
    return (kp,ERR)

def DBERRHandle(msgID,ERR): # send user error message for opening db
    match ERR:
        case 1:
            bot.send_message(msgID,"Unable to open DB- Wrong Password")
        case 2:
            bot.send_message(msgID,"Unable to open DB- database tampering or file corruption")
        case 3:
            bot.send_message(msgID,"Unable to open DB- corruption during database saving")
        case 4:
            bot.send_message(msgID,"Unable to open DB- error in configuration file")

# setting menu
bot.delete_my_commands(scope=None, language_code=None) # delete previus commands
bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("dbpass", "Set database password"),
        telebot.types.BotCommand("db", "Connect to database\nSee /db help for help"),
        telebot.types.BotCommand("userid", "Prints Telegram user ID"),
    ],
)

@bot.message_handler(commands=['db']) #open DB and print password
def send_welcome(message):
    AllowUserLST=map(int,UserData['AllowUser'].split(','))# split to list and convert to int
    UsrDBMsg=message.text.split(' ')
    if len(UsrDBMsg)==1 : #Check if no argument after /db
        bot.send_message(message.chat.id,'Use\n'+formatting.mcode('/db help to display help'),parse_mode='MarkdownV2')
    elif message.from_user.id in AllowUserLST:        
        if not UserDBPass=='' or UsrDBMsg[1].lower()=='help':
            # syntax: get, put, del          
            DelTime=1 # in minutes
            match UsrDBMsg[1].lower():
                case "get":
                    res=DBOpen()
                    if res[1]>0: #handle error opening db
                        DBERRHandle(message.chat.id,res[1])
                    else :
                        bot.send_chat_action(message.chat.id, 'typing')
                        entry = res[0].find_entries_by_title(UsrDBMsg[2],regex=True)
                        if len(entry)==0: #no result
                            bot.send_message(message.chat.id,'No entries found')
                        else:
                            for x in range(len(entry)):
                                if not str(entry[x].group)=='Group: "Recycle Bin"':
                                    # handle empty entries
                                    EUsr=EURL=EPass= ''
                                    if entry[x].username is not None: EUsr='\nUser: '+entry[x].username
                                    if entry[x].password is not None: EPass='\nPassword: '+entry[x].password
                                    if entry[x].url is not None: EURL='\nURL: '+entry[x].url

                                    bot.send_message(message.chat.id,'Title: '+
                                        entry[x].title+EUsr+EPass+EURL+
                                        '\nThis massage will disapear in '+str(DelTime)+' minutes')    
                                    threading.Timer(DelTime*60, delMsgDelay,[message.chat.id,message.id+x,2]).start()
                                else:
                                    bot.send_message(message.chat.id,'Entry '+str(x)+' is in the recycle bin')
                case "put":
                    if len(UsrDBMsg)>3: #check if syntex is correct len=4,5,6
                        res=DBOpen()
                        if res[1]>0: #handle error opening db
                            DBERRHandle(message.chat.id,res[1])
                        else:
                            match len(UsrDBMsg):
                                case 4:# no password entered
                                    randomstr = ''.join(random.sample(string.ascii_letters+string.digits,Passlength))
                                    res[0].add_entry(res[0].root_group, UsrDBMsg[2], UsrDBMsg[3], randomstr)
                                    bot.send_message(message.chat.id,'Password:\n'+randomstr+'\nThis massage will disapear in '+str(DelTime)+' minutes\nEntry Saved')
                                    threading.Timer(DelTime*60, delMsgDelay,[message.chat.id,message.id,2]).start() #deleting message
                                case 5: # use /db put [title] [user] [password] 
                                    res[0].add_entry(res[0].root_group, UsrDBMsg[2], UsrDBMsg[3], UsrDBMsg[4])
                                    bot.send_message(message.chat.id,'This massage will disapear in '+str(DelTime)+' minutes\nEntry Saved')
                                    threading.Timer(DelTime*60, delMsgDelay,[message.chat.id,message.id-1,2]).start() #deleting message
                                case 6: # use /db put [title] [user] [password] [URL]
                                    res[0].add_entry(res[0].root_group, UsrDBMsg[2], UsrDBMsg[3], UsrDBMsg[4],UsrDBMsg[5])
                                    bot.send_message(message.chat.id,'This massage will disapear in '+str(DelTime)+' minutes\nEntry Saved')
                                    threading.Timer(DelTime*60, delMsgDelay,[message.chat.id,message.id-1,2]).start() #deleting message                    
                            res[0].save()
                    else:
                         bot.send_message(message.chat.id,'Syntax error\nUse:\n'+
                            formatting.mcode('/db put [Title] [User] [Password] [URL]'),parse_mode='MarkdownV2') 
                case "del":
                    res=DBOpen()
                    if res[1]>0: #handle error opening db
                        DBERRHandle(message.chat.id,res[1])
                    else :
                        entry = res[0].find_entries(title=UsrDBMsg[2])
                        if len(entry)==0: #no result
                            bot.send_message(message.chat.id,'Entry not found')
                        else:
                            bot.send_message(message.chat.id,'Found '+str(len(entry))+' entries in database')
                            for x in range(len(entry)):
                                if eval(UserData['MoveToTrash']):
                                    res[0].trash_entry(entry[x])
                                else:
                                    res[0].delete_entry(entry[x])
                            res[0].save()
                            bot.send_message(message.chat.id,'Entry Deleted')                            
                case "help":
                    logging.info('Display db help')
                    bot.send_message(message.chat.id,'Connect to database\nUse\n'+
                        formatting.mcode('/db get [Title]  to get entry from the database\n'+
                        '/db put [Title] [User] [Password] [URL] to put entry into the database\n'+
                        '/db put [Title] [User] [Password] to put entry into the database\n'+
                        '/db put [Title] [User] to put entry into the database with random passowrd\n'+
                        '/db del to delete entry from the database'),parse_mode='MarkdownV2')
                case _: # If an exact match is not confirmed, this last case will be used if provided
                    logging.warning('/db arguments error')
                    bot.send_message(message.chat.id,'Syntax error\nUse\n'+
                        formatting.mcode('/db get put del [option]'),parse_mode='MarkdownV2')
        else:  
            logging.info('No password in memory')
            bot.send_message(message.chat.id,'Syntax error\nUse\n'+
                formatting.mcode('/dbpass [password]'),parse_mode='MarkdownV2')        
    else:
        logging.info('User ID dont match')
        bot.send_message(message.chat.id,'User have no permission !')

@bot.message_handler(commands=['userid']) # Show UserID
def send_welcome(message):
    logging.info('Show User ID')
    bot.send_message(message.chat.id,'User ID \= '+
        formatting.mbold(str(message.from_user.id)),parse_mode='MarkdownV2')# Show UserID

@bot.message_handler(commands=['dbpass']) #get DB password and delete it after 5 min
def send_welcome(message):
    userText=message.text[8:]
    if userText=="":
        bot.send_message(message.chat.id,'No password entered \nUse:\n'+
            formatting.mcode('/dbpass [password]'),parse_mode='MarkdownV2') 
    else:
        DelTime=5 # in minutes
        threading.Timer(DelTime*60, delMsgDelay,[message.chat.id,message.id,1]).start()
        global UserDBPass
        UserDBPass=userText
        bot.send_message(message.chat.id,'This massage will detele from system in '+str(DelTime) +' minutes') 

def delMsgDelay(chatID,msgID,UseCase): 	#function for delete message
    logging.info(str(msgID)+' message delete function start')
    if not bot.delete_message(chatID,msgID+1):
        logging.warning('Error delete massage ID '+msgID+1)
    match UseCase:
        case 1: # call from /dbpass
            if not bot.delete_message(chatID,msgID):
                logging.warning('Error delete massage ID '+msgID)
            global UserDBPass
            UserDBPass='' #zero memory password
            bot.send_message(chatID,'Password deleted from system')
        case 2: #call from /db get
            pass
        #    bot.send_message(chatID,'Entry disapeared') 
        case _:
            logging.error('Error in handling parameter')

def main():    
    bot.infinity_polling()

if __name__ == '__main__':
    main()
