import os
import logging
import logging.handlers
import click
import platform
import shutil
from codecs import open as c_open
from config import Config
from exception import *

here = os.path.abspath(os.path.dirname(__file__))


def edit_config(cert_folder, csv_file):
    """
    add or edit app folder or/and csv_file
    :param cert_folder:
    :param csv_file:
    :return:
    """
    _config = Tools().get_config()
    base_cert_directory = Tools().app_folder

    if cert_folder:
        base_cert_directory = cert_folder
        try:
            click.echo(Tools().add_custom_folder(base_cert_directory, "cert_directory"))
        except PathException as e:
            Tools().error(e)
        except FolderException as e:
            Tools().error(e)

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
        except ExtensionException as e:
            Tools().error(e)


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
        try:
            self.config.read_config_ini()
        except ConfigException as e:
            self.error("{e}\n".format(e=e))
        self.about = self.get_app_info()
        self.documents = os.path.join(os.environ["HOME"], "Documents")
        self.app_folder = os.path.join(self.documents, self.get_app_info("__title__"))
        self.custom_section = "custom"

        # Set cert folder
        self.load_config()

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
                try:
                    about[i] = open(about[i]).read()
                except IOError:
                    about[i] = ""
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
        """
        load custom app folder
        :return:
        """
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
            self.error("[!] Unable to open log file {f}: {e}\n".format(f=default["log_file"], e=err))

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
        message = "App directory has been created: {p}".format(p=folder)
        if os.path.exists(folder):
            if os.path.isdir(folder):
                self.config.add(self.custom_section, option, folder)
                self.load_config()
                message = "App directory has been selected: {p}".format(p=folder)
            else:
                raise FolderException("path: {p} is not a directory".format(p=folder))
        else:
            # raise PathException("path: {p} doesn't exist".format(p=folder))
            try:
                os.mkdir(folder)
                self.config.add(self.custom_section, option, folder)
                self.load_config()
            except OSError:
                self.error("Impossible to create app folder\n"
                           "Make sure you spell the path well: {p}".format(p=folder))

        return message

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
                raise PathException("path: {p} doesn't exist".format(p=_file))

            if os.path.isfile(_file):
                pass
            else:
                raise FileException("path: {p} is not a file".format(p=_file))

        file_name, file_ext = os.path.splitext(_file)
        if ext in file_ext:
            self.config.add(self.custom_section, option, _file.split("/")[-1])
        else:
            raise ExtensionException("file {f}: Extension {e} is expected, \"{g}\" given"
                                     .format(f=_file, e=ext, g=file_ext))

    def get_options(self):
        return self.opts

    def set_options(self, **kwargs):
        """
        edit or add items (key and value) to options
        :param kwargs:
        :return:
        """
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

    @staticmethod
    def error(message):
        click.echo("\n========ERROR========\n{m}\n========ERROR========\n".format(m=message))
        raise click.Abort


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


