#!/bin/env python3.9

# cat /var/lib/zabbix/config.py
# url = "http://127.0.0.1/api_jsonrpc.php"
# username = "Admin"
# password = "zabbix"

import sys
sys.path.insert(0,'/var/lib/zabbix')
import config

# make directories
import os

# work with Zabbix API JSON RPC
# pip3.9 install requests
import requests
import json


# to support arguments
import optparse

parser=optparse.OptionParser()

# import options
parser.add_option('-g','--group',help='give a host group')
parser.add_option('-l','--limit',help='limit the call',type=int)

(opts,args) = parser.parse_args() # instantiate parser

# if limit was defined then override
if opts.limit:
    if not opts.group:
        limit=opts.limit
    else:
        limit=99999
else:
    limit=99999


# supress warnings in case of self signed certificate:
# /usr/local/lib/python3.9/site-packages/urllib3/connectionpool.py:1095: InsecureRequestWarning: Unverified HTTPS request is being made to host 'zabbix.aigarskadikis.com'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
import urllib3
urllib3.disable_warnings()

# shortify vairables
url = config.url_src_instance
user = config.username_src_instance
password = config.password_src_instance
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

# prepare a file to write host list
hostListCSV = open(csv_export_dir+'/hosts.csv', 'w', newline='')
csvHostList_writer = csv.writer(hostListCSV)

# prepare a file to write macro list
macroListCSV = open(csv_export_dir+'/macros.csv', 'w', newline='')
csvMacroList_writer = csv.writer(macroListCSV)

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

token = parse('$.result').find(json.loads(response.text))[0].value

# get list of hosts
listOfHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output":["host","hostid","status","maintenance_status","groups"],
        "selectItems": "count",
        "selectParentTemplates": ["host"],
        "selectTriggers": "count",
        "selectMacros": "extend",
        "selectGroups":"query"},
    "auth": token, "id": 1}), verify=False).text))[0].value

listOfHostMacros = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "usermacro.get",
    "params": {
        "output":"extend"},
    "auth": token,"id": 1}), verify=False).text))[0].value

listOfHostGroups = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "hostgroup.get",
    "params": { "output": ["groupid","name","hosts"], "selectHosts":"query" },
    "auth": token,"id": 1}), verify=False).text))[0].value

# rename elements in JSON tree to not conflict while mapping with other result
for host in listOfHosts:
    host["hostName"] = host.pop("host")
    host["hostStatus"] = host.pop("status")
    host["amountOfItems"] = host.pop("items")
    host["amountOfTriggers"] = host.pop("triggers")
    templateBundle=''
    if len(host["parentTemplates"])>0:
        for idx,elem in enumerate(host["parentTemplates"]):
            templateBundle+=elem["host"]
            # if not last element
            if idx!=len(host["parentTemplates"])-1:
                templateBundle+=';'
    host["templateBundle"] = templateBundle
    # remove parentTemplates after parsing
    host.pop("parentTemplates")
    # count macros in output
    host["amountOfMacros"] = len(host.pop("macros"))

# map host name to host macro table
hostMacroWithHostName = []

# go through reported macros and create annother list which has only the columns which are required for import
for macro in listOfHostMacros:
    for host in listOfHosts:
        if host["hostid"]==macro["hostid"]:
            row = {}
            row["hostName"] = host["hostName"]
            row["macro"] = macro["macro"]
            row["type"] = macro["type"]
            row["description"] = macro["description"]
            try:
                row["value"] = macro["value"]
            except:
                row["value"] = ""
            hostMacroWithHostName.append(row)
            break

# get list of interfaces. pick up only the "main" ones
listOfInterfaces = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
    "method": "hostinterface.get",
    "params": {
        "output": ["hostid","ip","dns","type","details","port","main"]},
"auth": token,"id": 1}), verify=False).text))[0].value

