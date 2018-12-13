import os
import ConfigParser
import click
try:
    from certgenerator.cert_exceptions import NoConfigException
except ImportError:
    import sys
    sys.path.append("/..")
    from cert_exceptions import NoConfigException


class Config:
    def __init__(self):
        self.here = os.path.abspath(os.path.dirname(__file__))
        self.basedir = os.path.dirname(self.here)
        self.config_ini = os.path.join(self.here, "config.ini")
        self.config_parser = ConfigParser.RawConfigParser()
        try:
            self.read_config_ini()
        except NoConfigException as e:
            click.echo("{e}\n".format(e=e))
            raise click.Abort()
        self.default_csv_file = os.path.join(self.here, self.get("config", "csvfile"))
        self.yaml_file = os.path.join(self.here, self.get("config", "yamlfile"))

    def read_config_ini(self):
        """
        Read config.ini
        :return:
        """
        if os.path.exists(self.config_ini):
            self.config_parser.read(self.config_ini)
        else:
            raise NoConfigException("config File {f} doesn't exist".format(f=self.config_ini))

    def get_section(self, section=None):
        """
        return a dir of all section name
        :param section: if value is not none, return a directiory of all options of the specified setcion
        :return:
        """
        # self.read_config_ini()
        if section:
            try:
                items = self.config_parser.items(section)
                _dir = {}
                for item in items:
                    _dir[item[0]] = item[1]
                return _dir
            except ConfigParser.NoSectionError:
                return None
        else:
            return self.config_parser.sections()

    def get_all(self):
        """
        Return a dir of all section and options
        :return:
        """
        sections = {}
        for section in self.get_section():
            sections.update({section: self.get_section(section=section)})
        return sections

    def get(self, section, key):
        """
        return a value of an option from a section
        :param section:
        :param key:
        :return:
        """
        try:
            return self.get_section(section)[key]
        except TypeError:
            return None
        except KeyError:
            return None

    def add(self, section, option, value):
        """
        Create a section if not exist, and add option
        :param section:
        :param option:
        :param value:
        :return:
        """
        # self.read_config_ini()
        try:
            self.config_parser.add_section(section=section)
        except ConfigParser.DuplicateSectionError:
            pass
        self.config_parser.set(section, option, value)
        self.write_config_ini()

    def remove_section(self, section):
        """
        Remove an entire section
        :param section:
        :return:
        """
        self.read_config_ini()
        self.config_parser.remove_section(section)
        self.write_config_ini()

    def remove_option(self, section, option):
        """
        Remove option from section
        :param section:
        :param option:
        :return:
        """
        self.read_config_ini()
        self.config_parser.remove_option(section, option)
        self.write_config_ini()

    def write_config_ini(self):
        """
        Edit config ini
        :return:
        """
        try:
            with open(self.config_ini, "w") as f:
                self.config_parser.write(f)
        except IOError as e:
            click.echo("{e}\nFailed to edit config.ini\nTry to use sudo cert".format(e=e))
            raise click.Abort()
