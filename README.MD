This script monitors your grafana data to check your status from its point of view. It is independent of spd or spc so you can run it where you like.

It is recomended to install it in a server outside the subnet where your provider is (AWS, Oracle,...)

As of 30/5/2022 gmail will block unsecure use of its API so using Telegram is recomended.

- Create a new Google account.
- Turn https://myaccount.google.com/lesssecureapps to ON. This makes your account less secure.

It is recomended to use a secondary account for this, as the reduced security makes it vulnerable.

You can also use telegram. For that you will need to add the neccessary info as specified in the config.py

The following is for linux, but windows should be quite similar.

Download the last release and unzip it

cd to the directory

Edit config.py, add the data and save it as config_local.py

You can add several hosts separated by commas

test it 

$ python3 scprime_status_check.py

You will need a cronjob to execute it periodicaly.

$ crontab -e

And add a line similar to this one, that will execute the script every 20 minutes.

In order to prevent everybody scraping at the same time, you can get an aleatory minute from the following api and use it in the cron job

x = http://www.randomnumberapi.com/api/v1.0/random?min=0&max=59

x/20 * * * * systemd-cat -t "checkstatus-cron" python3 /home/daniel/scprime_status_check/scprime_status_check.py

To check the journal use

$ sudo journalctl -fn1000|grep checkstatus

Donations welcome:

SCP: 29397f5ac09162c48aeea537c4950d90a6b370899a2c8054a71e82ab4954228bb63e59c56464
