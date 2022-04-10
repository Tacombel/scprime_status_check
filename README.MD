- Create a new Google account.
- Turn https://myaccount.google.com/lesssecureapps to ON. This makes your account less secure.

You will need a cronjob to execute it periodicaly.

$ crontab -e

And add a line similar to this one, that will execute the script every 20 minutes.

*/20 * * * * systemd-cat -t "checkstatus-cron" python3 /home/daniel/scprime_status_check/scprime_status_check.py