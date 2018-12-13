import os
import ruamel.yaml
import time
import csv
import logging
import logging.handlers
import click
import platform
import shutil
import subprocess
from codecs import open as c_open
from config import Config
from cert_exceptions import *

here = os.path.abspath(os.path.dirname(__file__))
yaml = ruamel.yaml.YAML()


def edit_config(cert_folder, csv_file, _yaml):
    """
    add or edit app folder or/and csv_file or/and yaml
    :param cert_folder:
    :param csv_file:
    :param _yaml:
    :return:
    """
    tools = Tools()
    base_cert_directory = tools.app_folder
    base_csv_file = tools.config.default_csv_file

    if cert_folder:
        base_cert_directory = cert_folder

    try:
        tools.add_custom_folder(base_cert_directory, "cert_directory")
    except BadPathException as e:
        tools.error(e)
    except NoFolderException as e:
        tools.error(e)

    if csv_file:
        base_csv_file = csv_file

    else:
        try:
            base_csv_file = tools.get_config("custom")["csv"]
        except KeyError:
            pass
        except TypeError:
            pass

    try:
        tools.add_csv_file(base_csv_file, "csvfile", ext="csv")
    except NoFileException as e:
        tools.error(e)
    except BadExtensionException as e:
        tools.error(e)

    if _yaml:
        tools.write_yaml()
    else:
        try:
            tools.add_config_file()
        except NoFileException as e:
            tools.error(e)
        except BadExtensionException as e:
            tools.error(e)


def get_subject():
    fields = ["C", "CN", "ST", "L", "O", "OU", "emailAddress", "san"]
    subject = {}
    for field in fields:
        res = validate_subject(field)
        if res == "-" or res == "":
            continue
        subject[field] = res
    return subject


