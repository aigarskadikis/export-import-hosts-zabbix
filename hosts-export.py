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

print()
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
                "selectDiscoveries": "extend",
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
                "selectDiscoveries": "count",
                "selectInterfaces": "extend",
                "selectMacros": "extend",
                "selectGroups":"extend"},
            "auth": token, "id": 1}), verify=False).text))[0].value

if len(listOfHosts) > 0:

    for data in listOfHosts:
        # calculate few extra fields
        data["amountOfMacros"] = len(data["macros"])
        data["amountOfInterfaces"] = len(data["interfaces"])

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
                # table 'hosts'
                row["hostid"] = host["hostid"]
                row["host"] = host["host"]
                row["status"] = host["status"]
                row["maintenance_status"] = host["maintenance_status"]

                # custom
                row["templateBundle"] = templateBundle
                row["allGroups"] = hostGroupBundle
                row["amountOfMacros"] = host["amountOfMacros"]
                row["items"] = host["items"]
                row["triggers"] = host["triggers"]
                row["discoveries"] = len(host["discoveries"])
                row["amountOfInterfaces"] = host["amountOfInterfaces"]

                # 7 fields from table 'interfaces'

                try:
                    row["interfaceid"] = interface["interfaceid"]
                except:
                    row["interfaceid"] = ""

                try:
                    row["main"] = interface["main"]
                except:
                    row["main"] = ""

                try:
                    row["type"] = interface["type"]
                except:
                    row["type"] = ""

                try:
                    row["useip"] = interface["useip"]
                except:
                    row["useip"] = ""

                try:
                    row["ip"] = interface["ip"]
                except:
                    row["ip"] = ""

                try:
                    row["dns"] = interface["dns"]
                except:
                    row["dns"] = ""

                try:
                    row["port"] = interface["port"]
                except:
                    row["port"] = ""

                # 10 fields from table 'interface_snmp'
                if len(interface["details"])>0:

                    try:
                        row["community"] = interface["details"]['community']
                    except:
                        row["community"] = ""
                    
                    try:
                        row["authpassphrase"] = interface["details"]['authpassphrase']
                    except:
                        row["authpassphrase"] = ""

                    try:
                        row["authprotocol"] = interface["details"]['authprotocol']
                    except:
                        row["authprotocol"] = ""

                    try:
                        row["bulk"] = interface["details"]['bulk']
                    except:
                        row["bulk"] = ""

                    try:
                        row["contextname"] = interface["details"]['contextname']
                    except:
                        row["contextname"] = ""

                    try:
                        row["privpassphrase"] = interface["details"]['privpassphrase']
                    except:
                        row["privpassphrase"] = ""

                    try:
                        row["privprotocol"] = interface["details"]['privprotocol']
                    except:
                        row["privprotocol"] = ""

                    try:
                        row["securitylevel"] = interface["details"]['securitylevel']
                    except:
                        row["securitylevel"] = ""

                    try:
                        row["securityname"] = interface["details"]['securityname']
                    except:
                        row["securityname"] = ""

                    try:
                        row["version"] = interface["details"]['version']
                    except:
                        row["version"] = ""

                dataInOutput.append(row)

        else:
            row = {}
            # table 'hosts'
            row["hostid"] = host["hostid"]
            row["host"] = host["host"]
            row["status"] = host["status"]
            row["maintenance_status"] = host["maintenance_status"]

            # 6 custom fields
            row["templateBundle"] = templateBundle
            row["allGroups"] = hostGroupBundle
            row["amountOfMacros"] = host["amountOfMacros"]
            row["items"] = host["items"]
            row["triggers"] = host["triggers"]
            row["discoveries"] = len(host["discoveries"])
            row["amountOfInterfaces"] = host["amountOfInterfaces"]

            # characteritics from table 'interfaces'. 7 fields
            row["interfaceid"] = ""
            row["main"] = ""
            row["type"] = ""
            row["useip"] = ""
            row["ip"] = ""
            row["dns"] = ""
            row["port"] = ""

            # characteristics from table 'interface_snmp'
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

            dataInOutput.append(row)


if len(listOfHostGroups) > 0:
    print("creating hosts.csv, macros.csv into:")
    for group in listOfHostGroups:
        # if there are any hosts inside in this group
        if len(group["hosts"]) > 0:
            # create a short list of all hostid in this host group
            hostIDsInGroup = []
            for id in group["hosts"]:
                hostIDsInGroup.append(id["hostid"])

            # make sure a subdirectory of host group name exists
            try:
                os.makedirs(os.path.join(csv_export_dir, group["name"]))
            except:
                cannotMakeHostGroupDir = 1

            print("'"+os.path.join(csv_export_dir, group["name"])+"', ",end='', flush=True)



            # order on writing hosts.csv, macros.csv is important. first must be macros as it will drop "macros" column when done
            macrosCSV = open(os.path.join(csv_export_dir, group["name"], 'macros.csv'), 'w', newline='')
            csvMacrosList_writer = csv.writer(macrosCSV)
            
            macrosHeaderYes = 0
            for data in listOfHosts:
                if data["hostid"] in hostIDsInGroup:
                    # if there are macros defined on this host
                    if len(data["macros"]) > 0:
                        for macro in data["macros"]:
                            macro["hostName"] = data["host"]
                            if macrosHeaderYes == 0:
                                header = macro.keys()
                                csvMacrosList_writer.writerow(header)
                                macrosHeaderYes += 1
                            csvMacrosList_writer.writerow(macro.values())
                        

            macrosCSV.close()


            hostCSV = open(os.path.join(csv_export_dir, group["name"], 'hosts.csv'), 'w', newline='')
            csvHostList_writer = csv.writer(hostCSV)

            # order on writing hosts.csv, macros.csv is important. first must be macros as it will drop "macros" column when done
            count = 0
            for data in dataInOutput:
                if count == 0:
                    header = data.keys()
                    csvHostList_writer.writerow(header)
                    count += 1
                if data["hostid"] in hostIDsInGroup:
                    csvHostList_writer.writerow(data.values())

            hostCSV.close()

# rewrite all host macros in one CSV
macrosCSV = open(os.path.join(csv_export_dir,'macros.csv'), 'w', newline='')
csvMacrosList_writer = csv.writer(macrosCSV)
macrosHeaderYes = 0
for data in listOfHosts:
    # if there are macros defined on this host
    if len(data["macros"]) > 0:
        for macro in data["macros"]:
            macro["hostName"] = data["host"]
            if macrosHeaderYes == 0:
                header = macro.keys()
                csvMacrosList_writer.writerow(header)
                macrosHeaderYes += 1
            csvMacrosList_writer.writerow(macro.values())
macrosCSV.close()

# rewrite all hosts in one CSV
hostCSV = open(os.path.join(csv_export_dir, 'hosts.csv'), 'w', newline='')
csvHostList_writer = csv.writer(hostCSV)

count = 0
for data in dataInOutput:
    if count == 0:
        header = data.keys()
        csvHostList_writer.writerow(header)
        count += 1
    csvHostList_writer.writerow(data.values())
hostCSV.close()

print()
print()
print("it's time to run:")
print("./nested-templates-export.py")
print()
print("after that, to import all hosts on destination use: ")
print("./hosts-import.py -d '"+csv_export_dir+"'")
print()
