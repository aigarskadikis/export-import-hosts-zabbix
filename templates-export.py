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
url = config.url_src_instance
user = config.username_src_instance
password = config.password_src_instance

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# format output better
from pprint import pprint

templateExportDir = '/root/ztemplates'

# prepare a file to write host list
templateListCSV = open('/tmp/templates.csv', 'w', newline='')
csvTemplateList_writer = csv.writer(templateListCSV)

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value
print(token)

# get list of templates
listOfTemplates = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "templateids": ["11999","13728","13641"],
        "output": ["host","templateid"],
        "selectGroups": "query"
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

# get all template groups. will be used later for mapping
ListOfGroups = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
        "jsonrpc": "2.0",
    "method": "hostgroup.get",
    "params": {
        "output": ["groupid","name"]
        },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

for item in listOfTemplates:
  item["TemplateName"] = item.pop("host")
  item["TemplateGroups"] = item.pop("groups")

  # go through every object name an execite additional configuration/template export function
  print(item["templateid"])

  # map template groups with name
  attachedTemplates = [json[0] | json[1] for json in zip(item["TemplateGroups"], ListOfGroups)]
  pprint(attachedTemplates)

  # create a new file for writing
  f = open( templateExportDir + '/' + item["templateid"]+'.xml', "a")

  # put template XML content in variable for later analysis
  xmlTemplate = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
   "jsonrpc": "2.0",
    "method": "configuration.export",
    "params": {
        "options": {
            "templates": [
               item["templateid"]
            ]
        },
        "format": "xml"
    },
    "auth": token,
    "id": 1
          }), verify=False).text))[0].value
  
  # write XML tempate content in file
  f.write(xmlTemplate)
  f.close()

# write host list to a file
count = 0
for data in listOfTemplates:
    if count == 0:
        header = data.keys()
        csvTemplateList_writer.writerow(header)
        count += 1
    csvTemplateList_writer.writerow(data.values())

# close file for writing
templateListCSV.close()
