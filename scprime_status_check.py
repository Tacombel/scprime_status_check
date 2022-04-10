from config_local import Config
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
    elif status == 1:
        status = 'Online'
    elif status == 2:
        status = 'Error processing JSON'
    return status

def main():
    provider_list = Config.provider_list
    provider_name = Config.provider_name
    if len(provider_list) == 0:
        print(f'Lista de hosts vacia')
    elif len(provider_list) == 1:
        print(f'Provider {get_status(provider_list[0])}')
    elif len(provider_list) > 1:
        n = 0
        for e in provider_list:
            print(f'Host {provider_name[n]} {get_status(e)}')
            n += 1

if __name__ == '__main__':
    main()
