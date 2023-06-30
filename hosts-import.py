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

templateExportDir = config.zabbix_templates_export_dir

locationOfTemplateBundles = os.path.join(templateExportDir,'nested')

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

# assing CSV for reading
listOfHostsCSV = open(csv_export_dir+'/hosts.csv','rt')
# convert to python native list
listOfHosts = list(csv.DictReader(listOfHostsCSV))

listOfHostMacrosCSV = open(csv_export_dir+'/macros.csv','rt')
# convert to python native list
listOfHostMacros = list(csv.DictReader(listOfHostMacrosCSV))


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

# existing templates
listOfExistingTemplates = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "output":["host","templateid"]
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

# take new host
for newHost in listOfHosts:
    # by default lets assume host does not exist in destination
    hostExists=0
    # cehck if this host name already exists in destination. copmare 1 hostname with all hostnames in destination
    for existingHost in listOfExistingHosts:
        if existingHost["host"]==newHost["hostName"]:
            hostExists=1
            break

    if hostExists:
        #print(bcolors.OKGREEN + "'" + newHost["hostName"] + "' already exists in destination"+ bcolors.ENDC)
        already=1
    else:
        # need to register new host
        print(bcolors.FAIL + "host '"+newHost["hostName"] + "' is not yet registred. will register it now:")

        # define new list of macros which is about to be installed on this host
        newHostMacros = []

        # there can be mulitple lines in the list which match hostname
        for macro in listOfHostMacros:
            #print(macro["macro"])
            if macro["hostName"] == newHost["hostName"]:
                #print("found one matching line in macros.csv")
                # a host can have multiple macros
                row = {}
                # all columns must exist in CSV
                row["macro"] = macro["macro"]
                row["description"] = macro["description"]
                row["value"] = macro["value"]
                row["type"] = macro["type"]
                newHostMacros.append(row)

        # pick up template bundle
        templatesToAdd = newHost["templateBundle"].split(';')
        print("template names which needs to be attached to this host:",templatesToAdd)

        # keep in track tmeplate IDs to add
        templateIDsToAdd = []

        # if template list is not empty
        if len(templatesToAdd)>0:
            print("analyze templates which needs to be linked to new host")
            # analyze what is inside
            for oneOfTemplatesToAdd in templatesToAdd:
                # lets assume this template does not exist in destination
                templateIdInDestination = 0
                # go through all templates and look up if template exists
                for existingTemplate in listOfExistingTemplates:
                    if existingTemplate["host"] == oneOfTemplatesToAdd:
                        templateIdInDestination = existingTemplate["templateid"]
                
                print(templateIdInDestination)
                # if api reported a non-empty output, the template ID exists.
                if templateIdInDestination:
                    # add template to list which be attached to host object
                    templateIDsToAdd.append(templateIdInDestination)
                else:
                    print("template '"+oneOfTemplatesToAdd+"' not found. will import it now..")

                    # check in file system if such template object exists
                    try:
                        with open(locationOfTemplateBundles+'/'+oneOfTemplatesToAdd+'.xml', 'r') as file:
                            templateXMLtoImport = file.read().replace('\n', '')

                            payload=json.dumps({"jsonrpc":"2.0",
                                "method":"configuration.import",
                                "params":{
                                    "format":"xml",
                                    "rules":{
                                        "groups":{"createMissing":True,"updateExisting":True},
                                        "templates":{"createMissing":True,"updateExisting":True},
                                        "items":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                        "triggers":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                        "valueMaps":{"createMissing":True,"updateExisting":True}
                                        },
                                    "source": templateXMLtoImport},
                                "auth":token,"id":1})
                            print(parse('$.result').find(json.loads(requests.request("POST",url,headers=headers,data=payload,verify=False).text))[0].value)

                            # do a follow up and check if template exists, pick up tamplate ID
                            newTemplateID = parse('$.result').find(json.loads(requests.request("POST",url,headers=headers,data=json.dumps({"jsonrpc":"2.0",
                                "method":"template.get",
                                "params":{
                                    "output":["templateid"],
                                    "search":{"host":oneOfTemplatesToAdd},
                                    "searchWildcardsEnabled":1
                                    },
"auth":token,"id":1}),verify=False).text))[0].value
                            print(newTemplateID)

                            templateIDsToAdd.append(newTemplateID[0]["templateid"])

                            # add new template name to virtual list
                            row = {}
                            row["host"] = oneOfTemplatesToAdd
                            row["templateid"] = newTemplateID
                            listOfExistingTemplates.append(row)

                    except:
                        print("cannot find file in file system or API call fails")


        # check if this is ZBX host
        if newHost["interface_type"]=='1':
            try:
                # create a Zabbix agent host
                print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc":"2.0",
                    "method":"host.create",
                    "params":{
                        "host":newHost["hostName"],
                        "interfaces":[{
                            "type":1,
                            "main":1,
                            "useip":1,
                            "ip":newHost["interface_ip"],
                            "dns":newHost["interface_dns"],
                            "port":newHost["interface_port"]}],
                        "groups":[{"groupid":"5"}],
                        "macros":newHostMacros
                        },
                "auth": token,"id":1}),verify=False).text))[0].value)
            except:
                print("unable to create ZBX host")

            
        elif newHost["interface_type"]=='2':
            print("new host is SNMP")
            # this is SNMP host. Need to check version

            if newHost["version"]=='2':
                # this is SNMPv2 host
                try:
                    # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                    print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
                        "method":"host.create",
                        "params":{
                            "host":newHost["hostName"],"interfaces":[{
                                "type":2,
                                "main":1,
                                "useip":1,
                                "ip":newHost["interface_ip"],
                                "dns":newHost["interface_dns"],
                                "port":newHost["interface_port"],
                                "details":{
                                    "community":newHost["community"],
                                    "bulk":newHost["bulk"],
                                    "version":newHost["version"]}}],
                            "groups":[{"groupid":"5"}],
                            "macros":newHostMacros},
                    "auth": token,"id": 1}), verify=False).text))[0].value)
                    existingHostsList.append(newHost["hostName"])
                except:
                    print("unable to create SNMPv2 host")

            elif newHost["version"]=='3':
                # this is SNMPv3 host
                try:
                    # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                    print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
                        "method":"host.create",
                        "params":{
                            "host":newHost["hostName"],"interfaces":[{
                                "type":2,
                                "main":1,
                                "useip":1,
                                "ip":newHost["interface_ip"],
                                "dns":newHost["interface_dns"],
                                "port":newHost["interface_port"],
                                "details":{
                                    "version":newHost["version"],
                                    "bulk":newHost["bulk"],
                                    "securityname":newHost["securityname"],
                                    "contextname":newHost["contextname"],
                                    "securitylevel":newHost["securitylevel"],
                                    "authpassphrase":newHost["authpassphrase"],
                                    "authprotocol":newHost["authprotocol"],
                                    "privpassphrase":newHost["privpassphrase"],
                                    "privprotocol":newHost["privprotocol"]}}],
                                "groups":[{"groupid":"5"}],
                                "macros":newHostMacros
                                },
                    "auth":token,"id":1}),verify=False).text))[0].value)
                    existingHostsList.append(newHost["hostName"])
                except:
                    print("unable to create SNMPv3 host")
            else:
                unknownSNMPversion=1

        # check if this is ZBX host
        elif newHost["interface_type"]=='4':
            try:
                # create a Zabbix agent host
                print(parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc":"2.0",
                    "method":"host.create",
                    "params":{
                        "host":newHost["hostName"],
                        "interfaces":[{
                            "type":4,
                            "main":1,
                            "useip":1,
                            "ip":newHost["interface_ip"],
                            "dns":newHost["interface_dns"],
                            "port":newHost["interface_port"]}],
                        "groups":[{"groupid":"5"}],
                        "macros":newHostMacros
                        },
                "auth": token,"id":1}),verify=False).text))[0].value)
            except:
                print("unable to create JMX host")
        else:
            print("this is not ZBX, not SNMP, not JMX host")

listOfHostsCSV.close()
listOfHostMacrosCSV.close()

