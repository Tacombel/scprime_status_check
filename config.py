
class Config(object):
    # You need to add a provider ID, in the provider_list, and a provider_name. For every provider that you add make and entry on both lists.
    provider_list = [] # Your hosts Id, between ''. You can add several, separated by ,
    provider_name = [] # Your hosts name, between ''. You can add several, separated by ,
    # email
    port = 465
    email = '' # From address
    password = '' # Password
    dest_email = '' # To address
    #telegram
    # Your Telegram Token. Search @BotFather and create BOT
    telegram_token = "" 
    # Your ID User. Search @userinfobot. There will be several. Keep testing until one answer with something like Id:56869524
    user_id = ""
    #percentage to set the alarm for reduction of used space. 5% in this example
    storage_alarm_factor = 5
