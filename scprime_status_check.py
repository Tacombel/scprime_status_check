from config_local import Config
from send_email import send_email
from send_telegram import send_telegram_msg
import requests
from requests.structures import CaseInsensitiveDict
import json

def get_status(publickey):
    url = 'https://grafana.scpri.me/api/ds/query'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = json.dumps({"queries":[{"refId":"A","datasourceId":2,"rawSql":"SELECT \nverified::int,\nuptimeratio,\n--acceptingcontracts::int,\nincentives_factor,\ntotalstorage, \ntotalstorage-remainingstorage as usedstorage\n--lastscantime*1000 as timestamp\nFROM network.provider_details \nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
    r = requests.post(url, data=data, headers=headers)
    r = r.json()
    try:
        status = r['results']['A']['frames'][0]['data']['values'][0][0]
    except:
        print(f'Error processing JSON', flush=True)
        status = 2
    if status == 0:
        status = 'Offline'
        error = get_error(publickey)
    elif status == 1:
        status = 'Online'
        error = None
    elif status == 2:
        status = 'Error processing JSON'
        error = None
    return status, error

def get_error(publickey):
    url = 'https://grafana.scpri.me/api/ds/query'
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = json.dumps({"queries":[{"refId":"B","datasourceId":2,"rawSql":"SELECT\ncase\n    when acceptingcontracts and verified = false then 'Different provider has more recently announced on this address'\n    when (\"Error\" is not null or \"Error\" != '') and (verified is null or verified = false) then 'Unable to connect to provider on this address'\n    else null\nend as err_conn,\ncase\n    when verified and version is not null and version < '1.6.3.2' then 'Outdated daemon v'||version||' - Update to 1.6.3.2'\n    when verified and (relayerport is null or relayerport='invalid') then 'API port ('||(SUBSTRING(netaddress, POSITION(':' IN netaddress) + 1, 6)::int + 1)||') error - Check forwarding'\n    when acceptingcontracts = false and verified then 'Not accepting contracts - Wallet locked or set to \"acceptingcontracts false”'\n    when totalstorage < ir.min_totalstorage then 'Capacity offered is below incentives minimum (500 GB)'\n    when verified then null\n    else 'N/A'\nend as err_config,\ncase\n    when storageprice < ir.min_storageprice or (storageprice > ir.max_storageprice or ir.max_storageprice is null) then 'Storage price outside of incentives range'\n    when (collateral/storageprice) < ir.min_collateralratio then 'Collateral price should be at least 1x storage price'\n    else null\nend as err_pricing\n--case when uptimeratio is not null and uptimeratio < '0.95' then case when uptimeratio > '0.85' then 1 else 0 end end as uptimewarn\n--\"Error\"\nFROM network.provider_details s\ncross join lateral (select * from network.incentives_requirements order by valid_since desc limit 1) ir\nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
    r = requests.post(url, data=data, headers=headers)
    r = r.json()
    return json.dumps(r['results']['B']['frames'][0]['data']['values'])

def send_error(status, error, n):
    provider_name = Config.provider_name
    if status == 'Error processing JSON' or status == 'Offline':
        subject = 'ScPrime Status Check ALARM'
        text =   provider_name[n] + ': ' + status + ' ' + error
        text_tlgrm = '<b>' + provider_name[n] + '</b>: ' + status + ' ' + error
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
        status, error = get_status(provider_list[0])
        print(f'Provider {status}, {error}', flush=True)
        send_error(status, error, 0)
    elif len(provider_list) > 1:
        n = 0
        for e in provider_list:
            status, error = get_status(e)
            print(f'Host {provider_name[n]} {status}, {error}', flush=True)
            send_error(status, error, n)
            n += 1

if __name__ == '__main__':
    main()
