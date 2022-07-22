import json
import os
import urllib.parse
from datetime import datetime
from enum import Enum
from random import choice
from types import SimpleNamespace
from colorama import Fore as Color


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class ResourceMode(Enum):
    CYCLE = 0
    ONE_TIME_USE = 1


class Resource:
    def __init__(self, resource: list, resource_mode: ResourceMode):
        self._bad_items = []
        self._resource = resource
        self._mode = resource_mode
        self._pointer = 0

    def get_resource(self):
        return self._resource

    def get_bad_items(self):
        return self._bad_items

    def get_random(self):
        return choice(self._resource) if len(self._resource) > 0 else None

    def combine(self, resource):
        bi = resource.get_bad_items()
        for bad_item in bi:
            self._bad_items.append(bad_item)
        rs = resource.get_resource()
        for item in rs:
            self._bad_items.append(item)

    def add_bad_items(self, bad_item):
        self._bad_items.append(bad_item)

    def add_bad_item(self, bad_item):
        self._bad_items.append(bad_item)

    def get(self):
        while True:
            if self._pointer < len(self._resource):
                if self._resource[self._pointer] in self._bad_items:
                    self._pointer += 1
                    continue
                return self._resource[self._pointer]
            else:
                if self._mode == ResourceMode.CYCLE:
                    if self._count_available() == 0:
                        return None
                    self._pointer = 0
                    continue
                else:
                    return None

    def _count_available(self):
        count = 0
        for res in self._resource:
            if res not in self._bad_items:
                count += 1
        return count

    def __len__(self):
        return self._count_available()


def LoadLinesAsResource(filename, resource_mode: ResourceMode) -> Resource:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as fh:
            lines = [x.strip() for x in fh if x.strip() != '']
        return Resource(lines, resource_mode)
    else:
        file = open(filename, "x")
        file.close()
        return Resource([], resource_mode)


def LoadLinesAsResourceWithFunction(filename, resource_mode: ResourceMode, function) -> Resource:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as fh:
            lines = [function(x.strip()) for x in fh if x.strip() != '']
        return Resource(lines, resource_mode)
    else:
        file = open(filename, "x")
        file.close()
        return Resource([], resource_mode)


def load_config(filename, structure: dict | None = None):
    # config = json.load(open('./config.json', 'r', encoding='utf-8'), object_hook=lambda d: SimpleNamespace(**d))
    if not os.path.exists(filename):
        with open(filename, mode='x', encoding='utf-8') as file:
            if structure:
                file_structure = {}
                for name, description in structure.items():
                    file_structure.update({
                        name: None,
                    })
                    if description:
                        file_structure.update({
                            f'{name}_description': description
                        })
                file.write(json.dumps(file_structure, indent=4, ensure_ascii=False))
    config = json.load(open(filename, 'r', encoding='utf-8'), object_hook=lambda d: SimpleNamespace(**d))
    missing_keys = []
    if structure:
        for key in structure.keys():
            if key not in config.__dict__.keys():
                missing_keys.append(key)
        if len(missing_keys) > 0:
            keys = ','.join(missing_keys)
            log(f'[ КОНФИГ ] - Отсутсвуют ключи: {keys}', log_type=LogType.Warning)
    return config


class LogType(Enum):
    Warning = Color.LIGHTYELLOW_EX
    Success = Color.LIGHTGREEN_EX
    Error = Color.RED
    Regular = Color.LIGHTWHITE_EX
    Debug = Color.LIGHTBLUE_EX
    Info = Color.WHITE


def log(data: str, log_that: bool = False, additional_data: str = "", color: Color = None,
        filename: str = "log.txt", log_type: LogType = LogType.Regular):
    time = datetime.now().strftime("%H:%M:%S")
    color = color if color else log_type.value
    match log_type:
        case LogType.Error:
            tag = '[ XXX ] '
        case LogType.Warning:
            tag = '[ !!! ] '
        case _:
            tag = ''

    print(f"{color}[ {time} ] : {tag}{data}{Color.RESET}")
    if log_that:
        if not os.path.exists(filename):
            file = open(filename, "x", encoding="utf-8")
        else:
            file = open(filename, "a", encoding="utf-8")

        additional_data = f' | -> Debug data: {additional_data}' if additional_data else ''

        file.write(f"[ {time} ] : {tag}{data}{additional_data}\n")
        file.close()


def urlendcode(string) -> str:
    return urllib.parse.quote_plus(string)


if __name__ == '__main__':
    load_config('config.json', {'tg_token': 'Токен телеграм'})

    log('Ошибка', log_type=LogType.Error, log_that=True)
    log('Предупреждение', log_type=LogType.Warning)
    log('Отладочная информация', log_type=LogType.Debug)
    log('Основной текст', log_type=LogType.Regular)
    log('Информация', log_type=LogType.Info)
    log('Успех', log_type=LogType.Success)
