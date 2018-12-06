import click
import functools
import os
from functools import update_wrapper
from tools import Tools
import callbacks


def global_options(argument="csr"):
    """Define global options
    """
    def inner_options(f):
        _type = ['csr', 'p12']
        options = [
            click.option('-c', '--config', is_flag=True,
                         help="Use config.ini, if you use csv, column 'serial' required"),
            click.option('-ks', '--key-size', type=click.Choice(['1024', '2048', '4096']),
                         help="Define key size", show_choices=True),
            click.option('-sa', '--san', multiple=True, type=str),
            click.option('-s', '--subject', is_flag=True, expose_value=False,
                         callback=callbacks.get_subject, help="define subject")
        ]
        if argument in _type:
            if argument is "csr":
                pass
            elif argument is "p12":
                options = [
                    click.option('-c', '--config', is_flag=True,
                                 help="Use config.ini, if you use csv, column 'serial' required"),
                ]
        return functools.reduce(lambda x, opt: opt(x), options, f)
    return inner_options


def folder_options(f):
    """Define certificate folder options and csv file
    """
    options = [
        click.option("-cert", "--cert-folder",
                     type=str,
                     help="Define path to save generated csr and p12, default is {p}"
                     .format(p=os.path.join(Tools().app_folder, "certificate"))),
    ]
    return functools.reduce(lambda x, opt: opt(x), options, f)


def csv_options(absolute=True):
    """Define csv and absolute options
    """
    def inner_options(f):
        options = [
            click.option('-csv', '--csv-file', type=str,
                     help="Define csv, if not use '-a', it will use serial.csv (default csv of app)"),
            click.option('-a', '--absolute', is_flag=True, help="use absolute path of csv"),
        ]
        if not absolute:
            options = [
                click.option('-csv', '--csv-file', type=str,
                             help="Define csv file, it will search file in certificate folder"),
            ]
        return functools.reduce(lambda x, opt: opt(x), options, f)
    return inner_options


def pass_logger(func):
    """Marks a callback as wanting to receive the logger
    object as first argument
    """
    def wrapper(*args, **kwargs):
        return func(Tools().get_logger(), *args, **kwargs)
    return update_wrapper(wrapper, func)