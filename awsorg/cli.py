from pprint import pprint
import sys

import click
from tabulate import tabulate
import yaml

from awsorg import errorNotify, errorExit
from awsorg.organisation import (
    orgClient,
    getRoots,
    getAccounts,
    buildOrgTree,
)
from awsorg.cache import validCache, writeCache


class Config:
    def __init__(self):
        try:
            self.profile = None
            self.profilename = None
            self.cache = None
        except Exception as e:
            errorNotify(sys.exc_info()[2], e)


passconfig = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "-c",
    "--cache-age",
    type=click.STRING,
    default="1d",
    help="Max age of cache before it is refreshed: default '1d' (can be in hours - 3h - or days - 2d)",
)
@click.option(
    "-n", "--profile-name", type=click.STRING, help="Friendly name for this profile"
)
@click.option(
    "-p",
    "--profile",
    type=click.STRING,
    required=True,
    help="The AWS profile (credentials) to use",
)
@passconfig
def cli(config, cache_age, profile_name, profile):
    try:
        if profile != "":
            config.profile = profile
        config.profilename = (
            profile_name.replace(" ", "_")
            if profile_name is not None
            else config.profile
        )
        config.cacheage = 86400
        if len(cache_age) > 1:
            mod = cache_age[-1]
            xlen = int(cache_age[:-1])
            mults = {"h": 3600, "d": 86400}
            if mod.lower() in mults:
                mult = mults[mod.lower()]
            else:
                mult = mults["d"]
            config.cacheage = xlen * mult
        config.cache = validCache(config.profile, cacheage=config.cacheage)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def refresh(config):
    """Refresh the cache for this profile."""
    try:
        click.echo(f"Refreshing cache for {config.profilename}")
        oc = orgClient(profile=config.profile)
        tree = buildOrgTree(oc, config.profile, config.profilename)
        config.cache = tree
        writeCache(config.profile, config.cache)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


# @cli.command()
# @passconfig
# def refresh(config):
#     """Refresh the cache for this profile."""
#     try:
#         click.echo(f"Refreshing cache for {config.profile}")
#         oc = orgClient(profile=config.profile)
#         tree = getTree(oc)
#         tree["profilename"] = (
#             config.profilename if config.profilename is not None else config.profile
#         )
#         config.cache = tree
#         writeCache(config.profile, config.cache)
#     except Exception as e:
#         errorNotify(sys.exc_info()[2], e)


def getCache(config):
    try:
        if config.cache is None:
            refresh(config)
            if config.cache is None:
                raise Exception(
                    "Failed to obtain information from the {config.profile} organisation."
                )
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Roots(config):
    """Display the Root OU ID and ARN for the Organisation."""
    try:
        ignore = ["profilename", "timestamp"]
        roots = []
        getCache(config)
        lines = [[config.cache["Name"], config.cache["profile"], "", "", ""]]
        for root in config.cache["roots"]:
            line = [root["Name"], root["Id"]]
            line.extend([root["Arn"], len(root["ous"]), len(root["accounts"])])
            lines.append(line)
        head = ["Name", "Id", "Arn", "OUs", "Accounts"]
        summary = tabulate(lines, headers=head)
        click.echo()
        click.echo(summary)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Summary(config):
    """Display the OU Tree Summary for the Organisation"""
    try:
        root, lines, kids, totalaccts, ousn, acctsn = processRootTree(config)
        click.echo()
        click.echo(f"Organisation: {config.profile}")
        click.echo()
        headers = ["Root Id", "Child OUs", "Child Accounts", "Total Accounts"]
        click.echo(tabulate([[root, ousn, acctsn, totalaccts]], headers=headers))
        click.echo()
        headers = ["OU Id", "OU Name", "Child OUs", "Child Accounts"]
        click.echo(tabulate(lines, headers=headers))
        if len(kids):
            print()
            headers = ["ParentId", "OU Id", "OU Name", "Child Accounts"]
            click.echo(tabulate(kids, headers=headers))
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Tree(config):
    """Display the full OU Tree including child accounts"""
    try:
        getCache(config)
        info = getCacheInfo(config.cache)
        for root in info["roots"]:
            blocks = makeOULines(root, config.cache[root]["tree"][root])
            for block in blocks:
                click.echo(block)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def processRootTree(config):
    try:
        level = width = 0
        lines = []
        kids = []
        totalaccts = 0
        getCache(config)
        info = getCacheInfo(config.cache)
        for root in info["roots"]:
            tree = config.cache[root]["tree"][root]
            ousn = 0 if "ous" not in tree else len(tree["ous"])
            acctsn = 0 if "accounts" not in tree else len(tree["accounts"])
            totalaccts += acctsn
            if ousn > 0:
                level = 0
                ous = [extractOU(oud) for oud in tree["ous"]]
                for ou in ous:
                    parentid, haskids, naccts, slines = processSubTree(ou, level)
                    for kid in haskids:
                        knaccts = len(kid["accounts"])
                        totalaccts += knaccts
                        kids.append([parentid, kid["Id"], kid["Name"], knaccts])
                    lines.extend(slines)
                    totalaccts += naccts
        return (root, lines, kids, totalaccts, ousn, acctsn)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def processSubTree(subtree, level):
    """returns a list of strings indented by level

    the headings for each element of the list are:
    OUID, Name, Number of Sub-OUs, Number of Accounts
    """
    try:
        lines = []
        ousn = 0 if "ous" not in subtree else len(subtree["ous"])
        acctsn = 0 if "accounts" not in subtree else len(subtree["accounts"])
        lines.append(
            makeOneLine(
                ["" for x in range(level)],
                [subtree["Id"], subtree["Name"], ousn, acctsn],
            )
        )
        haskids = []
        if ousn > 0:
            level += 1
            ous = [extractOU(oud) for oud in subtree["ous"]]
            for ou in ous:
                haskids.append(ou)
        return subtree["Id"], haskids, acctsn, lines
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def getCacheInfo(cache):
    try:
        info = {}
        for key in cache:
            if key == "timestamp":
                info["timestamp"] = cache["timestamp"]
            elif key == "profilename":
                info["profilename"] = cache["profilename"]
            else:
                if "roots" not in info:
                    info["roots"] = []
                info["roots"].append(key)
        return info
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def showBlock(title, headers, lines):
    try:
        click.echo(f"\n{title}")
        click.echo("".join(["=" for x in title]))
        click.echo()
        click.echo(tabulate(lines, headers=headers))
        click.echo()
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def extractOU(oudictin):
    """Extracts the ou from the cache ou dictionary."""
    try:
        for key in oudictin:
            ou = oudictin[key]
            ou["Id"] = key
        return ou
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def findOU(findou, cache):
    """looks down one level to find the ou

    returns: the ou dictionary if found or None
    """
    try:
        if "ous" in cache:
            for oud in cache["ous"]:
                ou = extractOU(oud)
                if findou in [ou["Id"], ou["Name"]]:
                    return ou
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def makeOULines(ou, oudict, indent=0):
    try:
        lindent = ["" for x in range(0, indent)]
        headers = makeOneLine(lindent, ["OU", "Id", "OUs", "Accounts"])
        print(headers)
        ousn = 0 if "ous" not in oudict else len(oudict["ous"])
        acctsn = 0 if "accounts" not in oudict else len(oudict["accounts"])
        line = makeOneLine(lindent, [oudict["Name"], ou, ousn, acctsn])
        block = [tabulate([line], headers=headers)]
        if acctsn > 0:
            headers, lines = makeAccountsLines(oudict["accounts"], indent=indent + 1)
            block.append(tabulate(lines, headers=headers))
        if ousn > 0:
            for oud in oudict["ous"]:
                for ouid in oud:
                    # print(f"{ouid=}")
                    # pprint(oud[ouid])
                    block.append(makeOULines(ouid, oud[ouid], indent=indent + 1))
        return block
    except Exception as e:
        errorExit(sys.exc_info()[2], e)


