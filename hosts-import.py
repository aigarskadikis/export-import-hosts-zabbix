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

existingHostsList = []

for existingHost in listOfExistingHosts:
    existingHostsList.append(existingHost["host"])

for existingHost in listOfExistingHosts:
    for newHost in listOfHosts:
        if newHost["hostName"] in existingHostsList:
            print(bcolors.OKGREEN + "'" + newHost["hostName"] + "' already exists in destination"+ bcolors.ENDC)
        else:
            print(bcolors.FAIL + "'"+newHost["hostName"] + "' is not yet registred")

            pprint(newHost)

            # check if this is ZBX host
            if newHost["interfaceType"]=='1':
                try:
                    # create a Zabbix agent host
                    print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
 "jsonrpc": "2.0",
    "method": "host.create",
    "params": {
        "host": newHost["hostName"],
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": newHost["IP_address"],
                "dns": newHost["interface_DNS"],
                "port": newHost["interfacePort"]
            }
        ],
        "groups": [
            {
                "groupid": "5"
            }
        ]
    },
    "auth": token,
    "id": 1
                  }), verify=False).text))[0].value)
                except:
                    print("unable to create ZBX host")

                
            elif newHost["interfaceType"]=='2':
                print("new host is SNMP")
                # this is SNMP host. Need to check version

                if newHost["version"]=='2':
                    # this is SNMPv2 host
                    try:
                        # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                        print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
 "jsonrpc": "2.0",
    "method": "host.create",
    "params": {
        "host": newHost["hostName"],
        "interfaces": [
            {
                "type": 2,
                "main": 1,
                "useip": 1,
                "ip": newHost["IP_address"],
                "dns": newHost["interface_DNS"],
                "port": newHost["interfacePort"],
                "details" : {
                    "version": newHost["version"],
                    "bulk": newHost["bulk"],
                    "securityname": newHost["securityname"],
                    "contextname": newHost["contextname"],
                    "securitylevel": newHost["securitylevel"],
                    "authpassphrase": newHost["authpassphrase"],
                    "authprotocol": newHost["authprotocol"],
                    "privpassphrase": newHost["privpassphrase"],
                    "privprotocol": newHost["privprotocol"]
                    }
            }
        ],
        "groups": [
            {
                "groupid": "5"
            }
        ]
    },
    "auth": token,
    "id": 1
                  }), verify=False).text))[0].value)
                    except:
                        print("unable to create SNMPv2 host")

                elif newHost["version"]=='3':
                    # this is SNMPv3 host
                    try:
                        # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                        print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
 "jsonrpc": "2.0",
    "method": "host.create",
    "params": {
        "host": newHost["hostName"],
        "interfaces": [
            {
                "type": 2,
                "main": 1,
                "useip": 1,
                "ip": newHost["IP_address"],
                "dns": newHost["interface_DNS"],
                "port": newHost["interfacePort"],
                "details" : {
                    "version": newHost["version"],
                    "bulk": newHost["bulk"],
                    "securityname": newHost["securityname"],
                    "contextname": newHost["contextname"],
                    "securitylevel": newHost["securitylevel"],
                    "authpassphrase": newHost["authpassphrase"],
                    "authprotocol": newHost["authprotocol"],
                    "privpassphrase": newHost["privpassphrase"],
                    "privprotocol": newHost["privprotocol"]
                    }
            }
        ],
        "groups": [
            {
                "groupid": "5"
            }
        ]
    },
    "auth": token,
    "id": 1
                  }), verify=False).text))[0].value)
                    except:
                        print("unable to create SNMPv3 host")
                else:
                    unknownSNMPversion=1

            else:
                    notMatchinSNMPorZBX=1




# close file for writing
listOfHostsCSV.close()
listOfHostMacrosCSV.close()
