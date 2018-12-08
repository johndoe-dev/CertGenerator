import click
import sys
from tools import validate_subject, Tools


def get_subject(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    fields = ["C", "CN", "ST", "L", "O", "OU", "emailAddress"]

    for field in fields:
        res = validate_subject(field)
        if res == "-":
            continue
        ctx.params[field] = res


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    try:
        tools = Tools()
        version = tools.get_app_info("__version__")
        name = tools.get_app_info("__title__")
        python_version = "{n} {v}".format(n="Python", v=sys.version)
        click.echo("{n} {v}\n{p}".format(n=name, v=version, p=python_version))
    except KeyError:
        pass
    ctx.exit()
