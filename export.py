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

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value
print(token)

# get list of hosts
listOfHosts = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output":["host","hostid","status","maintenance_status"],
        "selectItems": "count",
        "selectParentTemplates": ["name"],
        "selectTriggers": "count",
        "selectMacros": "extend"
        
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

listOfHostMacros = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "usermacro.get",
    "params": {
        "output": "extend"
    },
    "auth": token,
    "id": 1
    }), verify=False).text))[0].value

# rename elements in JSON tree to not conflict while mapping with other result
for item in listOfHosts:
  item["hostName"] = item.pop("host")
  item["hostStatus"] = item.pop("status")
  item["amountOfItems"] = item.pop("items")
  item["amountOfTriggers"] = item.pop("triggers")

  templateBundle=''
  if len(item["parentTemplates"])>0:
      print("there are",len(item["parentTemplates"]),"templates linked to ",item["hostName"])

      for idx,elem in enumerate(item["parentTemplates"]):
          templateBundle+=elem["name"]
          # if not last element
          if idx!=len(item["parentTemplates"])-1:
              templateBundle+=';'
  item["templateBundle"] = templateBundle
  # remove parentTemplates after parsing
  item.pop("parentTemplates")

  # count macros in output
  item["amountOfMacros"] = len(item.pop("macros"))

# get list of interfaces. pick up only the "main" ones
listOfInterfaces = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "hostinterface.get",
    "params": {
        "output": ["hostid","ip","dns","type","details","port"],
        "filter": {"main":1}
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value

# rename elements in JSON tree to not conflict while mapping with other result
for item in listOfInterfaces:
  item["interface_DNS"] = item.pop("dns")
  item["IP_address"] = item.pop("ip")
  item["interfaceDetails"] = item.pop("details")
  item["interfaceType"] = item.pop("type")
  item["interfacePort"] = item.pop("port")
  
  # per SNMPv2/SNMPv3 the amount of columns differ, let's have them all in output
  if len(item["interfaceDetails"])>0:
      print("there are extra details per interface",item.get("hostid"),", that is:",item["interfaceDetails"])
      try:
          item["authpassphrase"] = item["interfaceDetails"]['interfaceDetails']
      except:
          item["authpassphrase"] = ""
          
      try:
          item["authprotocol"] = item["interfaceDetails"]['authprotocol']
      except:
          item["authprotocol"] = ""

      try:
          item["bulk"] = item["interfaceDetails"]['bulk']
      except:
           item["bulk"] = ""

      try:
          item["contextname"] = item["interfaceDetails"]['contextname']
      except:
          item["contextname"] = ""

      try:
          item["privpassphrase"] = item["interfaceDetails"]['privpassphrase']
      except:
          item["privpassphrase"] = ""

      try:
          item["privprotocol"] = item["interfaceDetails"]['privprotocol']
      except:
          item["privprotocol"] = ""

      try:
          item["securitylevel"] = item["interfaceDetails"]['securitylevel']
      except:
          item["securitylevel"] = ""

      try:
          item["securityname"] = item["interfaceDetails"]['securityname']
      except:
          item["securityname"] = ""

      try:
          item["version"] = item["interfaceDetails"]['version']
      except:
          item["version"] = ""

      #destroy original entity
      item.pop("interfaceDetails")
  else:
      item["authpassphrase"] = ""
      item["authprotocol"] = ""
      item["bulk"] = ""
      item["contextname"] = ""
      item["privpassphrase"] = ""
      item["privprotocol"] = ""
      item["securitylevel"] = ""
      item["securityname"] = ""
      item["version"] = ""

      # destroy original entity
      item.pop("interfaceDetails")

# merge 2 different lists together. It works like a magic and automatically locates the column name to do the mapping
outcome = [json[0] | json[1] for json in zip(listOfHosts, listOfInterfaces)]
pprint(outcome)

macroList = [json[0] | json[1] for json in zip(listOfHostMacros,listOfHosts)]
# drop unnecessary columns
for item in macroList:
  item.pop("hostmacroid")
  item.pop("hostid")
  item.pop("type")
  item.pop("maintenance_status")
  item.pop("hostStatus")
  item.pop("amountOfItems")
  item.pop("amountOfTriggers")
  item.pop("amountOfMacros")

# write host list to a file
count = 0
for data in outcome:
    if count == 0:
        header = data.keys()
        csvHostList_writer.writerow(header)
        count += 1
    csvHostList_writer.writerow(data.values())

# write macro list to a file
count = 0
for data in macroList:
    if count == 0:
        header = data.keys()
        csvMacroList_writer.writerow(header)
        count += 1
    csvMacroList_writer.writerow(data.values())

# close file for writing
hostListCSV.close()
macroListCSV.close()
