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
#print(token)

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
      #print("there are",len(item["parentTemplates"]),"templates linked to ",item["hostName"])

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

print(hostMacroWithHostName)


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
  item["interface_dns"] = item.pop("dns")
  item["interface_ip"] = item.pop("ip")
  item["interface_details"] = item.pop("details")
  item["interface_type"] = item.pop("type")
  item["interface_port"] = item.pop("port")
  
  # per SNMPv2/SNMPv3 the amount of columns differ, let's have them all in output
  if len(item["interface_details"])>0:
      #print("there are extra details per interface",item.get("hostid"),", that is:",item["interface_details"])
      try:
          item["community"] = item["interface_details"]['community']
      except:
          item["community"] = ""

      try:
          item["authpassphrase"] = item["interface_details"]['authpassphrase']
      except:
          item["authpassphrase"] = ""
          
      try:
          item["authprotocol"] = item["interface_details"]['authprotocol']
      except:
          item["authprotocol"] = ""

      try:
          item["bulk"] = item["interface_details"]['bulk']
      except:
           item["bulk"] = ""

      try:
          item["contextname"] = item["interface_details"]['contextname']
      except:
          item["contextname"] = ""

      try:
          item["privpassphrase"] = item["interface_details"]['privpassphrase']
      except:
          item["privpassphrase"] = ""

      try:
          item["privprotocol"] = item["interface_details"]['privprotocol']
      except:
          item["privprotocol"] = ""

      try:
          item["securitylevel"] = item["interface_details"]['securitylevel']
      except:
          item["securitylevel"] = ""

      try:
          item["securityname"] = item["interface_details"]['securityname']
      except:
          item["securityname"] = ""

      try:
          item["version"] = item["interface_details"]['version']
      except:
          item["version"] = ""

      #destroy original entity
      item.pop("interface_details")
  else:
      item["community"] = ""
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
      item.pop("interface_details")


# manually go through host list and add the columns which reflect interface details
for host in listOfHosts:
    interfaceExists = 0
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

#pprint(listOfHostMacros)

# write host list to a file
count = 0
for data in listOfHosts:
    if count == 0:
        header = data.keys()
        csvHostList_writer.writerow(header)
        count += 1
    csvHostList_writer.writerow(data.values())

#pprint(listOfHostMacros)

# write macro list to a file
count = 0
for data in hostMacroWithHostName:
        if count == 0:
            header = data.keys()
            csvMacroList_writer.writerow(header)
            count += 1
        csvMacroList_writer.writerow(data.values())
        #csvMacroList_writer.writerow(header)
        #print(data.values())

# close file for writing
hostListCSV.close()
macroListCSV.close()