def validate_subject(field):
    """
    Validate subject
    :param field:
    :return:
    """
    if field is "C":
        c = str(click.prompt("Enter your Country Name (2 letter code) (put \"-\" to keep empty)",
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
            click.prompt("Enter your Common Name (eg, DNS name) (put \"-\" to keep empty)",
                         default=platform.node(), show_default=True))

    elif field is "ST":
        return str(click.prompt("Enter your State or Province <full name> (put \"-\" to keep empty)",
                                default="France", show_default=True))

    elif field is "L":
        return str(click.prompt("Enter your (Locality Name (eg, city) (put \"-\" to keep empty)",
                                default="Paris", show_default=True))

    elif field is "O":
        return str(
            click.prompt("Enter your Organization Name (eg, company) (put \"-\" to keep empty)",
                         default="Enterprise", show_default=True))

    elif field is "OU":
        return str(click.prompt("Enter your Organizational Unit (eg, section) (put \"-\" to keep empty)",
                                default="IT", show_default=True))

    elif field is "emailAddress":
        return str(click.prompt("Enter your email address (put \"-\" to keep empty)",
                                default="{n}@localhost.fr".format(n=platform.node()), show_default=True))

    elif field is "san":
        return str(click.prompt("Enter Subject Alt name (san) separate by space (ex: test.com test2.com ...)"
                                " (put \"-\" to keep empty)"))


class Tools:
    def __init__(self):
        self.here = here
        self.basedir = os.path.dirname(self.here)
        self.opts = Options()
        self.config = Config()
        self.about = self.get_app_info()
        self.documents = os.path.join(os.environ["HOME"], "Documents")
        self.app_folder = os.path.join(self.documents, self.get_app_info("__title__"))
        self.csv_folder = os.path.join(self.app_folder, "csv")
        self.yaml_file = os.path.join(self.app_folder, self.config.yaml_file.split("/")[-1])
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
        self.makedir(self.app_folder)

    def load_config(self):
        """
        load custom app folder
        :return:
        """
        try:
            if "cert_directory" in self.config.get_section(self.custom_section):
                self.app_folder = self.config.get(self.custom_section, "cert_directory")
                self.csv_folder = os.path.join(self.app_folder, "csv")
                self.yaml_file = os.path.join(self.app_folder, self.config.yaml_file.split("/")[-1])
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
        self.makedir(log)
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
        message = "App directory created: {p}".format(p=folder)
        if os.path.exists(folder):
            if os.path.isdir(folder):
                self.config.add(self.custom_section, option, folder)
                self.load_config()
                message = "App directory selected: {p}".format(p=folder)
            else:
                raise NoFolderException("path: {p} is not a directory".format(p=folder))
        else:
            try:
                self.makedir(folder)
                self.config.add(self.custom_section, option, folder)
                self.load_config()
            except OSError:
                self.error("Impossible to create app folder\n"
                           "Make sure you spell the path well: {p}".format(p=folder))

        self.makedir(self.csv_folder)
        click.echo(message)

    def add_csv_file(self, _file, option=None, ext="csv"):
        """
        Add csv file in config ini and add file in path folder
        :param _file:
        :param option:
        :param ext:
        :return:
        """
        absolute = True
        source = ""
        destination = ""
        message = ""
        if len(_file.split("/")) == 1:
            absolute = False
        self.load_config()

        if absolute:
            if os.path.exists(_file) and os.path.isfile(_file):
                if self.check_extension(_file, ext):
                    source = _file
                    destination = self.csv_folder
                    message = "copy {s} to {d}"\
                        .format(s=_file.split('/')[-1], d=os.path.join(self.csv_folder, _file.split('/')[-1]))
            else:
                raise NoFileException("path: {p} doesn't exist".format(p=_file))

        else:
            if self.check_extension(_file, ext):
                source = self.config.default_csv_file
                destination = os.path.join(self.csv_folder, _file.split("/")[-1])
                message = "add csv: {f} in app directory: {p}"\
                    .format(f=_file.split("/")[-1], p=self.csv_folder)

        try:
            self.copy_file(source, destination, message)
        except FileAlreadyExists as e:
            click.echo("{e} => file selected".format(e=e))

        if option:
            self.config.add(self.custom_section, option, _file.split("/")[-1])

    def add_config_file(self):
        """
        Add config file in path folder
        :return:
        """
        try:
            self.load_config()
            source = self.config.yaml_file
            destination = self.yaml_file
            message = "add yaml: {f} in app directory: {p}".format(f=source.split('/')[-1], p=self.app_folder)
            self.copy_file(self.config.yaml_file, destination, message=message)
        except FileAlreadyExists as e:
            click.echo("{e} => already added".format(e=e))

    @staticmethod
    def copy_file(source, destination, message=None):
        """
        copy file
        :param source:
        :param destination:
        :param message:
        :return:
        """
        if os.path.isfile(destination):
            if not os.path.exists(destination):
                pass
            else:
                raise FileAlreadyExists("file {p} already exists".format(p=destination))
        else:
            if not os.path.exists(os.path.join(destination, source.split("/")[-1])):
                pass
            else:
                raise FileAlreadyExists("file {p} already exists"
                                    .format(p=os.path.join(destination, source.split("/")[-1])))
        shutil.copy2(source, destination)
        if message:
            click.echo(message)

    def create_csv_file(self, _file):
        """
        Create csv file
        :param _file:
        :return:
        """
        csv_data = [["serial"], ["1234"]]
        if not os.path.exists(_file):
            with open(os.path.join(self.csv_folder, _file), 'w') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(csv_data)

    @staticmethod
    def makedir(path):
        """
        Create directory with all rights
        :param path:
        :return:
        """
        if not os.path.exists(path):
            os.mkdir(path)
            os.chmod(path, 0777)

    @staticmethod
    def check_extension(_file, ext):
        """
        check extension of given file
        :param _file:
        :param ext:
        :return:
        """
        file_name, file_ext = os.path.splitext(_file)
        if ext in file_ext:
            return True
        raise BadExtensionException("file {f}: Extension {e} is expected, \"{g}\" given"
                                    .format(f=_file, e=ext, g=file_ext))

    def write_yaml(self):
        """
        Write yaml in app folder
        :return:
        """
        yaml_file = os.path.join(self.app_folder, self.config.yaml_file.split("/")[-1])
        old_yaml = "{f}_{t}".format(f=yaml_file, t=time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time())))
        if self.app_folder_exists():
            if os.path.exists(yaml_file):
                click.echo("\nRename {f} to {n_f}".format(f=yaml_file.split("/")[-1], n_f=old_yaml.split("/")[-1]))
                os.rename(yaml_file, old_yaml)
            click.echo("configure csr.yaml\n")
            subject = get_subject()
            with open(yaml_file, "w") as f:
                yaml.dump(subject, f)
            click.echo("\ncsr.yaml has been configured")
        else:
            self.error("app folder: {p} doesn't exist\nTry \"cert init\" or \"cert config edit\" to create app folder"
                       .format(p=self.app_folder))

    def read_yaml(self):
        """
        Read yaml file from app folder
        :return:
        """
        yaml_file = os.path.join(self.app_folder, self.config.yaml_file.split("/")[-1])
        if self.app_folder_exists():
            if not os.path.exists(yaml_file):
                self.add_config_file()
            with open(yaml_file) as f:
                yaml_conf = yaml.load(f)
            return yaml_conf
        else:
            self.error("app folder: {p} doesn't exist\nTry \"cert init\" or \"cert config edit\" to create app folder"
                       .format(p=self.app_folder))

    def app_folder_exists(self):
        """
        Check is app folder path exists
        :return:
        """
        if os.path.exists(self.app_folder):
            return True
        return False

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

    @staticmethod
    def shell(cmd, strip=True, silent=True):
        """
        write and return result of shell cmd
        :param cmd:
        :param strip:
        :param silent:
        :return:
        """
        if not silent:
            click.echo('> {}' + cmd)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        if process.wait() == 0:
            if strip:
                return process.communicate()[0].rstrip()
            return process.communicate()[0]
        return ''


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


