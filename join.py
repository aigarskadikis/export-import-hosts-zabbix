#!/bin/env python3.9
import json
from jsonpath_ng import jsonpath, parse
dict1 = [{"hostid":123,"host":"one"},{"hostid":456,"host":"two"},{"hostid":789,"host":"three"}]
dict2 = [{"hostid":123,"IP":"127.0.0.1"},{"hostid":456,"IP":"192.168.88.1"}]
print(dict1)
print(dict2)
dict3 = [dict[0] | dict[1] for dict in zip(dict1, dict2)]
print(dict3)
