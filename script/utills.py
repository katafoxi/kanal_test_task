import time
from configparser import ConfigParser
from os.path import exists

CONFIG_FILE = "./project_docker.ini"


def get_config(section: str) -> dict:  # sourcery skip: raise-specific-error
    """
    Получает данные из файла project.ini
    :param section:
    :return: словарь '[имя_параметра]':'[значение]'
    """
    if not exists(CONFIG_FILE):
        raise Exception("Отсутствует ini файл")
    parser = ConfigParser()  # create a parser
    parser.read(CONFIG_FILE)  # read configurate file
    if not parser.has_section(section):
        raise Exception(
            "Section {0} is not found in the {1} file.".format(section, CONFIG_FILE)
        )
    params = parser.items(section)
    return {param[0]: param[1] for param in params}


def get_time() -> str:
    """

    :return: date as a string [hour:minute:second]
    """
    return "[" + time.strftime("%H:%M:%S") + "] "
