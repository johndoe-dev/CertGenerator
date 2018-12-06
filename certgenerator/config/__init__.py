import os
import ConfigParser


class Config:
    def __init__(self):
        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.config_ini = os.path.join(self.basedir, "config.ini")

        self.config_parser = ConfigParser.RawConfigParser()
        if os.path.exists(self.config_ini):
            self.config_parser.read(self.config_ini)
        else:
            raise Exception("config File doesn't exist")

    def get_section(self, section=None):
        """
        return a dir of all section name
        :param section: if value is not none, return a directiory of all options of the specified setcion
        :return:
        """
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
        except TypeError as e:
            return None
        except KeyError as e:
            return None

    def add(self, section, option, value):
        """
        Create a section if not exist, and add option
        :param section:
        :param option:
        :param value:
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.read(self.config_ini)
        try:
            config.add_section(section=section)
        except ConfigParser.DuplicateSectionError:
            pass
        config.set(section, option, value)
        with open(self.config_ini, "w") as f:
            config.write(f)

    def remove_section(self, section):
        """
        Remove an entire section
        :param section:
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.read(self.config_ini)
        config.remove_section(section)
        with open(self.config_ini, "w") as f:
            config.write(f)

    def remove_option(self, section, option):
        """
        Remove option from section
        :param section:
        :param option:
        :return:
        """
        config = ConfigParser.RawConfigParser()
        config.read(self.config_ini)
        config.remove_option(section, option)
        with open(self.config_ini, "w") as f:
            config.write(f)