# TelegramKeyPass
KeyPass integration into telegram- because why not
Useful in cases of personal keepass data file on local machine.

usecase:
  Setting a local keepass file on internal Raspberry pi server, and adding a telegram channel for querying the database on the go.
  
# Features
 * Secure personal keepass database (database file not exposed to the internet)
 * Add/Remove/Search querys. 
 * All sensative messages have auto deletation.

# Usege
* Modify settings in data.config
* use /help for command description
* /dbpass [your password]
* /db (get) (put) (del) query for interacting with database

# Libraries using:
* [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
* [PyKeePass](https://pypi.org/project/pykeepass)


# Obtaining keys
* [Obtaine Telegram Token](https://core.telegram.org/bots#botfather)
* Obtain telegram User ID.
* A ready to use KeePass database.
