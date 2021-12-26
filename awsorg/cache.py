from pathlib import Path
import sys
import time

import yaml

from awsorg import errorNotify

home = Path.home()
confdir = home / ".config"
confdir.mkdir(parents=True, exist_ok=True)
cachefn = confdir / "awsorg.yaml"


def validCache():
    try:
        cache = readCache()
        if cache is not None:
            then = int(time.time()) - 86400  # yesterday
            if cache["timestamp"] > then:
                return cache
        return None
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def readCache():
    try:
        if not cachefn.exists():
            return None
        with open(cachefn, "r") as ifn:
            cache = yaml.safe_load(ifn)
        return cache
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def writeCache(cache):
    try:
        cache["timestamp"] = int(time.time())
        with open(cachefn, "w") as ofn:
            yaml.dump(cache, ofn, default_flow_style=False)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
