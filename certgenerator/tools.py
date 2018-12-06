import os
import logging
import logging.handlers
import sys
import click
import platform
import shutil
from codecs import open as c_open
from config import Config
import exception

here = os.path.abspath(os.path.dirname(__file__))


def edit_config(cert_folder, csv_file):
    _config = Tools().get_config()
    base_cert_directory = Tools().app_folder

    if cert_folder:
        base_cert_directory = cert_folder
        try:
            Tools().add_custom_folder(cert_folder, "cert_directory")
        except exception.PathException as e:
            click.echo(e)
            raise click.Abort()
        except exception.FolderException as e:
            click.echo(e)
            raise click.Abort()

    if csv_file:
        try:
            if len(csv_file.split('/')) == 1:
                Tools().add_custom_file(csv_file, "csvfile", ext="csv")
                click.echo("add csv: {f} in directory: {d}".format(f=csv_file, d=base_cert_directory))
            elif len(csv_file.split('/')) > 1:
                Tools().create_certificate_folder()
                Tools().add_custom_file(csv_file, "csvfile", ext="csv", absolute=True)
                csv_folder = os.path.join(base_cert_directory, "csv")
                if not os.path.exists(csv_folder):
                    os.mkdir(csv_folder)
                shutil.copy2(csv_file, csv_folder)
        except exception.ExtensionException as e:
            click.echo(e)
            raise click.Abort()


def validate_subject(field):
    """
    Validate subject
    :param field:
    :return:
    """
    if field is "C":
        c = str(click.prompt("Enter your Country Name (2 letter code) (put \"-\" to fill empty)",
                             default="US", show_default=True))
        if c == "-":
            return c
        try:
            if len(c) != 2:
                raise ValueError(c)
            else:
                return c
        except ValueError, e:
            click.echo('Incorrect country name given , must be 2 letters code: {}'.format(e))
            return validate_subject(field)

    elif field is "CN":
        return str(
            click.prompt("Enter your Common Name (eg, DNS name) (put \"-\" to fill empty)",
                         default=platform.node(), show_default=True))

    elif field is "ST":
        return str(click.prompt("Enter your State or Province <full name> (put \"-\" to fill empty)",
                                default="France", show_default=True))

    elif field is "L":
        return str(click.prompt("Enter your (Locality Name (eg, city) (put \"-\" to fill empty)",
                                default="Paris", show_default=True))

    elif field is "O":
        return str(
            click.prompt("Enter your Organization Name (eg, company) (put \"-\" to fill empty)",
                         default="Enterprise", show_default=True))

    elif field is "OU":
        return str(click.prompt("Enter your Organizational Unit (eg, section) (put \"-\" to fill empty)",
                                default="IT", show_default=True))

    elif field is "emailAddress":
        return str(click.prompt("Enter your email address (put \"-\" to fill empty)",
                                default="{n}@localhost.fr".format(n=platform.node()), show_default=True))


class Tools:
    def __init__(self):
        self.here = here
        self.basedir = os.path.dirname(self.here)
        self.opts = Options()
        self.config = Config()
        self.about = self.get_app_info()
        self.documents = os.path.join(os.environ["HOME"], "Documents")
        self.app_folder = os.path.join(self.documents, self.get_app_info("__title__"))
        self.custom_section = "custom"

        # Set cert folder
        try:
            if "cert_directory" in self.config.get_section(self.custom_section):
                self.app_folder = self.config.get(self.custom_section, "cert_directory")
        except KeyError:
            pass
        except TypeError:
            pass

    @staticmethod
    def get_app_info(item=None):
        """
        Return app info
        :param item:
        :return:
        """
        about = {}
        with c_open(os.path.join(here, "__version__.py"), 'r', 'utf-8') as f:
            exec (f.read(), about)
        for i in about:
            if "__long_description__" in i:
                about[i] = open(about[i]).read()
        if item:
            return about[item]
        return about

    def create_certificate_folder(self):
        """
        Create path of certificate folder if not exist
        :return:
        """
        self.load_config()
        if not os.path.exists(self.app_folder):
            os.mkdir(self.app_folder)

    def load_config(self):
        try:
            if "cert_directory" in self.config.get_section(self.custom_section):
                self.app_folder = self.config.get(self.custom_section, "cert_directory")
        except KeyError:
            pass
        except TypeError:
            pass

    def get_certificate_folder(self):
        """
        Return path of certificate folder and created folder if not exist
        :return:
        """
        self.create_certificate_folder()
        return self.app_folder

    def logger_folder(self):
        """create logger folder"""
        log = os.path.join(self.get_certificate_folder(), "log")
        if not os.path.exists(log):
            os.mkdir(log)
        return log

    def get_logger(self):
        """
        create and return logger
        :return:
        """
        default = self.get_config("default")
        log_file = os.path.join(self.logger_folder(), default["log_file"])
        try:
            logger = logging.getLogger('certgen')
            handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=3)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)
            return logger
        except AttributeError as err:
            sys.stdout.write("[!] Unable to open log file {f}: {e}\n".format(f=default["log_file"], e=err))
            sys.exit(1)

    def get_config(self, section=None):
        """
        Return Config
        :param section:
        :return:
        """
        if section:
            return self.config.get_section(section)
        return self.config

    def add_custom_folder(self, folder, option):
        """
        Add custom folder in config ini
        :param folder:
        :param option:
        :return:
        """
        if os.path.exists(folder):
            if os.path.isdir(folder):
                self.config.add(self.custom_section, option, folder)
                self.app_folder = folder
            else:
                raise exception.FolderException("path: {p} is not a directory".format(p=folder))
        else:
            raise exception.PathException("path: {p} doesn't exist".format(p=folder))

    def add_custom_file(self, _file, option, ext="txt", absolute=False):
        """
        Add custom file in config ini
        :param _file:
        :param option:
        :param ext:
        :param absolute:
        :return:
        """
        if absolute:
            if os.path.exists(_file):
                pass
            else:
                raise exception.PathException("path: {p} doesn't exist".format(p=_file))

            if os.path.isfile(_file):
                pass
            else:
                raise exception.FileException("path: {p} is not a file".format(p=_file))

        file_name, file_ext = os.path.splitext(_file)
        if ext in file_ext:
            self.config.add(self.custom_section, option, _file.split("/")[-1])
        else:
            raise exception.ExtensionException("file {f}: Extension {e} is expected, \"{g}\" given"
                                               .format(f=_file, e=ext, g=file_ext))

    def get_options(self):
        return self.opts

    def set_options(self, **kwargs):
        for k, v in kwargs.items():
            if "config" in k and v is True:
                self.opts.update(config=self.get_config(section="config"))
                continue
            if "san" in k and v:
                self.opts.update(san=[str(i) for i in v])
                continue
            if "size" in k and v:
                self.opts.update(size=int(v))
                continue
            if k and v:
                self.opts[k] = v


class Options(dict):

    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        self.item_list = super(Options, self).keys()

    def __setitem__(self, key, value):
        self.item_list.append(key)
        super(Options, self).__setitem__(key, value)

    def __iter__(self):
        return iter(self.item_list)

    def keys(self):
        return self.item_list

    def values(self):
        return [self[key] for key in self]

    def itervalues(self):
        return (self[key] for key in self)


if __name__ == '__main__':
    t = Tools()
    print t.about


