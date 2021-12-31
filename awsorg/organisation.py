import sys

import boto3

from awsorg import errorExit, errorNotify, errorRaise


def paginate(command, kargs, listkey, nextname="NextToken", nextkey="NextToken"):
    """Paginate any boto3 command"""
    try:
        op = []
        kwargs = kargs
        while True:
            resp = command(**kwargs)
            if listkey in resp:
                op.extend(resp[listkey])
            if nextkey in resp and resp[nextkey]:
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
        errorRaise(sys.exc_info()[2], e)


def getClient(client, profile=None, region=None):
    try:
        sess = getSession(profile, region)
        return sess.client(client)
    except Exception as e:
        errorRaise(sys.exc_info()[2], e)


def orgClient(profile=None):
    try:
        return getClient("organizations", profile=profile)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def getRoots(orgclient):
    try:
        return paginate(orgclient.list_roots, {}, "Roots")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


# def getOUTree(orgclient):
#     try:
#         tree = {}
#         roots = getRoots(orgclient)
#         if len(roots) == 1:
#             tree["root"] = []
#             tree["accounts"] = getAccounts(orgclient, roots[0]["Id"])
#             kwargs = {"ParentId": roots[0]["Id"]}
#             children = paginate(
#                 orgclient.list_organizational_units_for_parent,
#                 kwargs,
#                 "OrganizationalUnits",
#             )
#             tree["root"].extend(children)
#         return tree
#     except Exception as e:
#         errorNotify(sys.exc_info()[2], e)


# def getTree(orgclient):
#     try:
#         tree = {}
#         roots = getRoots(orgclient)
#         for root in roots:
#             stree = getSubTree(orgclient, root)
#             tree[root["Id"]] = {"arn": root["Arn"], "tree": stree}
#         return tree
#     except Exception as e:
#         errorNotify(sys.exc_info()[2], e)


# def getSubTree(orgclient, startou):
#     try:
#         # print(f"getSubTree: {startou=}")
#         op = {startou["Id"]: {}}
#         kwargs = {"ParentId": startou["Id"]}
#         # print(f"calling paginate: {kwargs=}")
#         ous = paginate(
#             orgclient.list_organizational_units_for_parent,
#             kwargs,
#             "OrganizationalUnits",
#         )
#         if len(ous) > 0:
#             op[startou["Id"]]["ous"] = []
#             # print(f"getSubTree: {startou['Id']} child ous len: {len(ous)}")
#         for ou in ous:
#             op[startou["Id"]]["ous"].append(getSubTree(orgclient, ou))
#         op[startou["Id"]]["accounts"] = getAccounts(orgclient, startou["Id"])
#         # print(
#         # f"getSubTree: {startou['Id']} len accounts: {len(op[startou['Id']]['accounts'])}"
#         # )
#         infos = ["Name", "Arn"]
#         for info in infos:
#             if info in startou:
#                 op[startou["Id"]][info] = startou[info]
#                 # print(f'getSubTree: {startou["Id"]} setting {info} to {startou[info]}')
#         return op
#     except Exception as e:
#         errorNotify(sys.exc_info()[2], e)


def getAccounts(orgclient, parentid):
    try:
        kwargs = {"ParentId": parentid}
        return paginate(orgclient.list_accounts_for_parent, kwargs, "Accounts")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def buildOrgTree(orgclient, profile, profilename):
    try:
        op = {"profile": profile, "Name": profilename, "roots": []}
        roots = getRoots(orgclient)
        for root in roots:
            op["roots"].append(buildSubTree(orgclient, root))
        return op
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def buildSubTree(orgclient, startou):
    try:
        op = startou
        kwargs = {"ParentId": startou["Id"]}
        ous = paginate(
            orgclient.list_organizational_units_for_parent,
            kwargs,
            "OrganizationalUnits",
        )
        op["accounts"] = getAccounts(orgclient, startou["Id"])
        op["ous"] = [buildSubTree(orgclient, ou) for ou in ous]
        return op
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
