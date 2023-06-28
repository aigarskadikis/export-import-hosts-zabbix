#!/bin/env python3.9
import libxml2

doc = libxml2.parseFile("tst.xml")
ctxt = doc.xpathNewContext()
res = ctxt.xpathEval("//*")
if len(res) != 2:
    print("xpath query: wrong node set size")
    sys.exit(1)
if res[0].name != "doc" or res[1].name != "foo":
    print("xpath query: wrong node set value")
    sys.exit(1)
doc.freeDoc()
ctxt.xpathFreeContext()

