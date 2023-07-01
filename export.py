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
            for host in listOfHostGroups[0]["hosts"]:
                hostListInCare.append(host["hostid"])

if readyToQueryHostObjects:
    if len(hostListInCare) == 0:
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
    else:
        listOfHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "hostids": hostListInCare,
                "output":["host","hostid","status","maintenance_status","groups"],
                "selectItems": "count",
                "selectParentTemplates": ["host"],
                "selectTriggers": "count",
                "selectInterfaces": "extend",
                "selectMacros": "extend",
                "selectGroups":"extend"},
            "auth": token, "id": 1}), verify=False).text))[0].value

if len(listOfHosts) > 0:
    for host in listOfHosts:
        
        # prepare template list as one value in cell
        templateBundle=''
        if len(host["parentTemplates"])>0:
            for idx,elem in enumerate(host["parentTemplates"]):
                templateBundle+=elem["host"]
                # if not last element
                if idx!=len(host["parentTemplates"])-1:
                    templateBundle+=';'

        # prepare host group list as one value in cell
        hostGroupBundle=''
        if len(host["groups"])>0:
            for idx,elem in enumerate(host["groups"]):
                hostGroupBundle+=elem["name"]
                # if not last element
                if idx!=len(host["groups"])-1:
                    hostGroupBundle+=';'


        # if interface array is not empty
        if len(host["interfaces"]) > 0:
            for interface in host["interfaces"]:
                row = {}
                row["hostid"] = host["hostid"]
                row["host"] = host["host"]
                row["templateBundle"] = templateBundle
                row["allGroups"] = hostGroupBundle
                row["macros"] = host["macros"]

                try:
                    row["community"] = interface["interface_details"]['community']
                except:
                    row["community"] = ""
                
                try:
                    row["authpassphrase"] = interface["interface_details"]['authpassphrase']
                except:
                    row["authpassphrase"] = ""

                try:
                    row["authprotocol"] = interface["interface_details"]['authprotocol']
                except:
                    row["authprotocol"] = ""

                try:
                    row["bulk"] = interface["interface_details"]['bulk']
                except:
                    row["bulk"] = ""

                try:
                    row["contextname"] = interface["interface_details"]['contextname']
                except:
                    row["contextname"] = ""

                try:
                    row["privpassphrase"] = interface["interface_details"]['privpassphrase']
                except:
                    row["privpassphrase"] = ""

                try:
                    row["privprotocol"] = interface["interface_details"]['privprotocol']
                except:
                    row["privprotocol"] = ""

                try:
                    row["securitylevel"] = interface["interface_details"]['securitylevel']
                except:
                    row["securitylevel"] = ""

                try:
                    row["securityname"] = interface["interface_details"]['securityname']
                except:
                    row["securityname"] = ""

                try:
                    row["version"] = interface["interface_details"]['version']
                except:
                    row["version"] = ""

                dataInOutput.append(row)

        else:
            row = {}
            row["hostid"] = host["hostid"]
            row["host"] = host["host"]
            row["templateBundle"] = templateBundle
            row["allGroups"] = hostGroupBundle
            row["macros"] = host["macros"]

            row["community"] = ""
            row["authpassphrase"] = ""
            row["authprotocol"] = ""
            row["bulk"] = ""
            row["contextname"] = ""
            row["privpassphrase"] = ""
            row["privprotocol"] = ""
            row["securitylevel"] = ""
            row["securityname"] = ""
            row["version"] = ""
            row["interface_dns"] = ""
            row["interface_ip"] = ""
            row["interface_type"] = ""
            row["interface_port"] = ""

            dataInOutput.append(row)


if len(listOfHostGroups) > 0:
    for group in listOfHostGroups:

        # make sure a subdirectory of host group name exists
        try:
            os.makedirs(os.path.join(csv_export_dir, group["name"]))
        except:
            cannotMakeHostGroupDir = 1
        hostCSV = open(os.path.join(csv_export_dir, group["name"], 'hosts.csv'), 'w', newline='')
        csvHostList_writer = csv.writer(hostCSV)
        hostCSV.close()


pprint(dataInOutput)



