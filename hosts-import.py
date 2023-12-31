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

import optparse
parser=optparse.OptionParser()
parser.add_option('-d','--directory',help='give a directory for hosts.csv, macros.csv')
(opts,args) = parser.parse_args()

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# format output better
from pprint import pprint

if not opts.directory:
    print("give a directory where the import files are located. for example:")
    print("./hosts-import.py -d '/tmp/csv/Linux servers'")
    exit(1)

# assing CSV for reading
listOfHostsCSV = open(os.path.join(opts.directory,'hosts.csv'),'rt', encoding='utf-8')
# convert to python native list
listOfHosts = list(csv.DictReader(listOfHostsCSV))

listOfHostMacrosCSV = open(os.path.join(opts.directory,'macros.csv'),'rt', encoding='utf-8')
# convert to python native list
listOfHostMacros = list(csv.DictReader(listOfHostMacrosCSV))

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'), verify=False)

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
}).encode('utf-8'), verify=False).text))[0].value

# existing templates
listOfExistingTemplates = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "output":["host","templateid"]
    },
    "auth": token,
    "id": 1
}).encode('utf-8'), verify=False).text))[0].value

# take new host
for newHost in listOfHosts:
    # by default lets assume host does not exist in destination
    hostExists=0
    # cehck if this host name already exists in destination. copmare 1 hostname with all hostnames in destination
    for existingHost in listOfExistingHosts:
        if existingHost["host"]==newHost["host"]:
            hostExists=1
            break

    if hostExists:
        print(bcolors.OKGREEN + "'" + newHost["host"] + "', "+ bcolors.ENDC,end='', flush=True)
    else:
        if newHost["main"] == '1':
            # need to register new host
            #print(bcolors.WARNING + "host '"+newHost["host"] + "' is not yet registred. will register it now"+bcolors.ENDC)

            # define new list of macros which is about to be installed on this host
            newHostMacros = []

            # there can be mulitple lines in the list which match hostname
            for macro in listOfHostMacros:
                #print(macro["macro"])
                if macro["hostName"] == newHost["host"]:
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
            #print("template names which needs to be attached to this host:",templatesToAdd)

            # keep in track tmeplate IDs to add
            templateIDsToAdd = []

            # if template list is not empty
            if (len(newHost["templateBundle"]) > 0 and len(templatesToAdd) > 0):
                #print("analyze templates which needs to be linked to new host")
                # analyze what is inside


                # set flag to measure if all dependencies for host is completed
                allTemplatesExist=1

                for oneOfTemplatesToAdd in templatesToAdd:
                    # lets assume this template does not exist in destination
                    templateIdInDestination = 0
                    # go through all templates and look up if template exists
                    for existingTemplate in listOfExistingTemplates:
                        if existingTemplate["host"] == oneOfTemplatesToAdd:
                            templateIdInDestination = existingTemplate["templateid"]
                    #print(templateIDsToAdd)
                    
                    # if api reported a non-empty output, the template ID exists.
                    if not templateIdInDestination == 0:
                        # add template to list which be attached to host object
                        row = {}
                        row["templateid"] = templateIdInDestination
                        templateIDsToAdd.append(row)
                        
                    else:

                        # check in file system if such template object exists
                        
                        try:
                            with open(locationOfTemplateBundles+'/'+oneOfTemplatesToAdd+'.xml', 'r', encoding='utf-8') as file:
                                templateXMLtoImport = file.read().replace('\n', '')

                                uploadTemplatePayload=json.dumps({"jsonrpc":"2.0",
                                    "method":"configuration.import",
                                    "params":{
                                        "format":"xml",
                                        "rules":{
                                            "groups":{"createMissing":True,"updateExisting":True},
                                            "templates":{"createMissing":True,"updateExisting":True},
                                            "valueMaps":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "templateDashboards":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "templateLinkage":{"createMissing":True,"deleteMissing":False},
                                            "items":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "discoveryRules":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "triggers":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "graphs":{"createMissing":True,"updateExisting":True,"deleteMissing":True},
                                            "httptests":{"createMissing":True,"updateExisting":True,"deleteMissing":True}
                                            },
                                        "source": templateXMLtoImport},
                                    "auth":token,"id":1})

                                # this is to troubleshoot if API call does not work
                                #print(uploadTemplatePayload)
                                outputOfUpload = parse('$.result').find(json.loads(requests.request("POST",url,headers=headers,data=uploadTemplatePayload.encode('utf-8'),verify=False).text))[0].value
    #                            print(outputOfUpload)

                                # do a follow up and check if template exists, pick up tamplate ID
                                #sleep(1000)
                                newTemplateID = parse('$.result').find(json.loads(requests.request("POST",url,headers=headers,data=json.dumps({"jsonrpc":"2.0",
                                    "method":"template.get",
                                    "params":{
                                        "output":["templateid","host"],
                                        "search":{"host":oneOfTemplatesToAdd},
                                        "searchWildcardsEnabled":1
                                        },
    "auth":token,"id":1}).encode('utf-8'),verify=False).text))[0].value

                                try:
                                    # add new template name to virtual list
                                    row = {}
                                    row["host"] = oneOfTemplatesToAdd
                                    row["templateid"] = newTemplateID[0]["templateid"]
                                    print("new template '"+newTemplateID[0]["host"]+"', ",end='', flush=True)
                                    listOfExistingTemplates.append(row)
                                except:
                                    print("cannot add variable to global templates list for destination")

                                try:
                                    row = {}
                                    row["templateid"] = newTemplateID[0]["templateid"]
                                    templateIDsToAdd.append(row)
                                except:
                                    print("cannot prepare template list payload for host.create function")


                        except:
                            print(bcolors.FAIL +"import template '"+ oneOfTemplatesToAdd  + "' failed, therefore cannot register host '"+newHost["host"]+". try manually importing '"+ locationOfTemplateBundles+'/'+oneOfTemplatesToAdd+".xml', and rerun script. "+ bcolors.ENDC,end='', flush=True)
                            allTemplatesExist=0

            if allTemplatesExist == 1:
                if newHost["type"]=='1':
                    try:
                        # create a Zabbix agent host
                        parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc":"2.0",
                            "method":"host.create",
                            "params":{
                                "host":newHost["host"],
                                "interfaces":[{
                                    "type":1,
                                    "main":1,
                                    "useip":1,
                                    "ip":newHost["ip"],
                                    "dns":newHost["dns"],
                                    "port":newHost["port"]}],
                                "groups":[{"groupid":"5"}],
                                "macros":newHostMacros,
                                "templates":templateIDsToAdd
                                },
                        "auth": token,"id":1}).encode('utf-8'),verify=False).text))[0].value
                        print("new ZBX host '"+newHost["host"]+"', ",end='', flush=True)
                    except:
                        print("unable to create ZBX host")

                    
                elif newHost["type"]=='2':
                    #print("new host is SNMP")
                    # this is SNMP host. Need to check version

                    if newHost["version"]=='2':
                        # this is SNMPv2 host
                        try:
                            # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                            parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
                                "method":"host.create",
                                "params":{
                                    "host":newHost["host"],"interfaces":[{
                                        "type":2,
                                        "main":1,
                                        "useip":1,
                                        "ip":newHost["ip"],
                                        "dns":newHost["dns"],
                                        "port":newHost["port"],
                                        "details":{
                                            "community":newHost["community"],
                                            "bulk":newHost["bulk"],
                                            "version":newHost["version"]}}],
                                    "groups":[{"groupid":"5"}],
                                    "macros":newHostMacros,
                                    "templates":templateIDsToAdd},
                            "auth": token,"id": 1}).encode('utf-8'), verify=False).text))[0].value
                            print("new SNMPv2 host '"+newHost["host"]+"', ",end='', flush=True)
                        except:
                            print("unable to create SNMPv2 host")

                    elif newHost["version"]=='3':
                        # this is SNMPv3 host
                        try:
                            # create a SNMPv3 host. SNMPv3 host has 9 characteristics
                            parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
                                "method":"host.create",
                                "params":{
                                    "host":newHost["host"],"interfaces":[{
                                        "type":2,
                                        "main":1,
                                        "useip":1,
                                        "ip":newHost["ip"],
                                        "dns":newHost["dns"],
                                        "port":newHost["port"],
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
                                        "macros":newHostMacros,
                                        "templates":templateIDsToAdd
                                        },
                            "auth":token,"id":1}).encode('utf-8'),verify=False).text))[0].value
                            print("new SNMPv3 host '"+newHost["host"]+"', ",end='', flush=True)
                        except:
                            print("unable to create SNMPv3 host")
                    else:
                        unknownSNMPversion=1

                # check if this is ZBX host
                elif newHost["type"]=='4':
                    try:
                        # create a Zabbix agent host
                        parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc":"2.0",
                            "method":"host.create",
                            "params":{
                                "host":newHost["host"],
                                "interfaces":[{
                                    "type":4,
                                    "main":1,
                                    "useip":1,
                                    "ip":newHost["ip"],
                                    "dns":newHost["dns"],
                                    "port":newHost["port"]}],
                                "groups":[{"groupid":"5"}],
                                "macros":newHostMacros,
                                "templates":templateIDsToAdd
                                },
                        "auth": token,"id":1}).encode('utf-8'),verify=False).text))[0].value
                        print("new JMX host '"+newHost["host"]+"', ",end='', flush=True)
                    except:
                        print("unable to create JMX host")
                else:
                    print("this is not ZBX, not SNMP, not JMX host")
            else:
                #print("not all templates are ready. skipping regitration per '",newHost["host"],"', enable 'print(uploadTemplatePayload)' and simulate JSON via Postman")
                #print()
                a=1



print()
listOfHostsCSV.close()
listOfHostMacrosCSV.close()

