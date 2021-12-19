import sys

import boto3
import click

from awsorg import errorNotify, errorRaise, errorExit


def paginate(command, kargs, listkey, nextname="NextToken", nextkey="NextToken"):
    try:
        op = []
        kwargs = kargs
        while True:
            resp = command(kwargs)
            if listkey in resp:
                op.extend(resp[listkey])
            if nextkey in resp:
                kwargs[nextname] = resp[nextkey]
            else:
                break
        return op
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def getSession(profile=None, region=None):
    """Start a boto3 session."""
    try:
        kwargs = {}
        if profile is not None:
            kwargs["profile_name"] = profile
        if region is not None:
            kwargs["region_name"] = region
        return boto3.Session(**kwargs)
    except Exception as e:
        errorRaise(sys.exc_info()[2])


def getClient(client, profile=None, region=None):
    try:
        sess = getSession(profile, region)
        return sess.client(client)
    except Exception as e:
        errorRaise(sys.exc_info()[2])


def orgClient(profile=None):
    try:
        org = getClient("organizations", profile=profile)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def getRoots(orgclient):
    try:
        roots = orgclient.list_roots()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
