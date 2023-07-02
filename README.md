# Export list of host objects to CSV

Export list of host objects, host level macros from Zabbix 5.0 and import into Zabbix 6.0

## About

* Works with Python 3.9
* Export tested with 5.0.36
* Import tested with 6.0.18
* Credentials in separate file /var/lib/zabbix/config.py
* Every host element will have all SNMPv3 fiels. They will be blank if not used

## Test frontend connection

On frontend server, test if frontend is reachable
```
curl -kL http://127.0.0.1 | grep Zabbix
```

## Download and install scripts

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

## Configure access characteristics and export/import directories

Create directory
```
mkdir -p /var/lib/zabbix
```

Install credentials
```
echo "

url_src_instance = 'http://127.0.0.1/api_jsonrpc.php'
username_src_instance = 'Admin'
password_src_instance = 'zabbix'

zabbix_templates_export_dir = '/tmp/ztemplates'
csv_export_dir = '/tmp/csv'

url_dest_instance = 'http://example.contoso.com/api_jsonrpc.php'
username_dest_instance = 'Admin'
password_dest_instance = 'zabbix'

" | sudo tee /var/lib/zabbix/config.py
```

## Export hosts

Export all hosts and create subdirectories per every host group
```
./hosts-export.py
```

To export hosts from a specific group
```
./hosts-export.py -g 'Linux servers'
```

See output
```
find /tmp/csv -type f -name '*csv'
```

## Export all templates individually

Make sure 'zabbix_templates_export_dir' has been specified in config.py. Then run:

```
./templates-export.py
```

To export a specific template group:
```
./templates-export.py -g 'Templates/Databases'
```

## Create an XML template archive for each master template

Script will find templates which are already linked to hosts. It will not re-export same tamplate twice
```
./nested-templates-export.py
```

Outcome is browsable:
```
/tmp/ztemplates/nested
```

## Import hosts

Before entering this step, the "nested-templates-export.py" must be completed without any errors.

To import all hosts from the last 'hosts-export.py' session:
```
./hosts-import -d '/tmp/csv'
```

To import hosts and macros from a specific host group use:
```
./hosts-import -d '/tmp/csv/Linux servers'
```

