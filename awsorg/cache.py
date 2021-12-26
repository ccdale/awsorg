from pathlib import Path
import sys
import time

import yaml

from awsorg import errorNotify

home = Path.home()
confdir = home / ".config" / "awsorg"
confdir.mkdir(parents=True, exist_ok=True)
# cachefn = confdir / "awsorg.yaml"


def validCache(profile, cacheage=86400):
    """Checks if the cache is out of date - default age 1 day"""
    try:
        cachefn = confdir / f"{profile}.yaml"
        cache = readCache(cachefn)
        if cache is not None:
            then = int(time.time()) - cacheage
            if cache["timestamp"] > then:
                return cache
        return None
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def readCache(cachefn):
    try:
        if not cachefn.exists():
            return None
        with open(cachefn, "r") as ifn:
            cache = yaml.safe_load(ifn)
        return cache
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def writeCache(profile, cache):
    try:
        cachefn = confdir / f"{profile}.yaml"
        cache["timestamp"] = int(time.time())
        with open(cachefn, "w") as ofn:
            yaml.dump(cache, ofn, default_flow_style=False)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
