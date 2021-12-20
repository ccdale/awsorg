import sys

import click
from tabulate import tabulate

from awsorg import errorNotify
from awsorg.organisation import orgClient, getRoots, getOUTree, getAccounts


class Config:
    def __init__(self):
        try:
            self.profile = None
            self.region = None
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
    "-r", "--region", type=click.STRING, default="", help="The AWS region to run in"
)
@passconfig
def cli(config, profile, region):
    try:
        if profile != "":
            config.profile = profile
        if region != "":
            config.region = region
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
