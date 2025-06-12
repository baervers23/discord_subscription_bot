# Discord Subscription/Abonnement Bot

I created a discord bot for subscriptions, i use it for jellyfin together with a modified "membarr" bot.
Member with Subscription automatically gets a specific role, this role will cooperate with my customized membarr bot which activates and deactivates jellyfin

at the moment the bot answers in german, i translate it when i finish developing

# Working
```
subscription management with automatic role(timebased)
gift card system
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
Create .env file in root dir.
python3 main.py
```

# .env
```
DISCORD_TOKEN=Your Discord Token
GUILD_ID=Discord Server ID
ABO_ROLE_ID=Subscription Role
ADMIN_USER_ID=Admin Role
```

# commands (user):
```
/probeabo - self activated trial membership
/guthaben - remaining subscription time
/redeem [code] - redeem a subscription code, put codes in (codes.json)
```

# commands (admin):
```
/übersicht - overview of all subscriptions
/addabo [months] - adds x months of subscription to a member
/cancelabo [user] - removes subscription from user
/addcode [code] [months] - add a code called *userinput* for x months
/listcodes - list all available codes 
```


