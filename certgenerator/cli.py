import click
import json
import callbacks
import decorators
from certificate import Certificate
from tools import Tools, edit_config

tools = Tools()


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--verbose', is_flag=True, help="Display only if necessary")
@click.option('-d', '--debug', is_flag=True, help="Display all details")
@click.option('--version', is_flag=True, callback=callbacks.print_version,
              expose_value=False, is_eager=True, help="show version and exit")
def main(verbose, debug):
    """
    A command line tool to create and read CSR and P12
    """
    if tools.get_config(section="custom"):
        tools.set_options(custom=tools.get_config(section="custom"))

    tools.set_options(verbose=verbose, debug=debug)


@main.command()
@decorators.folder_options
@decorators.csv_options
def init(cert_folder, csv_file):
    """
    Create certificate folder and default csv file
    """
    edit_config(cert_folder, csv_file)


@main.command()
@click.pass_context
@decorators.pass_logger
@click.argument('name', type=str, required=False)
@decorators.global_options("csr")
def create(logger, ctx, name, config, key_size, san, **subject):
    """
    Create a single CSR
    """
    tools.set_options(ctx=ctx, config=config, san=san, size=key_size, subject=subject)

    if name:
        tools.set_options(name=str(name))

    cert = Certificate(logger=logger, opts=tools.opts)

    if 'subject' in tools.opts:
        cert.load_subject()

    cert.generate_csr()


@main.command()
@click.pass_context
@decorators.pass_logger
@decorators.csv_options
@decorators.global_options("csr")
def create_multiple(logger, ctx, csv_file, config, key_size, san, **subject):
    """
    Create multiple certificate using csv file
    """
    tools.set_options(ctx=ctx, config=config, san=san, size=key_size, subject=subject)
    cert = Certificate(logger=logger, opts=tools.opts)

    if 'subject' in tools.opts:
        cert.load_subject()

    if csv_file:
        cert.generate_multiple(csv_file=csv_file)
    else:
        cert.generate_multiple()


@main.command()
@click.pass_context
@decorators.pass_logger
@click.argument('name', type=str)
@click.option('-p', '--pem', type=str)
@click.option('-k', '--key', type=str)
@click.option('-pass', '--password', type=str, hide_input=True, help="Define password, default is '3z6F2Xfc'")
@decorators.global_options("p12")
def create_p12(logger, ctx, name, pem, key, password, config):
    """
    Create a simple p12
    Need key file and pem file
    """
    tools.set_options(ctx=ctx, config=config)

    cert = Certificate(logger=logger, opts=tools.opts)
    if password:
        cert.generate_p12(key=key, pem=pem, p12=name, password=password)
    else:
        cert.generate_p12(key=key, pem=pem, p12=name)


@main.command()
@click.pass_context
@decorators.pass_logger
@decorators.csv_options
@click.option('-p', '--pem-folder', type=str, help="Define pem folder where all the pem are located")
@click.option('-k', '--key-folder', type=str,
              help="Define key folder where all the key are located,"
                   " if not defined, it will search key in certificate folder")
@decorators.global_options("p12")
def create_multiple_p12(logger, ctx, csv_file, pem_folder, key_folder, config):
    """
    Create multiple p12 using csv file
    """
    tools.set_options(ctx=ctx, config=config)

    cert = Certificate(logger, opts=tools.opts)
    if csv_file:
        cert.generate_multiple_p12(csv_file=csv_file, pem_folder=pem_folder, key_folder=key_folder)
    else:
        cert.generate_multiple_p12(pem_folder=pem_folder, key_folder=key_folder)


@main.command()
@click.pass_context
@decorators.pass_logger
@click.argument("path", type=str)
@click.option('-pass', '--password', type=str, hide_input=True, help="password used for create p12")
@click.option('-t', '--plain-text', is_flag=True, help="Display certificate in plain text instead of json")
def read(logger, ctx, path, password, plain_text):
    """Read csr or p12"""
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
    """
    read config ini
    """
    _config = tools.get_config()
    click.echo(json.dumps(_config.get_all(), indent=2))


@config.command()
@decorators.folder_options
@decorators.csv_options
def edit(cert_folder, csv_file):
    """
    Add option in config ini (csr, p12 and csv path)
    """
    edit_config(cert_folder, csv_file)


@config.command()
@click.option("-cert", "--cert-folder", is_flag=True, help="if flag, delete cert path folder from config ini")
@click.option("-csv", "--csv-file", is_flag=True, help="if flag, delete csvfile from config ini")
def delete(cert_folder, csv_file):
    """
    Delete option from config ini (csr, p12 and csv path)
    """
    _config = tools.get_config()

    def check_section():
        if not _config.get_section(section="custom"):
            _config.remove_section(section="custom")

    if cert_folder:
        _config.remove_option(section="custom", option="cert_directory")
        check_section()

    if csv_file:
        _config.remove_option(section="custom", option="csvfile")
        check_section()

    if not cert_folder and not csv_file:
        _config.remove_section(section="custom")


if __name__ == "__main__":
    main()
