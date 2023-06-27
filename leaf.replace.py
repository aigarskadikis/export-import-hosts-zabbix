#!/bin/env python3.9
dict1 = [{"hostid":123,"host":"one"},{"hostid":345,"host":"two"}]
for item in dict1:
  item["host_ID"] = item.pop("hostid")
print(dict1)
