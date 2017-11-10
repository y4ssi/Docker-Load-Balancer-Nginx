# -*- coding: utf-8 -*-
# import library
import json
import os
import requests_unixsocket
import re
import filecmp
from shutil import copyfile
from subprocess import call
import docker
import threading

# connect to API Docker
session = requests_unixsocket.Session()
# Get network ID
Networks = session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/" +  str(os.environ["HOSTNAME"])  + "/json").json()["NetworkSettings"]["Networks"].values()[0]
networkID = Networks["NetworkID"]
name_service = Networks["Links"][0].split(":")[1]
aliases = Networks["Aliases"][0]

def containers_in_network(session):
    # Get containers in network
    return session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/networks/" + networkID).json()["Containers"]

def upstream():
# delete old upstream
    try:
        os.remove("/etc/nginx/upstream.conf.new")
    except:
        print "nothing to erase"

    # append new upstream
    with open("/etc/nginx/upstream.conf.new", "a") as upstream_new:
        upstream_new.write("upstream lb {\n")
        upstream_new.write("    ip_hash;\n")
        for key, value in containers_in_network(session).iteritems():
            if aliases not in value["Name"] and name_service in value["Name"]:
                upstream_new.write("    server " + value["IPv4Address"].split("/")[0] + ":" + str(os.environ["PORT_SERVICE"]) + " max_fails=1 fail_timeout=1s;\n")
        upstream_new.write("}")
    # Set upstream
    copyfile("/etc/nginx/upstream.conf.new", "/etc/nginx/upstream.conf")


def stream():
    # delete old stream
    try:
        os.remove("/etc/nginx/stream.conf.new")
    except:
        print "nothing to erase"

    # append new stream
    with open("/etc/nginx/stream.conf.new", "a") as stream_new:
        stream_new.write("upstream lb {\n")
        for key, value in containers_in_network(session).iteritems():
            if aliases not in value["Name"] and name_service in value["Name"]:
                stream_new.write("    server " + value["IPv4Address"].split("/")[0] + ":" + str(os.environ["PORT_SERVICE"]) + " max_fails=1 fail_timeout=1s;\n")
        stream_new.write("}")
    # Set stream
    copyfile("/etc/nginx/stream.conf.new", "/etc/nginx/stream.conf")

def nginx():
    stream()
    upstream()
    call(["nginx", "-g", "daemon off;"])

def nginx_reload():
    stream()
    upstream()
    call(["nginx", "-s", "reload"])

# start nginx
threads = []
t1 = threading.Thread(target=nginx, args=())
threads.append(t1)
t1.start()

# events docker to add or delete upstream and stream
client = docker.APIClient(base_url="unix://var/run/docker.sock")
for event in client.events(filters={"network": networkID}):
    if not event=="":
        nginx_reload()