def makeSubTreeLines(subtree, indent=1):
    try:
        lines = []
        lindent = ["" for x in range(0, indent)]
        headers = makeOneLine(lindent, ["OU", "Id", "OUs", "Accounts"])
        ousn = 0 if "ous" not in subtree else len(subtree["ous"])
        print(f"{ousn=}")
        acctsn = 0 if "accounts" not in subtree else len(subtree["accounts"])
        print(f"{acctsn=}")
        xline = [subtree["Name"], subtree, ousn, acctsn]
        lines.append(makeOneLine(lindent, xline))
        if ousn > 0:
            xhead, slines = makeSubTreeLines(subtree["ous"], indent=indent + 1)
            showBlock(f"{subtree['Name']} OUs", xhead, slines)
        if acctsn > 0:
            xhead, slines = makeAccountsLines(subtree["accounts"], indent=indent + 1)
            showBlock(f"{subtree['Name']} Accounts", xhead, slines)
        return (headers, lines)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def makeAccountsLines(accts, indent=2):
    try:
        lines = []
        lindent = ["" for x in range(0, indent)]
        headers = makeOneLine(lindent, ["ID", "Name", "Email"])
        for acct in accts:
            xline = [acct["Id"], acct["Name"], acct["Email"]]
            lines.append(makeOneLine(lindent, xline))
        return (headers, lines)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def makeOneLine(indent, line):
    try:
        xline = indent
        xline.extend(line)
        return xline
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def displaySubTree(subtree):
    try:
        lines = makeSubTreeLines(subtree)
        tab = tabulate
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def summariseSubTree(subtree, parentid=None):
    try:
        headers = ["OU", "Id", "OUs", "Accounts", "Parent OU"]
        lines = []
        for ou in subtree:
            parent = "" if parentid is None else parentid
            acctsn = ousn = 0
            if "ous" in ou:
                ousn = len(ou["ous"])
            if "accounts" in ou:
                acctsn = len(ou["accounts"])
            lines.append([ou["Name"], ou, ousn, acctsn, parent])
        return lines
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def displaySummary(orgclient, tree, showaccounts=False):
    try:
        totalaccts = 0
        lines = []
        blank = ["", "", ""]
        headers = (
            ["OU", "Account ID", "Name"] if showaccounts else ["OU", "Accounts", "Id"]
        )
        rnaccts = len(tree["accounts"])
        totalaccts += rnaccts
        line = ["Root", rnaccts, ""]
        lines.append(line)
        if showaccounts:
            for acct in tree["accounts"]:
                lines.append(accountLine(acct))
            lines.append(blank)
        for ou in tree["root"]:
            accts = getAccounts(orgclient, ou["Id"])
            naccts = len(accts)
            totalaccts += naccts
            line = [ou["Name"], naccts, ou["Id"]]
            lines.append(line)
            if showaccounts:
                for acct in accts:
                    lines.append(accountLine(acct))
                lines.append(blank)
        line = ["Totals", totalaccts, ""]
        lines.append(line)
        print(f"\n\n{tabulate(lines, headers=headers)}")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def accountLine(acct):
    try:
        line = ["", acct["Id"], acct["Name"]]
        return line
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


def pluralise(amount, word):
    try:
        return word if amount == 1 else f"{word}s"
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def cprint(config):
    """Pretty print the config"""
    try:
        pprint(config.cache)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
