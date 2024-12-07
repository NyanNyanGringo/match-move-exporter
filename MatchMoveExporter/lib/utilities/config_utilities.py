"""
Library for working with .json configuration files.

If the value conf_file_path is not specified in the functions,
the operations will be performed on the default configuration file.
"""

import json
import os

from MatchMoveExporter.userconfig import UserConfig



class ConfigKeys:
    NAME = "name"
    PROJECT = "project"
    USERNAME = "username"


def setup_config():
    config_path = os.path.dirname(UserConfig.get_config_filepath())
    os.makedirs(config_path, exist_ok=True)


def write_config(key, conf, conf_file_path=UserConfig.get_config_filepath()):
    """
    Записать значение в конфиг-файл в формате ключ-значение.
    :
    :param key: str
    :param conf: any
    :param conf_file_path: str
    :return: True
    """
    config_data = dict()

    if os.path.isfile(conf_file_path):
        f = open(conf_file_path, mode='r')
        config_data = json.load(f)
        f.close()

    config_data[key] = conf

    f = open(conf_file_path, mode='w')
    json.dump(config_data, f, indent=2, sort_keys=True)
    f.close()

    return True


def read_config_key(key, conf_file_path=UserConfig.get_config_filepath()):
    """
    Прочитать значение по ключу из конфига
    :
    :param key: any
    :param conf_file_path: str
    :return: any
    """

    if not check_key(key, conf_file_path):
        raise Exception(f"Config {conf_file_path} or key {key} doesn't exists!")

    f = open(conf_file_path, mode='r')
    config_data_input = json.load(f)
    f.close()

    return config_data_input[key]


def check_key(key, conf_file_path=UserConfig.get_config_filepath()):
    """
    Проверить - существует ли конфинг-файл и есть ли у него ключ
    :
    :param key: any
    :param conf_file_path: str
    :return: bool
    """

    if not os.path.isfile(conf_file_path):
        return False

    f = open(conf_file_path, mode='r')
    config_data_input = json.load(f)
    f.close()

    if key in config_data_input.keys():
        return True
    else:
        return False


def delete_key(key, conf_file_path=UserConfig.get_config_filepath()):
    """
    Удалить ключ и его значение из конфиг-файла
    :
    :param key: any
    :param conf_file_path: str
    :return: bool
    """

    if check_key(key, conf_file_path):
        f = open(conf_file_path, mode='r')
        config_data = json.load(f)
        f.close()

        del config_data[key]

        f = open(conf_file_path, mode='w')
        json.dump(config_data, f, indent=2, sort_keys=True)
        f.close()
        return True
    return False
