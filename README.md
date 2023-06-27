# Export list of host objects to CSV

## Features

Python 3.9 compatible
Credentials in separate file. /var/lib/zabbix/config.py out from box
doing bulk request to get all objects in one go
output to CSV. /tmp/hosts.csv by default
use native JSON/requests. not using 'pyzabbix' or 'zabbixapi' module
join 2 JSON arrays together (by hostid). works like magic (only when both parts has a column)
extract host objects
extract interfaces
extract only main interface
replace some JSON leaf to not make conflicts
remove HTTPS errors
put interface details in same level
same amount of columns per SNMPv2 and SNMPv3

## todo

Separate file for host macros

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
url = "http://127.0.0.1/api_jsonrpc.php"
username = "Admin"
password = "zabbix"
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

## Known issues

No human friendly message if username or password is not correct

There must be a way to optimize "try" amd "except" part.

