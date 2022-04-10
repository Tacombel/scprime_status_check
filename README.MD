- Create a new Google account.
- Turn https://myaccount.google.com/lesssecureapps to ON. This makes your account less secure.

It is recomended to use a secondary account for this, as the reduced security makes it vulnerable.

Download the last release and unzip it

cd to the directory

Edit config.py, add the data and save it as config_local.py

You can add several hosts separated by commas

test it 

$ python3 scprime_status_check.py

You will need a cronjob to execute it periodicaly.

$ crontab -e

And add a line similar to this one, that will execute the script every 20 minutes.

*/20 * * * * systemd-cat -t "checkstatus-cron" python3 /home/daniel/scprime_status_check/scprime_status_check.py

Donations welcome:

SCP: 29397f5ac09162c48aeea537c4950d90a6b370899a2c8054a71e82ab4954228bb63e59c56464