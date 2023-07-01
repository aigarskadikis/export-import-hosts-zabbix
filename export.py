#!/bin/env python3.9
import sys
sys.path.insert(0,'/var/lib/zabbix')
import config
import os
import requests
import json
from jsonpath_ng import jsonpath, parse
import csv
from pprint import pprint
import urllib3
urllib3.disable_warnings()

import optparse
parser=optparse.OptionParser()
parser.add_option('-g','--group',help='give a host group')
parser.add_option('-l','--limit',help='limit the call',type=int)
(opts,args) = parser.parse_args()

if opts.limit:
    if not opts.group:
        limit=opts.limit
    else:
        limit=99999
else:
    limit=99999

url = config.url_src_instance
user = config.username_src_instance
password = config.password_src_instance
csv_export_dir = config.csv_export_dir

try:
    os.makedirs(csv_export_dir)
except:
    makeDirFailes = 1

hostListInCare = []
listOfHosts = []
dataInOutput = []
listOfHostGroups = []
readyToQueryHostObjects = 1

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}
response = requests.request("POST", url, headers=headers, data=payload, verify=False)
token = parse('$.result').find(json.loads(response.text))[0].value

if not opts.group:
    # get list of all host groups and host objects inside
    listOfHostGroups = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "hostgroup.get",
    "params": { "output": ["groupid","name","hosts"], "selectHosts":"query" },
    "auth": token,"id": 1}), verify=False).text))[0].value
else:
    listOfHostGroups = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
        "method":"hostgroup.get",
        "params":{"output":["groupid","name","hosts"],"filter":{"name":[opts.group]},"selectHosts":"query"},
        "auth": token,"id": 1}), verify=False).text))[0].value
    if len(listOfHostGroups) == 0:
        print("specified host group '"+opts.group+"' does not exists")
        readyToQueryHostObjects=0
    else:
        if len(listOfHostGroups[0]["hosts"]) == 0:
            print("specified host group '"+opts.group+"' exists, but do not contain any host objects. nothing to do")
            readyToQueryHostObjects = 0
        else:
            print(listOfHostGroups[0]["hosts"])

if readyToQueryHostObjects:
    # get list of hosts
    listOfHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output":["host","hostid","status","maintenance_status","groups"],
        "selectItems": "count",
        "selectParentTemplates": ["host"],
        "selectTriggers": "count",
        "selectInterfaces": "extend",
        "selectMacros": "extend",
        "selectGroups":"extend"},
    "auth": token, "id": 1}), verify=False).text))[0].value


