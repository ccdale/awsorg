import sys

import boto3

from awsorg import errorNotify, errorRaise, errorExit


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
