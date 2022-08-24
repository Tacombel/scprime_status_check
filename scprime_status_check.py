from config_local import Config
from os.path import exists
from send_email import send_email
from send_telegram import send_telegram_msg
import requests
from requests.structures import CaseInsensitiveDict
import json

def get_status(publickey, name):
    url = 'https://grafana.scpri.me/api/ds/query'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = json.dumps({"queries":[{"refId":"A","datasourceId":2,"rawSql":"SELECT \nverified::int,\nuptimeratio,\n--acceptingcontracts::int,\nincentives_factor,\ntotalstorage, \ntotalstorage-remainingstorage as usedstorage\n--lastscantime*1000 as timestamp\nFROM network.provider_details \nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
    r = requests.post(url, data=data, headers=headers)
    r = r.json()
    try:
        status = r['results']['A']['frames'][0]['data']['values'][0][0]
        usedstorage = r['results']['A']['frames'][0]['data']['values'][4][0]
        usedstorage = int(usedstorage)
    except:
        print(f'Error processing JSON', flush=True)
        status = 2
    
    usedstorage_dict = {}
    if exists('usedstorage.txt'):
        with open('usedstorage.txt') as f:
            usedstorage_dict = json.loads(f.read())
            if name in usedstorage_dict:
                usedstorage_old = usedstorage_dict[name]
            else:
                usedstorage_old = usedstorage
    else:
        usedstorage_old = usedstorage
    usedstorage_alarm = False
    if usedstorage < (usedstorage_old * (100 - Config.storage_alarm_factor) / 100):
        usedstorage_alarm = True
    
    usedstorage_dict[name] = usedstorage
    with open('usedstorage.txt', 'w') as f:
        f.write(json.dumps(usedstorage_dict))
        f.close()

    error = get_error(publickey)
    if len(error) == 0:
        error = None
    if status == 0:
        status = 'Offline'
    elif status == 1:
        status = 'Online'
    elif status == 2:
        status = 'Error processing JSON'
    return status, error, usedstorage_alarm

def get_error(publickey):
    url = 'https://grafana.scpri.me/api/ds/query'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = json.dumps({"queries":[{"refId":"B","datasourceId":2,"rawSql":"SELECT\ncase\n    when acceptingcontracts and verified = false then 'Different provider has more recently announced on this address'\n    when (\"Error\" is not null or \"Error\" != '') and (verified is null or verified = false) then 'Unable to connect to provider on this address'\n    else null\nend as err_conn,\ncase\n    when verified and version is not null and version < '1.6.3.2' then 'Outdated daemon v'||version||' - Update to 1.6.3.2'\n    when verified and (relayerport is null or relayerport='invalid') then 'API port ('||(SUBSTRING(netaddress, POSITION(':' IN netaddress) + 1, 6)::int + 1)||') error - Check forwarding'\n    when acceptingcontracts = false and verified then 'Not accepting contracts - Wallet locked or set to \"acceptingcontracts false”'\n    when totalstorage < ir.min_totalstorage then 'Capacity offered is below incentives minimum (500 GB)'\n    when verified then null\n    else 'N/A'\nend as err_config,\ncase\n    when storageprice < ir.min_storageprice or (storageprice > ir.max_storageprice or ir.max_storageprice is null) then 'Storage price outside of incentives range'\n    when (collateral/storageprice) < ir.min_collateralratio then 'Collateral price should be at least 1x storage price'\n    else null\nend as err_pricing\n--case when uptimeratio is not null and uptimeratio < '0.95' then case when uptimeratio > '0.85' then 1 else 0 end end as uptimewarn\n--\"Error\"\nFROM network.provider_details s\ncross join lateral (select * from network.incentives_requirements order by valid_since desc limit 1) ir\nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
    r = requests.post(url, data=data, headers=headers)
    r = r.json()
    r = r['results']['B']['frames'][0]['data']['values']
    response = []
    for e in r:
        if e[0] is not None:
            response.append(e[0])
    return response

def send_error(status, error, storage, n):
    provider_name = Config.provider_name
    if status == 'Error processing JSON' or status == 'Offline':
        subject = 'ScPrime Status Check ALARM'
        if error:
            text =   provider_name[n] + ': ' + status + ' ' + str(error)
            text_tlgrm = '<b>' + provider_name[n] + '</b>: ' + status + ' ' + str(error)
        else:
            text =   provider_name[n] + ': ' + status
            text_tlgrm = '<b>' + provider_name[n] + '</b>: ' + status
        if Config.email != "":
            send_email(subject, text)
        if Config.telegram_token != "":
            send_telegram_msg(text_tlgrm)
    if status == 'Online' and error:
        subject = 'ScPrime Status Check ALARM'
        text =   provider_name[n] + ': ' + status + ' ' + str(error)
        text_tlgrm = '<b>' + provider_name[n] + '</b>: ' + status + ' ' + str(error)
        if Config.email != "":
            send_email(subject, text)
        if Config.telegram_token != "":
            send_telegram_msg(text_tlgrm)
    if storage:
        subject = 'ScPrime Status Check ALARM'
        text =   provider_name[n] + ': Storage Alarm'
        text_tlgrm = '<b>' + provider_name[n] + '</b>: Storage Alarm'
        if Config.email != "":
            send_email(subject, text)
        if Config.telegram_token != "":
            send_telegram_msg(text_tlgrm)

def main():
    provider_list = Config.provider_list
    provider_name = Config.provider_name
    if len(provider_list) == 0:
        print(f'Lista de hosts vacia', flush=True)
        send_email('ScPrime Status Check ALARM', 'Empty hosts list. Check config_local.py')
    elif len(provider_list) == 1:
        status, error, storage = get_status(provider_list[0], provider_name[0])
        print(f'Host {provider_name[0]} {status}, {error}', flush=True)
        if storage:
            print(f'Host {provider_name[0]}: Storage Alarm', flush=True)
        send_error(status, error, storage, 0)
    elif len(provider_list) > 1:
        n = 0
        for i, e in enumerate(provider_list):
            status, error, storage = get_status(e, provider_name[i])
            print(f'Host {provider_name[n]} {status}, {error}', flush=True)
            if storage:
                print(f'Host {provider_name[n]}: Storage Alarm', flush=True)
            send_error(status, error, storage, n)
            n += 1


if __name__ == '__main__':
    main()