# rename elements in JSON tree to not conflict while mapping with other result
for interface in listOfInterfaces:

    # aggregate all interface addresses in one place

    # treat main interface in priority
    if interface["main"] == '1':

        interface["interface_dns"] = interface.pop("dns")
        interface["interface_ip"] = interface.pop("ip")
        interface["interface_details"] = interface.pop("details")
        interface["interface_type"] = interface.pop("type")
        interface["interface_port"] = interface.pop("port")
      
        # per SNMPv2/SNMPv3 the amount of columns differ, let's have them all in output
        if len(interface["interface_details"])>0:
            try:
                interface["community"] = interface["interface_details"]['community']
            except:
                interface["community"] = ""
            
            try:
                interface["authpassphrase"] = interface["interface_details"]['authpassphrase']
            except:
                interface["authpassphrase"] = ""

            try:
                interface["authprotocol"] = interface["interface_details"]['authprotocol']
            except:
                interface["authprotocol"] = ""

            try:
                interface["bulk"] = interface["interface_details"]['bulk']
            except:
                interface["bulk"] = ""

            try:
                interface["contextname"] = interface["interface_details"]['contextname']
            except:
                interface["contextname"] = ""

            try:
                interface["privpassphrase"] = interface["interface_details"]['privpassphrase']
            except:
                interface["privpassphrase"] = ""

            try:
                interface["privprotocol"] = interface["interface_details"]['privprotocol']
            except:
                interface["privprotocol"] = ""

            try:
                interface["securitylevel"] = interface["interface_details"]['securitylevel']
            except:
                interface["securitylevel"] = ""

            try:
                interface["securityname"] = interface["interface_details"]['securityname']
            except:
                interface["securityname"] = ""

            try:
                interface["version"] = interface["interface_details"]['version']
            except:
                interface["version"] = ""

            #destroy original entity
            interface.pop("interface_details")
        else:
            interface["community"] = ""
            interface["authpassphrase"] = ""
            interface["authprotocol"] = ""
            interface["bulk"] = ""
            interface["contextname"] = ""
            interface["privpassphrase"] = ""
            interface["privprotocol"] = ""
            interface["securitylevel"] = ""
            interface["securityname"] = ""
            interface["version"] = ""

            # destroy original entity
            interface.pop("interface_details")

# manually go through host list and add the columns which reflect interface details
for host in listOfHosts:
    interfaceExists = 0
    host.pop("groups")
    # iterate through interface
    for interface in listOfInterfaces:

        if host["hostid"]==interface["hostid"]:
            # transfer interface fiels to general host table
            host["community"] = interface["community"]
            host["authpassphrase"] = interface["authpassphrase"]
            host["authprotocol"] = interface["authprotocol"]
            host["bulk"] = interface["bulk"]
            host["contextname"] = interface["contextname"]
            host["privpassphrase"] = interface["privpassphrase"]
            host["privprotocol"] = interface["privprotocol"]
            host["securitylevel"] = interface["securitylevel"]
            host["securityname"] = interface["securityname"]
            host["version"] = interface["version"]
            host["interface_dns"] = interface["interface_dns"]
            host["interface_ip"] = interface["interface_ip"]
            host["interface_type"] = interface["interface_type"]
            host["interface_port"] = interface["interface_port"]
            interfaceExists = 1
            break

    if not interfaceExists:
        host["community"] = ""
        host["authpassphrase"] = ""
        host["authprotocol"] = ""
        host["bulk"] = ""
        host["contextname"] = ""
        host["privpassphrase"] = ""
        host["privprotocol"] = ""
        host["securitylevel"] = ""
        host["securityname"] = ""
        host["version"] = ""
        host["interface_dns"] = ""
        host["interface_ip"] = ""
        host["interface_type"] = ""
        host["interface_port"] = ""

# host list are prepared here

# if no argument of host group was specified
finalList = []
if not opts.group:
    finalList = listOfHosts

else:
    selectedHostGroupExists=0
    for selectedHostGroup in listOfHostGroups:
        if selectedHostGroup["name"] == opts.group:
            selectedHostGroupExists=1
            if len(selectedHostGroup["hosts"])>0:
                for selectedHost in selectedHostGroup["hosts"]:
                    for host in listOfHosts:
                        if host["hostid"] == selectedHost["hostid"]:
                            finalList.append(host)
            else:
                print("host group is empty")
            break

    if not selectedHostGroupExists:
        print("'"+opts.group+"' host group does not exist")

# write host list to a file
count = 0
for data in finalList:
    if count == 0:
        header = data.keys()
        csvHostList_writer.writerow(header)
        count += 1
    csvHostList_writer.writerow(data.values())

# write macro list to a file
count = 0
for data in hostMacroWithHostName:
        if count == 0:
            header = data.keys()
            csvMacroList_writer.writerow(header)
            count += 1
        csvMacroList_writer.writerow(data.values())

# close file for writing
hostListCSV.close()
macroListCSV.close()
