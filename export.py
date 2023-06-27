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
url = config.url
user = config.username
password = config.password

# have support for JSON path
# pip3.9 install jsonpath-ng
import json
from jsonpath_ng import jsonpath, parse

# support for CSV export and import
import csv

# format output better
from pprint import pprint

# prepare a file to write
data_file = open('/tmp/hosts.csv', 'w', newline='')
csv_writer = csv.writer(data_file)


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

# rename elements in JSON tree to not conflict while mapping with other result
for item in listOfHosts:
  item["hostName"] = item.pop("host")
  item["hostStatus"] = item.pop("status")
  item["amountOfItems"] = item.pop("items")
  item["amountOfTriggers"] = item.pop("triggers")
  if len(item["parentTemplates"])>0:
      print("there are",len(item["parentTemplates"]),"templates linked to ",item["hostName"])
  # remove parentTemplates. This step does not make sence. It's temporary to have a clean output
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

# write output to file
count = 0
for data in outcome:
    if count == 0:
        header = data.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(data.values())

# close file for writing
data_file.close()

