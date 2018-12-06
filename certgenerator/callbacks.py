import click
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
        conf = Tools()
        version = conf.get_app_info("__version__")
        name = conf.get_app_info("__title__")
        click.echo("Name: {n}\nVersion: {v}".format(n=name, v=version))
    except KeyError:
        pass
    ctx.exit()
