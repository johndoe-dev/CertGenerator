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
            click.option('-f', '--force', is_flag=True, help="Overwrite existing file"),
            click.option('-ks', '--key-size', type=click.Choice(['1024', '2048', '4096']),
                         help="Define key size", show_choices=True),
            click.option('-sa', '--san', multiple=True, type=str,
                         help="Add Subject Alt Name (ex: --san test.com --san test1.com ...)"),
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
                    click.option('-f', '--force', is_flag=True, help="Overwrite existing file"),
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
        click.option("-y", "--yaml",
                     is_flag=True,
                     help="Copy and edit Yaml file in generated path")
    ]
    return functools.reduce(lambda x, opt: opt(x), options, f)


def csv_options(f):
    """Define csv options
    """
    options = [
        click.option('-csv', '--csv-file', type=str,
                     help="Define csv file, if only name is defined, it will search in csv folder of app directory"),
    ]

    return functools.reduce(lambda x, opt: opt(x), options, f)


def pass_logger(func):
    """Marks a callback as wanting to receive the logger
    object as first argument
    """
    def wrapper(*args, **kwargs):
        return func(Tools().get_logger(), *args, **kwargs)
    return update_wrapper(wrapper, func)