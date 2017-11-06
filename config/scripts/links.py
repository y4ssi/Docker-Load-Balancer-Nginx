# -*- coding: utf-8 -*-
# import library
import json
import os
import requests_unixsocket
import re
import filecmp
from shutil import copyfile
from subprocess import call

# delete old upstream
try:
    os.remove("/etc/nginx/conf.d/upstream.conf.new")
except:
    print "nothing to erase"

# append new upstream
with open("/etc/nginx/conf.d/upstream.conf.new", "a") as upstream_new:
    upstream_new.write("upstream lb {\n")
    # connect to API Docker
    session = requests_unixsocket.Session()
    # Get network ID
    networkID = session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/" +  str(os.environ["HOSTNAME"])  + "/json").json()["NetworkSettings"]["Networks"].values()[0]["NetworkID"]
    # Get containers in network
    containers = session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/networks/" + networkID).json()["Containers"]
    for key, value in containers.iteritems():
        if "_lb_" not in value["Name"]:
            upstream_new.write("    server " + value["IPv4Address"].split("/")[0] + ":" + str(os.environ["PORT_SERVICE"]) + " max_fails=1 fail_timeout=1s;\n")
    upstream_new.write("}")
# Set upstream
copyfile("/etc/nginx/conf.d/upstream.conf.new", "/etc/nginx/conf.d/upstream.conf")
call(["nginx", "-g", "daemon off;"])
