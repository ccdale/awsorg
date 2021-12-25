from pathlib import Path
import sys
import time

import yaml

from awsorg import errorNotify

home = Path.home()
confdir = home / ".config"
confdir.mkdir(parents=True, exist_ok=True)
cachefn = confdir / "awsorg.yaml"
if not cachefn.exists():
    cachefn.touch()


def validCache():
    try:
        cache = readCache()
        now = int(time.time())
        then = now - 86400
        if cache["timestamp"] < then:
            return None
        return cache
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def readCache():
    try:
        with open(cachefn, "r") as ifn:
            cache = yaml.safe_load(ifn)
        if cache is None:
            cache = {"timestamp": 1640318856}  # Fri 24 Dec 04:07:36 GMT 2021
        return cache
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def writeCache(cache):
    try:
        with open(cachefn, "w") as ofn:
            yaml.dump(cache, ofn, default_flow_style=False)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
