#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, sys, urllib2
from os import getenv
from re import match
from docker import Client
from docker.errors import DockerException

def main(repotag):
    # divide into repo name and tag name
    try:
        (repo, tag) = repotag.rsplit(":",1)
    except ValueError:
        repo = repotag
        tag = "latest"
        repotag = repo + ":" + tag

    # get image id from private registry
    request_url =  "http://localhost:5000/v2/" + repo + "/manifests/" + tag
    request_headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"
    }
    req = urllib2.Request( request_url, headers=request_headers )
    try:
        res = urllib2.urlopen(req, timeout=10)
        digest = json.loads(res.read())["config"]["digest"]
    except urllib2.HTTPError:
        digest = "(no image)"
    except urllib2.URLError:
        digest = "(connection error)"
    except:
        digest = "(unexpected error)"

    # get image id from local volume
    dockerhost = getenv("DOCKER_HOST", "unix://var/run/docker.sock")
    try:
        cli = Client( base_url=dockerhost, version='auto', timeout=10 )
        imgid = "(no image)"
        for images in cli.images():
            if repotag in images['RepoTags']:
                imgid = images['Id']
    except DockerException:
        imgid = "(connection error)"
    except:
        imgid = "(unexpected error)"

    # compare and output results
    pattern = r"sha256:"
    if match(pattern, digest) and match(pattern, imgid):
        if digest == imgid:
            print( "same images" )
            exitcode = 0
        else:
            print( "different images" )
            exitcode = 2
    else:
        print( "cannot compare" )
        exitcode = 5
    print( "localhost:5000  " + digest )
    print( "Docker Host     " + imgid )
    sys.exit(exitcode)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print >>sys.stderr, "Usage: " + sys.argv[0] + " [REPOSITORY:TAG]"
        sys.exit(22)
    main(sys.argv[1])
