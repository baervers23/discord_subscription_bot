# Discord Subscription/Abonnement Bot

A Discord Bot with the purpose of managing “Premium Memberships” via time-based Discord Roles.

The bot is useful for various purposes and communities so I share it as a standalone bot

I use it together with a modified membarr-bot in Jellyfin. The subscription bot takes care of everything concerning the membership and the modified membarr-bot takes care of the account creation as well as the deactivation and activation of the users. 

I will soon upload the modified membarr-bot to github and link it here

At the moment the bot is programmed in German and the commands in English, if necessary you have to translate it yourself.

Translated with DeepL.com (free version)

# Working
```
timebased role management - bot give the role while subscription is active and take the role when the subscription expires
gift card system - add custom codes like for example a netflix giftcard
trial membership - let the user start a trial month per slash command
reminder - reminds a user at 30/7/3 days before his subscription expires
manual admin commands & user commands (see below)
```

# Create a Discord Bot
 1) Create the discord server that your users will get member roles or use an existing discord that you can assign roles from
 2) Log into https://discord.com/developers/applications and click 'New Application'
 3) (Optional) Add a short description and an icon for the bot. Save changes.
 4) Go to 'Bot' section in the side menu
 5) Uncheck 'Public Bot' under Authorization Flow
 6) Check all 3 boxes under Privileged Gateway Intents: Presence Intent, Server Members Intent, Message Content Intent. Save changes.
 7) Copy the token under the username or reset it to copy. This is the token used in the docker image.
 8) Go to 'OAuth2' section in the side menu, then 'URL Generator'
 9) Under Scopes, check 'bot' and applications.commands
10) Copy the 'Generated URL' and paste into your browser and add it to your discord server from Step 1.

# Installation
```
git clone https://github.com/baervers23/discord_abo_bot.git
pip3 install -r requirements.txt 
edit .env file in root dir.
python3 main.py
```

# .env
```
DISCORD_TOKEN=Your Discord Token
GUILD_ID=Discord Server ID
ABO_ROLE_ID=Subscription Role ID
ADMIN_USER_ID=Admin Role ID
```

# commands (user):
```
/probeabo - self activated trial membership
/guthaben - remaining subscription time
/redeem [code] - redeem a subscription code from the codes.json file
```

# commands (admin):
```
/übersicht - overview of all subscriptions
/addabo [months] - adds x months of subscription to a member
/cancelabo [user] - removes subscription from user
/addcode [code] [months] - add a code called *userinput* for x months
/listcodes - list all available codes 
```


