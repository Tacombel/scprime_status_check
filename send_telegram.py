import requests
from config_local import Config

def send_telegram_msg(message):
    bot_token = Config.telegram_token
    bot_chatID = Config.user_id
    bot_message = message
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=html&text=' + bot_message
    response = requests.get(send_text)
    return response.json()
