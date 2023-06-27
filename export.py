#!/bin/env python3.9

# cat /var/lib/zabbix/config.py
# url = "http://127.0.0.1/api_jsonrpc.php"
# username = "Admin"
# password = "zabbix"

import sys
sys.path.insert(0,'/var/lib/zabbix')
import config

# work with Zabbix API JSON RPC
# pip3.9 install requests
import requests
import json

# supress warnings in case of self signed certificate:
# /usr/local/lib/python3.9/site-packages/urllib3/connectionpool.py:1095: InsecureRequestWarning: Unverified HTTPS request is being made to host 'zabbix.aigarskadikis.com'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
import urllib3
urllib3.disable_warnings()

# shortify vairables
url = config.url
user = config.username
password = config.password

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# prepare a file to write
data_file = open('/tmp/jsonoutput.csv', 'w', newline='')
csv_writer = csv.writer(data_file)


# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value
print(token)

# get list of hosts

listOfHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output":["host","hostid"]
        
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

print(listOfHosts)

listOfInterfaces = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "hostinterface.get",
    "params": {
        "output": "extend"
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

#print(listOfInterfaces)

# write output to file
count = 0
for data in listOfHosts:
    if count == 0:
        header = data.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(data.values())

# close file for writing
data_file.close()

