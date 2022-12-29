import json
import os
import time
import urllib.parse
import threading
from datetime import datetime
from enum import Enum
from random import choice
from types import SimpleNamespace
from colorama import Fore as Color, init
from typing import List
import sys

init()


class DataPath:
    def __init__(self, path: str):
        self.data_path = path.split('.')

    def extract(self, data: dict):
        try:
            for part in self.data_path:
                try:
                    data = data[part]
                except:
                    try:
                        part = int(part)  # TODO: check
                        data = data[part]
                    except:
                        return None
                        pass
            return data
        except:
            return None


# TODO: Custom client
class Struct:
    def __init__(self, entries: dict):
        for k, v in entries.items():
            self.__dict__.update({k: Struct(v)} if type(v) == dict else {k: v})

    def has_key(self, key):
        return key in self.__dict__.keys()

    def get_as_dict(self):
        dictd = {}
        for k, v in self.__dict__.items():
            dictd.update({k: v.__dict__} if type(v) == Struct else {k: v})
        return dictd

    def __str__(self):
        return str(self.__dict__)


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

    def combine(self, resource, duplicate_prevention_function=None, from_start=True):
        bi = resource.get_bad_items()
        for bad_item in bi:
            if duplicate_prevention_function:
                old_bad_item = duplicate_prevention_function(self._bad_items, bad_item)
                if old_bad_item:
                    self._bad_items.remove(old_bad_item)
                self._bad_items.append(bad_item)
            else:
                self._bad_items.append(bad_item)
        rs = resource.get_resource()
        for item in rs:
            if duplicate_prevention_function:
                old_item = duplicate_prevention_function(self._resource, item)
                if old_item:
                    self._resource.remove(old_item)
                self._resource.append(item)
            else:
                self._resource.append(item)
        if from_start:
            self._resource = self._resource[::-1]

    def add_bad_items(self, bad_items, duplicate_prevention_function=None):
        if type(bad_items) == Resource:
            bad_items = bad_items.get_resource()
        elif type(bad_items) == list:
            pass
        else:
            return False

        for bad_item in bad_items:
            if duplicate_prevention_function:
                old_bad_item = duplicate_prevention_function(self._bad_items, bad_item)
                if old_bad_item:
                    self._bad_items.remove(old_bad_item)
                self._bad_items.append(bad_item)
            self._bad_items.append(bad_item)

    def add_bad_item(self, bad_item):
        self._bad_items.append(bad_item)

    def get(self):
        while True:
            if self._pointer < len(self._resource):
                pointer = self._pointer
                self._pointer += 1
                if self._resource[pointer] in self._bad_items:
                    continue
                return self._resource[pointer]
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


def LoadLinesAsResource(filename: str, resource_mode: ResourceMode) -> Resource:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as fh:
            lines = [x.strip() for x in fh if x.strip() != '']
        resource = Resource(lines, resource_mode)
        return resource
    else:
        file = open(filename, "x")
        file.close()
        return Resource([], resource_mode)


def LoadLinesAsResourceWithFunction(filename: str, function,
                                    resource_mode: ResourceMode = ResourceMode.ONE_TIME_USE) -> Resource:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as fh:
            lines = [function(x.strip()) for x in fh if x.strip() != '' and function(x.strip())]
        return Resource(lines, resource_mode)
    else:
        file = open(filename, "x")
        file.close()
        return Resource([], resource_mode)


class ConfigParam:
    def __init__(self, name, description, value_type: type = str):
        self.name = name
        self.value_type = value_type
        self.value = None
        self.description = description

    def set_value(self, value):
        if value:
            self.value = self.value_type(value)
        else:
            self.value = value

    def __dict__(self):
        return {self.name: self.value, f'{self.name}_description': self.description}


def load_config(filename='config.json', structure: List[ConfigParam] | None = None, critical_to_have_all_keys=True):
    # config = json.load(open('./config.json', 'r', encoding='utf-8'), object_hook=lambda d: SimpleNamespace(**d))
    if not os.path.exists(filename):
        with open(filename, mode='x', encoding='utf-8') as file:
            if structure:
                file_structure = {}
                for config_param in structure:
                    config_param.set_value(input(
                        f'В конфиге не задан параметр ({config_param.name}, {config_param.description}), впишите значение: '))
                    file_structure.update(dict(config_param))
                file.write(json.dumps(file_structure, indent=4, ensure_ascii=False))
    config = json.load(open(filename, 'r', encoding='utf-8'), object_hook=lambda d: SimpleNamespace(**d))
    missing_keys = []
    if structure:
        for key in structure.keys():
            if key not in config.__dict__.keys():
                missing_keys.append(key)
        if len(missing_keys) > 0:
            keys = ', '.join(missing_keys)
            log(f'[ КОНФИГ ] - Отсутствуют ключи: {keys}',
                log_type=LogType.Error if critical_to_have_all_keys else LogType.Warning)
            if critical_to_have_all_keys:
                time.sleep(5)
                exit()
    return config


