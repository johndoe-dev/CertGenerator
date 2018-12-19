import click
import json
import callbacks
import decorators
from certificate import Certificate
from tools import Tools, edit_config

tools = Tools()


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-V', '--version', is_flag=True, callback=callbacks.print_version,
              expose_value=False, is_eager=True, help="show version and exit")
def main():
    """
    A command line tool to create and read CSR and P12
    """
    if tools.get_config(section="custom"):
        tools.set_options(custom=tools.get_config(section="custom"))


@main.command(short_help="init app")
@decorators.folder_options
@decorators.csv_options
def init(cert_folder, csv_file, yaml):
    """
    \b
    Create or edit certificate folder and csv file
    Add yaml file if not exists (csr.yaml)
    \f

    :param cert_folder:
    :param csv_file:
    :param yaml:
    :return:
    """
    edit_config(cert_folder, csv_file, yaml)


@main.command()
@click.pass_context
@decorators.pass_logger
@click.argument('name', type=str, required=False)
@decorators.global_options("csr")
@decorators.debug_options
def create(logger, ctx, name, config, force, key_size, san, verbose, debug, **subject):
    """
    Create a single CSR
    \f

    :param logger:
    :param ctx:
    :param name:
    :param config:
    :param force:
    :param key_size:
    :param san:
    :param verbose:
    :param debug:
    :param subject:
    :return:
    """
    tools.set_options(ctx=ctx, config=config, san=san, size=key_size, subject=subject, verbose=verbose, debug=debug)

    if name:
        tools.set_options(name=str(name))

    cert = Certificate(logger=logger, opts=tools.opts)

    if 'subject' in tools.opts:
        cert.load_subject()

    cert.generate_csr(force=force)


@main.command(short_help="Create multiple CSR")
@click.pass_context
@decorators.pass_logger
@decorators.csv_options
@decorators.global_options("csr")
@decorators.debug_options
def create_multiple(logger, ctx, csv_file, config, force, key_size, san, verbose, debug, **subject):
    """
    Create multiple certificate using csv file
    \f

    :param logger:
    :param ctx:
    :param csv_file:
    :param config:
    :param force:
    :param key_size:
    :param san:
    :param verbose:
    :param debug:
    :param subject:
    :return:
    """
    tools.set_options(ctx=ctx, config=config, san=san, size=key_size, subject=subject, verbose=verbose, debug=debug)
    cert = Certificate(logger=logger, opts=tools.opts)

    if 'subject' in tools.opts:
        cert.load_subject()

    if csv_file:
        cert.generate_multiple(csv_file=csv_file, force=force)
    else:
        cert.generate_multiple(force=force)


@main.command(short_help="Create one p12")
@click.pass_context
@decorators.pass_logger
@click.argument('name', type=str)
@click.option('-p', '--pem', type=str)
@click.option('-k', '--key', type=str)
@click.option('-pass', '--password', type=str, hide_input=True, help="Define password, default is '3z6F2Xfc'",
              default="3z6F2Xfc")
@decorators.global_options("p12")
@decorators.debug_options
def create_p12(logger, ctx, name, pem, key, password, config, force, verbose, debug):
    """
    \b
    Create a simple p12
    Need key file and pem file
    \f

    :param logger:
    :param ctx:
    :param name:
    :param pem:
    :param key:
    :param password:
    :param config:
    :param force:
    :param verbose:
    :param debug:
    :return:
    """
    tools.set_options(ctx=ctx, config=config, verbose=verbose, debug=debug)

    cert = Certificate(logger=logger, opts=tools.opts)
    cert.generate_p12(key=key, pem=pem, p12=name, password=password, force=force)


@main.command(short_help="Create multiple p12")
@click.pass_context
@decorators.pass_logger
@decorators.csv_options
@click.option('-p', '--pem-folder', type=str, help="Define pem folder where all the pem are located")
@click.option('-k', '--key-folder', type=str,
              help="Define key folder where all the key are located,"
                   " if not defined, it will search key in certificate folder")
