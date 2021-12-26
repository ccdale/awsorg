import sys

import click
from tabulate import tabulate

from awsorg import errorNotify
from awsorg.organisation import orgClient, getRoots, getOUTree, getAccounts
from awsorg.cache import validCache


class Config:
    def __init__(self):
        try:
            self.profile = None
            self.cache = None
        except Exception as e:
            errorNotify(sys.exc_info()[2], e)


passconfig = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "-p",
    "--profile",
    type=click.STRING,
    default="",
    help="The AWS profile (credentials) to use",
)
@click.option(
    "-c",
    "--cache-age",
    type=click.STRING,
    default="1d",
    help="Max age of cache before it is refreshed: default '1d' (can be in hours - 3h - or days - 2d)",
)
@passconfig
def cli(config, profile, cache_age):
    try:
        if profile != "":
            config.profile = profile
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
        config.cache = validCache(cacheage=config.cacheage)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Roots(config):
    """Display the Root OU ID and ARN for the Organisation."""
    try:
        oc = orgClient(profile=config.profile)
        roots = getRoots(oc)
        if len(roots) == 1:
            click.echo("\nRoot OU:")
            click.echo(f'    ID:  {roots[0]["Id"]}')
            click.echo(f'    ARN: {roots[0]["Arn"]}')
        else:
            raise Exception(f"roots length is not 1 {roots=}")
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Summary(config):
    """Display the OU Tree Summary for the Organisation"""
    try:
        oc = orgClient(profile=config.profile)
        tree = getOUTree(oc)
        displaySummary(oc, tree)
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)


@cli.command()
@passconfig
def Tree(config):
    """Display the full OU Tree including child accounts"""
    try:
        oc = orgClient(profile=config.profile)
        tree = getOUTree(oc)
        displaySummary(oc, tree, showaccounts=True)
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
