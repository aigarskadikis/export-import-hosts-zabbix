#!/bin/env python3.9

# cat /var/lib/zabbix/config.py
# url = "http://127.0.0.1/api_jsonrpc.php"
# username = "Admin"
# password = "zabbix"

import sys
sys.path.insert(0,'/var/lib/zabbix')
import config

# to support arguments
import optparse

parser=optparse.OptionParser()

# import options

parser.add_option('-g','--templategroup',help='give a host group')
parser.add_option('-l','--limit',help='limit the call',type=int)

(opts,args) = parser.parse_args() # instantiate parser

# if limit was defined then override
if opts.limit:
    if not opts.templategroup:
        limit=opts.limit
    else:
        limit=99999
else:
    limit=99999


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
    os.makedirs(os.path.join(templateExportDir,'all'))
except:
    cannotMakeDir = 1

# prepare a file to write template list
templateListCSV = open(os.path.join(csv_export_dir, 'templates.csv'), 'w', newline='')
csvTemplateList_writer = csv.writer(templateListCSV)

# pick up token which will be used latter in script
payload = json.dumps({"jsonrpc":"2.0","method":"user.login","params":{"user":user,"password":password},"id":1})
headers = {'Content-Type': 'application/json'}

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

#print(response.text)
token = parse('$.result').find(json.loads(response.text))[0].value

# get list of templates
listOfTemplates = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "output": ["host","templateid"],
        "selectGroups": "query",
        "limit": limit
    },
    "auth": token,
    "id": 1
}), verify=False).text))[0].value


ListOfGroups = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({
             "jsonrpc": "2.0",
             "method": "hostgroup.get",
             "params": {
                 "output": ["groupid","name","templates"],
                 "selectTemplates":"query"},
             "auth": token,"id": 1}), verify=False).text))[0].value

if opts.templategroup:
    for hg in ListOfGroups:
        if hg["name"] == opts.templategroup:
            if len(hg["templates"]) > 0:
                print("total amount of templates to export:",len(hg["templates"]))
                for t in hg["templates"]:
                    # look up template name
                    for n in listOfTemplates:
                        if t["templateid"] == n["templateid"]:
                            templateName = n["host"]
                            #print(templateName)
                            break

                    print(t["templateid"]+' ',end='', flush=True)

                    # put template XML content in variable
                    xmlTemplate = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc":"2.0",
                        "method":"configuration.export","params":{"options":{"templates":[t["templateid"]]},"format": "xml"},
                        "auth": token,"id": 1}), verify=False).text))[0].value
                    for templateGroup in n["groups"]:
                        for globalGroup in ListOfGroups:
                            if templateGroup["groupid"]==globalGroup["groupid"]:
                                path = os.path.join(templateExportDir,globalGroup["name"])
                                try:
                                    os.makedirs(path)
                                except:
                                    cannotMakeDir = 1
                                f = open(  templateExportDir + '/' + globalGroup["name"] + '/' +n["host"]+'.xml', "w")
                                f.write(xmlTemplate)
                                f.close()
                    

            else:
                print("template group '"+hg["name"]+"' has been found but not templates inside")

else:
    print("total amount of templates to export:",len(listOfTemplates))

    # transform naming of listOfTemplates
    for template in listOfTemplates:

        # go through every object name an execute additional configuration/template export function
        print(template["templateid"]+' ',end='', flush=True)
        
        # put template XML content in variable
        xmlTemplate = parse('$.result').find(json.loads(requests.request("POST", url, headers=headers, data=json.dumps({"jsonrpc": "2.0",
            "method":"configuration.export","params": { "options": { "templates": [ template["templateid"] ] },"format": "xml" },
            "auth": token,"id": 1}), verify=False).text))[0].value
        
        # if template belongs to multiple template groups then create multiple directories
        for templateGroup in template["groups"]:
            # take template group id and find the template group name
            for globalGroup in ListOfGroups:
                # look up the mapping
                if templateGroup["groupid"]==globalGroup["groupid"]:
                    # calculate the destionation directory based on template group name
                    path = os.path.join(templateExportDir,globalGroup["name"])
                    # make sure directory exists
                    try:
                        os.makedirs(path)
                    except:
                        cannotMakeDir = 1
                    # open file for writing
                    f = open(  templateExportDir + '/' + globalGroup["name"] + '/' +template["host"]+'.xml', "w")
                    # write XML tempate content in file
                    f.write(xmlTemplate)
                    # close file
                    f.close()
        
        # there will be one single directory too to have all template objects in one place
        f = open(  templateExportDir + '/all/' + template["host"]+'.xml', "w")
        f.write(xmlTemplate)
        f.close()

print("")
print("to explore outcome use commands:")
print("tree",templateExportDir)
print("find",templateExportDir,"-type f")

count = 0
for data in listOfTemplates:
    if count == 0:
        header = data.keys()
        csvTemplateList_writer.writerow(header)
        count += 1
    csvTemplateList_writer.writerow(data.values())

    # close file for writing
templateListCSV.close()
