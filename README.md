# Export list of host objects to CSV

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
cd && git clone https://github.com/aigarskadikis/export-import-hosts-zabbix.git
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