class LogType(Enum):
    Warning = Color.LIGHTYELLOW_EX
    Success = Color.LIGHTGREEN_EX
    Error = Color.RED
    Regular = Color.LIGHTWHITE_EX
    Debug = Color.LIGHTBLUE_EX
    Info = Color.WHITE


def log(data: str, log_that: bool = False, tag: str | None = None, additional_data: str = '', color: Color = None,
        filename: str = 'log.txt', log_type: LogType = LogType.Regular, use_russian=False, use_time=True,
        include_trace=True):
    timestamp = datetime.now().strftime('%H:%M:%S')
    color = color if color else log_type.value
    tag = f'{tag}' if tag else ''
    match log_type:
        case LogType.Error:
            log_tag = '[ ОШИБКА ]' if use_russian else '[ XXX ] '
        case LogType.Warning:
            log_tag = '[ ВНИМАНИЕ ]' if use_russian else '[ !!! ] '
        case _:
            log_tag = ''

    timestamp = f'[ {timestamp} ] : ' if use_time else ''
    print(f'{color}{timestamp}{log_tag}{tag}{data}{Color.RESET}')
    if log_that:
        additional_data = f' | -> Debug data: {additional_data}' if additional_data else ''
        with open(filename, 'a+', encoding='utf-8') as file:
            file.write(f'[ {time} ] : {tag}{data}{additional_data}\n')
            file.close()


class FileWriteInfo:
    def __init__(self, filename):
        self.filename = filename
        self.file_lines = None
        self.refresh_data()
        self._data_to_write = []
        self._data_to_replace = []

    def refresh_data(self):
        with open(self.filename, mode='r') as file:
            self.file_lines = [x.strip() for x in file if x.strip() != '']

    @property
    def needs_to_be_written(self):
        return self._data_to_write

    def write(self, data: str, equality_filter=':', equality_index=0):
        if not data:
            return
        for line in self.file_lines:
            eq1 = line.split(equality_filter)[equality_index]
            eq2 = data.split(equality_filter)[equality_index]
            if eq1 == eq2:
                self._data_to_replace.append([line, data])
        if len(self._data_to_replace) > 0:
            for line, replace in self._data_to_replace:
                self.file_lines[self.file_lines.index(line)] = replace if replace else line
            self._data_to_replace = []
            with open(self.filename, mode='w+') as file:
                file.write('\n'.join(self.file_lines) + '\n')
            self.refresh_data()
        else:
            self._data_to_write.append(data)

    def written(self, data: str):
        self.refresh_data()
        self._data_to_write.remove(data)

    def __eq__(self, other):
        if type(other) == FileWriteInfo:
            return other.filename == self.filename
        else:
            return False


class FileManager:
    def __init__(self):
        self.files = []
        self.sync_pulse = 5
        self._stop = False

    def add_file(self, filename):
        self.files.append(FileWriteInfo(filename))

    def write_to_file(self, filename, data):
        for file in self.files:
            if file.filename == filename:
                file.write(data)

    def start_sync(self):
        thread = threading.Thread(target=self._sync_thread)
        thread.start()

    def stop_sync(self):
        self._stop = True

    def _sync_thread(self):
        local_stop = False
        while True:
            if self._stop:
                local_stop = True
            for file in self.files:
                if len(file.needs_to_be_written) > 0:
                    for data in file.needs_to_be_written:
                        with open(file.filename, mode='a+') as f:
                            f.write(f'{data}\n')
                        file.written(data)
            if local_stop:
                stop = True
                for file in self.files:
                    if len(file.needs_to_be_written) > 0:
                        stop = False
                if stop:
                    self._stop = False
                else:
                    continue
                return
            time.sleep(self.sync_pulse)


def urlendcode(string) -> str:
    return urllib.parse.quote_plus(string)


def list_to_str(separator, data: list):
    return separator.join(data)


if __name__ == '__main__':
    load_config('config.json', {'tg_token': 'Токен телеграм'})

    log('Ошибка', log_type=LogType.Error, log_that=True)
    log('Предупреждение', log_type=LogType.Warning)
    log('Отладочная информация', log_type=LogType.Debug)
    log('Основной текст', log_type=LogType.Regular)
    log('Информация', log_type=LogType.Info)
    log('Успех', log_type=LogType.Success)
