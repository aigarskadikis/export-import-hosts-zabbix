# Export list of host objects to CSV

Export list of host objects, host level macros from Zabbix 5.0 and import into Zabbix 6.0

## Features

* Python 3.9 compatible
* Credentials in separate file. /var/lib/zabbix/config.py out from box
* Doing few bulk requests to get all objects in one go
* Output to CSV. /tmp/hosts.csv, /tmp/macros.csv by default
* Use native JSON/requests. not using 'pyzabbix' or 'zabbixapi' module. Can use official documents from https://www.zabbix.com/documentation/5.0/en/manual/api and copy snippet prety much 1:1
* Join 2 JSON arrays together (by hostid). works like magic (only when both parts has a matching column)
* Extract host objects. host.get
* Extract only main interfaces. hostinterface.get.
* Replace names of few JSON leafs to not make conflicts while merging data from different "tables"
* Remove HTTPS errors. Not really a feature!
* Put interface details in same level.
* Same amount of columns per SNMPv2 and SNMPv3. Every host element will have all SNMPv3 fiels. They will be blank if not used

## todo

Separate file for host macros. /tmp/macros.csv

"user.login" API method between 5.0 vs 6.0 is using different input fields


## How to use

On frontend server, test if frontend is reachable
```
curl -kL http://127.0.0.1 | grep Zabbix
```

Create a profile to communicate with Zabbix API
```
mkdir -p /var/lib/zabbix
```

Install credentials
```
echo '
url_src_instance = "http://127.0.0.1/api_jsonrpc.php"
username_src_instance = "Admin"
password_src_instance = "zabbix"
' | sudo tee /var/lib/zabbix/config.py
```

Install git utility to download this project
```
dnf -y install git
```

Install Python3.9
```
dnf -y install python3.9 python3.9-pip
```

Install modules required by program
```
pip3.9 install jsonpath-ng requests
```

Download this project
```
cd && git clone https://github.com/aigarskadikis/export-import-hosts-zabbix.git && cd export-import-hosts-zabbix
```

Set the main program executable
```
chmod +x export.py
```

Launch program
```
./export.py
```

See output
```
cat /tmp/hosts.csv
```

## Missing features, ideas to improve

No human friendly message if username or password is not correct

No value mapping per host.status, interface.type

There must be a way to optimize "try" amd "except" part of code


## Known issues

With Zabbix 6.0 it's possible to create host objects without interface at all. This program will not export those objects. With version 5.0 it's impossible to create a host object without an interface.