@click.option('-pass', '--password', type=str, hide_input=True, help="Define password, default is '3z6F2Xfc'",
              default="3z6F2Xfc")
@decorators.global_options("p12")
@decorators.debug_options
def create_multiple_p12(logger, ctx, csv_file, pem_folder, key_folder, password, config, force, verbose, debug):
    """
    Create multiple p12 using csv file
    \f

    :param logger:
    :param ctx:
    :param csv_file:
    :param pem_folder:
    :param key_folder:
    :param password:
    :param config:
    :param force:
    :param verbose:
    :param debug:
    :return:
    """
    tools.set_options(ctx=ctx, config=config, verbose=verbose, debug=debug)

    cert = Certificate(logger, opts=tools.opts)
    if csv_file:
        cert.generate_multiple_p12(csv_file=csv_file, pem_folder=pem_folder,
                                   key_folder=key_folder, password=password, force=force)
    else:
        cert.generate_multiple_p12(pem_folder=pem_folder, key_folder=key_folder, password=password, force=force)


@main.command()
@click.pass_context
@decorators.pass_logger
@click.argument("path", type=str)
@click.option('-pass', '--password', type=str, hide_input=True, help="password used for create p12")
@click.option('-t', '--plain-text', is_flag=True, help="Display certificate in plain text instead of json")
def read(logger, ctx, path, password, plain_text):
    """
    Read csr or p12
    \f

    :param logger:
    :param ctx:
    :param path:
    :param password:
    :param plain_text:
    :return:
    """
    tools.set_options(ctx=ctx)

    cert = Certificate(logger=logger, opts=tools.opts)
    click.echo(cert.read(path=path, password=password, plain_text=plain_text))


"""
    CONFIG SECTION:
        - Read config ini
        - edit config ini
"""


@main.group()
def config():
    """
    Edit or read config ini
    """


@config.command()
def read():
    """read config ini
    """
    app_folder = None
    if tools.app_folder_exists():
        app_folder = "\n\nApp folder : {p}\n".format(p=tools.app_folder)
        list_yaml = json.dumps(tools.read_yaml(), indent=2)
    else:
        list_yaml = "Create app folder using \"cert init\" or \"cert config edit\" before read or edit yaml file"
    click.echo("+++++config.ini+++++\n{c}".format(c=json.dumps(tools.config.get_all(), indent=2)))
    if app_folder:
        click.echo(app_folder)
    click.echo("+++++csr.yaml+++++\n{y}".format(y=list_yaml))


@config.command(short_help="edit app config")
@decorators.folder_options
@decorators.csv_options
def edit(cert_folder, csv_file, yaml):
    """
    \b
    Create or edit certificate folder and csv file
    Add yaml file if not exists (csr.yaml)
    \f

    :param cert_folder:
    :param csv_file:
    :param yaml:
    :return:
    """
    edit_config(cert_folder, csv_file, yaml)


@config.command()
def edit_yaml():
    """
    Edit Yaml file
    """
    tools.write_yaml()


@config.command(short_help="Delete options")
@click.option("-cert", "--cert-folder", is_flag=True, help="if flag, delete cert path folder from config ini")
@click.option("-csv", "--csv-file", is_flag=True, help="if flag, delete csvfile from config ini")
def delete(cert_folder, csv_file):
    """
    Delete option from config ini (csr, p12 and csv path)
    \f

    :param cert_folder:
    :param csv_file:
    :return:
    """
    _config = tools.get_config()

    if not cert_folder and not csv_file:
        _config.remove_section(section="custom")

    with decorators.RemoveOption(config=_config, option=cert_folder) as o:
        if o:
            _config.remove_option(section="custom", option="app_folder")

    with decorators.RemoveOption(config=_config, option=csv_file) as o:
        if o:
            _config.remove_option(section="custom", option="csvfile")


if __name__ == "__main__":
    main()
