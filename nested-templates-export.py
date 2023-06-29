#!/bin/env python3.9
import sys
sys.path.insert(0,'/var/lib/zabbix')
import config

# to automatically make directories via python
import os

# work with Zabbix API JSON RPC
# pip3.9 install requests
import requests
import json

# supress warnings in case of self signed certificate:
# /usr/local/lib/python3.9/site-packages/urllib3/connectionpool.py:1095: InsecureRequestWarning: Unverified HTTPS request is being made to host 'zabbix.aigarskadikis.com'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
import urllib3
urllib3.disable_warnings()

# shortify vairables
url = config.url_src_instance
user = config.username_src_instance
password = config.password_src_instance
csv_export_dir = config.csv_export_dir

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# format output better
from pprint import pprint

templateExportDir = config.zabbix_templates_export_dir
# create a sub directory 'all'
try:
    os.makedirs(os.path.join(templateExportDir,'nested'))
except:
    cannotMakeDir = 1

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value



# listing all hosts and attached master templates
listOfHostsHavingTemplates = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output": ["parentTemplates","host","hostid"],
        "selectParentTemplates": "query"
    },
    "auth": token,
    "id": 1
    }), verify=False).text))[0].value

#pprint(listOfHostsHavingTemplates)

# iterate through hosts
for host in listOfHostsHavingTemplates:
    # if this host has some templates
    if len(host["parentTemplates"])>0:
        # inform this host is having templates
        print(host["host"]+" is having",len(host["parentTemplates"]),"master templates")
        pprint(host["parentTemplates"])
        # go through parent templates one by one
        for templateid in host["parentTemplates"]:
            # set an empty todo list
            todo = []
            # set an empty array
            templatesToExport = []
            # add parrent to archive
            templatesToExport.append(templateid["templateid"])
            # add parrent to todo list for analisis
            todo.append(templateid["templateid"])

            # analyze the rest of templates
            print("there is a todo list to go through")
            while len(todo)>0:
                dependencies = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
                    "jsonrpc": "2.0","method": "template.get","params": {
				"templateids": todo[0],	"output": ["host","parentTemplates"],"selectParentTemplates":"query" }, "auth": token,  "id": 1
    }), verify=False).text))[0].value
                todo.remove(todo[0])

                for p in dependencies:
                    if len(p["parentTemplates"])>0:
                        for n in p["parentTemplates"]:
                            todo.append(n["templateid"])
                            templatesToExport.append(n["templateid"])
            print("total amount of templates to export per '"+templateid["templateid"]+"' is: ")
            print(templatesToExport)

            # export template bundle
            xmlTemplateBundle = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
   "jsonrpc": "2.0",
    "method": "configuration.export",
    "params": { "options": { "templates": templatesToExport },
        "format": "xml"
    },
    "auth": token,
    "id": 1
          }), verify=False).text))[0].value

            path = os.path.join(templateExportDir,templateid["templateid"])
            f = open( templateExportDir + '/nested/' + templateid["templateid"] + '.xml', "w")
            f.write(xmlTemplateBundle)
            f.close()




