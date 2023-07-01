# Export list of host objects to CSV

Export list of host objects, host level macros from Zabbix 5.0 and import into Zabbix 6.0

## About

* Works with Python 3.9
* Export tested with 5.0.23
* Import tested with 6.0.18
* Credentials in separate file. /var/lib/zabbix/config.py out from box
* Use native JSON/requests. not using 'pyzabbix' or 'zabbixapi' module. Can use official documents from https://www.zabbix.com/documentation/5.0/en/manual/api and copy snippet prety much 1:1
* Remove HTTPS errors. Not really a feature!
* Every host element will have all SNMPv3 fiels. They will be blank if not used

## CSV export for host objects

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
chmod +x hosts-export.py
```

Export all hosts and create subdirectories per every host group
```
./hosts-export.py
```

See output
```
find /tmp/csv -type f -name '*csv'
```

## Template export

Make sure 'zabbix_templates_export_dir' has been specified in config.py

### Export all templates individually

This is only for backup purpose

```
./templates-export.py
```

### Create nested template bundles

This script will undertand all levels of nested template create one solid XML file which contains the whole tree. Script will create the "bundles" only for registred hosts (where template is really in use)
```
./nested-templates-export.py
```

Outcome is browsable:
```
/tmp/ztemplates/nested
```

## Import hosts

Before entering this step, the "nested-templates-export.py" must be completed without any errors.

To import all hosts and macros from a specific catogory use:
```
./hosts-import -d '/tmp/ztemplate/Linux servers'
```

