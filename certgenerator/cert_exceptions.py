class NoFolderException(Exception):
    """
    Raise for folder exception
    """
    pass


class NoFileException(Exception):
    """
    Raise for file exception
    """
    pass


class BadPathException(Exception):
    """
    Raise for Path exception
    """
    pass


class BadExtensionException(Exception):
    """
    Raise for file extension
    """
    pass


class NoConfigException(Exception):
    """
    Raise config exception
    """
    pass


class FileAlreadyExists(Exception):
    """
    Raise File already exists exception
    """
    pass
