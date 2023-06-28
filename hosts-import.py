#!/bin/env python3.9
import sys
sys.path.insert(0,'/var/lib/zabbix')
import config
import os
import requests
import json
import urllib3
urllib3.disable_warnings()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# shortify vairables
url = config.url_dest_instance
user = config.username_dest_instance
password = config.password_dest_instance
csv_export_dir = config.csv_export_dir

try:
    os.makedirs(csv_export_dir)
except:
    makeDirFailes = 1

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# format output better
from pprint import pprint

# load CSV files
listOfHostsCSV = open(csv_export_dir+'/hosts.csv','rt')
listOfHosts = csv.DictReader(listOfHostsCSV)
listOfHostMacrosCSV = open(csv_export_dir+'/macros.csv','rt')
ListOfHostMacros = csv.DictReader(listOfHostMacrosCSV)

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value

# get list of existing host names
listOfExistingHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output":["host","hostid"]
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

# check host name in existing instance
for existingHost in listOfExistingHosts:
    #print(existingHost["host"])

    for newHost in listOfHosts:
        if newHost["hostName"]==existingHost["host"]:
            print(bcolors.OKGREEN + newHost["hostName"] + " already exists in destination"+ bcolors.ENDC)
        else:
            print(newHost["hostName"] + "is not yet registred")


# close file for writing
listOfHostsCSV.close()
listOfHostMacrosCSV.close()
