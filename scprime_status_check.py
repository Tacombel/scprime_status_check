#v0.8

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
    data = json.dumps({"queries":[{"refId":"A","datasourceId":2,"rawSql":"SELECT \nverified::int,\nuptimeratio,\n--acceptingcontracts::int,\nincentives_factor,\ntotalstorage as \"Total Capacity\",\nleast(scp_corp_data_bytes,totalstorage-remainingstorage) as \"Used (SCP Corp)\"\n--lastscantime*1000 as timestamp\nFROM network.provider_details\njoin lateral\n(\nselect\n\tcoalesce(sum(bytes),0)::bigint as scp_corp_data_bytes\n\tfrom contracts.contractors cc\n\tcross join lateral (\n\t\tselect bytes \n\t\tfrom contracts.contractsize where cc.id=contractorid\n\t\tand publickey=provider_details.publickey\n\t\tand timestamp between provider_details.lastsuccessfulscantime-86400 and provider_details.lastsuccessfulscantime\n\t\torder by timestamp desc nulls last limit 1) cs\n) contracts on true\n--left join network.provider_storage ps using (publickey)\nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
    r = requests.post(url, data=data, headers=headers)
    r = r.json()
    usedstorage = 0
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
    data = json.dumps({"queries":[{"refId":"B","datasourceId":2,"rawSql":"SELECT\r\ncase\r\n    when acceptingcontracts = true and verified = false \r\n    \tthen 'Different provider has more recently announced on this address'\r\n    when (\"Error\" is not null or \"Error\" != '') and (verified is null or verified = false) \r\n    \tthen 'Unable to connect to provider on this address'\r\n    else null\r\nend as err_conn,\r\ncase\r\n    when acceptingcontracts = true and verified = false \r\n    \tthen 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#unable-to-connect-to-provider-on-this-address'\r\n    when (\"Error\" is not null or \"Error\" != '') and (verified is null or verified = false) \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#unable-to-connect-to-provider-on-this-address'\r\n    else null\r\nend as res_conn,\r\ncase\r\n    when network.is_licensed('"+publickey+"') is distinct from true then 'Provider has no license assigned'\r\n    when verified and version is not null and version < '1.6.6' then 'Outdated daemon v'||version||' - Update to latest'\r\n    when verified and (relayerport is null or relayerport='invalid') then 'API port ('||(SUBSTRING(netaddress, POSITION(':' IN netaddress) + 1, 6)::int + 1)||') error - Check forwarding'\r\n    when acceptingcontracts = false and verified then 'Not accepting contracts - Wallet locked or set to \"acceptingcontracts false”'\r\n    when totalstorage < ir.min_totalstorage then 'Capacity offered is below incentives minimum (500 GB)'\r\n    when s.blockheight < (select blockheight-2 from consensus.blocks where orphaned = false and timestamp <= s.lastsuccessfulscantime order by blockheight desc limit 1) then\r\n    'Blockchain not synchronized'\r\n    when verified is distinct from true then 'N/A'\r\n    else null\r\nend as err_config,\r\ncase\r\n    when network.is_licensed('"+publickey+"') is distinct from true \r\n      then 'https://docs.scpri.me/diy-getting-started/licensing-faq#now-that-ive-received-my-license-how-do-i-apply-it'\r\n    when verified and version is not null and version < '1.6.6' \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_4q950ljeooxn'\r\n    when verified and (relayerport is null or relayerport='invalid') \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_yvoxh8mhl1ho'\r\n    when acceptingcontracts = false and verified \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_s88dtf52hg8d'\r\n    when totalstorage < ir.min_totalstorage \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_f6x66h5el11g'\r\n    when s.blockheight < (select blockheight-2 from consensus.blocks where orphaned = false and timestamp <= s.lastsuccessfulscantime order by blockheight desc limit 1) \r\n      then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_ny6qtmcmmxvx'\r\n    when verified then null\r\nend as res_config,\r\ncase\r\n    when storageprice < ir.min_storageprice or (storageprice > ir.max_storageprice or ir.max_storageprice is null) then 'Storage price outside of incentives range'\r\n    when (collateral/storageprice) < ir.min_collateralratio then 'Collateral price should be at least 1x storage price'\r\n    when contracted.bytes is not null and maxcollateral <= storageprice*contracted.bytes*4000 then 'Maxcollateral low'\r\n    when verified is distinct from true then 'N/A'\r\n    else null\r\nend as err_pricing,\r\ncase \r\n    when storageprice < ir.min_storageprice or (storageprice > ir.max_storageprice or ir.max_storageprice is null) \r\n  then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_35ydz9usi69g'\r\n    when storageprice>0 and (collateral/storageprice) < ir.min_collateralratio \r\n  then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_hohsgkcyp3ph'\r\n    when contracted.bytes is not null and maxcollateral <= storageprice*contracted.bytes*4000 \r\n  then 'https://docs.scpri.me/tutorials/grafana-provider-status-messages#_i7sckyjx8cmw'\r\n    else null\r\nend as res_settings\r\n--case when uptimeratio is not null and uptimeratio < '0.95' then case when uptimeratio > '0.85' then 1 else 0 end end as uptimewarn\r\n--\"Error\"\r\nFROM network.provider_details s\r\ncross join lateral (select * from network.incentives_requirements order by valid_since desc limit 1) ir\r\nleft join (select bytes \r\n\t\tfrom contracts.contractsize where contractorid=1\r\n\t\tand publickey='"+publickey+"'\r\n\t\torder by timestamp desc nulls last limit 1) contracted on true\r\nWHERE publickey='"+publickey+"'","format":"table","intervalMs":3600000,"maxDataPoints":874}],"range":{"raw":{"from":"now-30d","to":"now"}}})
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
