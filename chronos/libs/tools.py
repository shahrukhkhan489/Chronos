# File: libs.py
import itertools
import math
import os
import re
import sys
import time
from ast import literal_eval
from collections import OrderedDict, defaultdict
from configparser import RawConfigParser
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

from cryptography.fernet import Fernet

from chronos.libs import debug
import psutil
import yaml

float_precision = 8


# noinspection PyShadowingNames
def create_log(mode='a'):
    return debug.create_log(mode)


def write_console_log(browser, mode='a'):
    return debug.write_console_log(browser, mode)


def shutdown_logging():
    debug.shutdown_logging()


def get_config():
    script_dir = Path(Path(Path(os.path.abspath(__file__)).parent).parent).parent
    config = RawConfigParser(allow_no_value=True, strict=False, empty_lines_in_values=False, dict_type=ConfigParserMultiValues, converters={"list": ConfigParserMultiValues.getlist})
    config_file = os.path.join(script_dir, "chronos.cfg")
    if os.path.exists(config_file):
        try:
            config.read(config_file)
        except Exception as e:
            print(e)
    else:
        print("Configuration file '{}' not found".format(config_file))
        exit(0)
    return config


def chunks(collection, size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(collection), size):
        yield collection[i:i + size]


class ConfigParserMultiValues(OrderedDict):

    def __setitem__(self, key, value):
        if key in self and isinstance(value, list):
            self[key].extend(value)
        else:
            super().__setitem__(key, value)

    @staticmethod
    def getlist(value):
        value = str(value).strip().replace('\r\n', '\n')
        value = value.replace('\r', '\n')
        result = str(value).split('\n')
        return result


class Switch:
    def __init__(self, value): self._val = value

    def __enter__(self): return self

    # Allows traceback to occur
    # noinspection PyShadowingBuiltins
    def __exit__(self, type, value, traceback): return False

    def __call__(self, *mconds): return self._val in mconds


def to_csv(log, data, delimeter=','):
    result = ''
    log.info(str(type(data)) + ': ' + str(data))
    if isinstance(data, dict):
        for _key in data:
            if result == '':
                result = to_csv(log, data[_key])
            else:
                result = delimeter + to_csv(log, data[_key], delimeter)
    elif isinstance(data, list):
        for item in data:
            if result == '':
                result = to_csv(log, item)
            else:
                result = delimeter + to_csv(log, item, delimeter)
    else:
        result = data
    return result


def get_timezone():
    timestamp = time.time()
    date_utc = datetime.utcfromtimestamp(timestamp)
    date_local = datetime.fromtimestamp(timestamp)
    date_delta = max(date_utc, date_local) - min(date_utc, date_local)
    timezone = '{0:0{width}}'.format(int(date_delta.seconds / 60 / 60), width=2) + '00'
    if date_local > date_utc:
        timezone = '+' + timezone
    elif date_local < date_utc:
        timezone = '-' + timezone
    return timezone


def get_time_offset():
    timestamp = time.time()
    date_utc = datetime.utcfromtimestamp(timestamp)
    date_local = datetime.fromtimestamp(timestamp)
    date_delta = date_local - date_utc
    return date_delta


def dt_parse(t):
    ret = datetime.strptime(t[0:16], '%Y-%m-%dT%H:%M')
    if t[17] == '+':
        ret -= timedelta(hours=int(t[18:20]), minutes=int(t[20:]))
    elif t[17] == '-':
        ret += timedelta(hours=int(t[18:20]), minutes=int(t[20:]))
    return ret


def remove_empty_lines(text):
    return "".join([s for s in text.splitlines(True) if s.strip("\r\n")])


def get_yaml_config(file, log, root=False):
    # get the user defined settings file
    result = None
    string_yaml = ""
    try:
        with open(file, 'r') as stream:
            try:
                temp_yaml = yaml.safe_load(stream)
                string_yaml = yaml.dump(temp_yaml, default_flow_style=False)
                snippets = re.findall(r"^(\s*-?\s*)({?)(file:\s*)([\w/\\\"'.:>-]+)(}?)$", string_yaml, re.MULTILINE)
                if root:
                    log.debug(snippets)
                for i in range(len(snippets)):
                    indentation = str(snippets[i][0]).replace("-", " ")
                    search = snippets[i][1] + snippets[i][2] + snippets[i][3] + snippets[i][4] + ""
                    filename = os.path.join(os.path.dirname(file), snippets[i][3])
                    if not os.path.exists(filename):
                        log.error("File '" + str(snippets[i][3]) + "' does not exist. Please update the value in '" + str(os.path.basename(file)) + "'")
                        exit(1)
                    # recursively find and replace snippets
                    snippet_yaml = get_yaml_config(filename, log)
                    string_snippet_yaml = yaml.dump(snippet_yaml, default_flow_style=False)

                    # split snippet yaml into lines (platform independent)
                    lines = string_snippet_yaml.splitlines(True)
                    for j in range(len(lines)):
                        # don't indent the first line, only indent the 2nd line and above
                        if j > 0:
                            lines[j] = indentation + lines[j]
                    # join the lines again to form the yaml with indentation
                    string_snippet_yaml = "".join(lines)
                    # some debugging info
                    log.debug(search)
                    log.debug(string_snippet_yaml)
                    # replace the search value with the snippet
                    string_yaml = string_yaml.replace(search, string_snippet_yaml, 1)

                # clear any empty lines
                string_yaml = remove_empty_lines(string_yaml)
                log.debug(string_yaml)
                result = yaml.safe_load(string_yaml)
            except yaml.YAMLError as err_yaml:
                log.exception(err_yaml)
                f = open(file + ".err", 'w')
                f.write(string_yaml)
                f.close()
        if root:
            f = open(file + '.tmp', 'w')
            f.write(yaml.dump(result))
            f.close()
    except FileNotFoundError as err_file:
        log.exception(err_file)
    except OSError as err_os:
        log.exception(err_os)
    return result


time_intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )


def display_time(seconds, granularity=2):
    result = []

    for name, count in time_intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(int(value), name))
    return ', '.join(result[:granularity])


def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier


def chmod_r(path, permission):
    """
    Set permissions recursively for POSIX systems
    :param path: the file/directory to set permissions for
    :param permission: octal integer, e.g. 0o755 to set permission 755
    :return:
    """
    if os.name == 'posix' or sys.platform == 'os2':
        os.chmod(path, permission)
        for dir_path, dir_names, file_names in os.walk(path):
            for name in dir_names:
                os.chmod(os.path.join(dir_path, name), permission)
            for name in file_names:
                os.chmod(os.path.join(dir_path, name), permission)


def format_number(value, precision=8):
    global float_precision
    float_precision = precision
    result = value
    if isinstance(value, int):
        result = value
    elif isinstance(value, float):
        negative = value < 0
        if result.is_integer():
            result = int(result)
            if result == 0 and negative:
                result = result * -1
        else:
            result = round_up(result, precision)

    return result


def wait_for(condition_function, timeout=5):
    start_time = time.time()
    while time.time() < start_time + (timeout / 0.01):
        if condition_function():
            return True
        else:
            time.sleep(0.01)
    raise Exception(
        'Timeout waiting for {}'.format(condition_function.__name__)
    )


def path_in_use(path, log=None):
    for process in psutil.process_iter():
        try:
            if process.name().find('chrome') >= 0:
                files = process.open_files()
                if files:
                    for f in files:
                        # log.info("{}\t{}".format(message, f.path))
                        if f.path.find(path) >= 0:
                            return True
        # This catches a race condition where a process ends
        # before we can examine its files
        except Exception as e:
            if log:
                log.exception(e)
            else:
                debug.log("ERROR", "path_in_use", e)
    return False


def get_operating_system():
    result = 'windows'
    if sys.platform == 'os2':
        result = 'macos'
    elif os.name == 'posix':
        result = 'linux'
    return result


# Generate unique token from pin.  This adds a marginal amount of security.
def get_token(password):
    token = hashlib.sha224(password.encode('utf-8'))
    return token.hexdigest()


def find_files_and_folders(filename, a_dir=os.curdir):
    """
    Find files and/or folders on the basis of (a part of) a filename
    :param filename: the filename
    :param a_dir: the directory to search, os.curdir by default
    :return: found dirs (array), and found files (array)
    """
    files = []
    dirs = []
    for x in os.walk(a_dir):

        root = x[0]
        for name in x[1]:
            if name.find(filename) >= 0:
                result = os.path.join(str(root), str(name))
                dirs.append(result)
        for name in x[2]:
            if name.find(filename) >= 0:
                result = os.path.join(str(root), str(name))
                files.append(result)
    return dirs, files


def get_immediate_subdirectories(a_dir=os.curdir):
    """
    Get the immediate subdirectories of a given dir
    :param a_dir: the directory to search, os.curdir by default
    :return: the found subdirectories (array)
    """
    return [f.name for f in os.scandir(a_dir) if f.is_dir()]


def get_int(number):
    """
    Converts a numerical str into an integer.Return None, if the string is not an integer
    https://stackoverflow.com/questions/1265665/how-can-i-check-if-a-string-represents-an-int-without-using-try-except
    :param number: String representation of the number
    :return: The int value of the string, e.g 0.0 return 0, or None when the string is not an integer (e.g. 0.1)
    """
    splits = number.split('.')
    if len(splits) > 2:
        # too many splits
        return None
    if len(splits) == 2 and splits[1]:
        # handle decimal part recursively :-)
        if get_int(splits[1]) != 0:
            return None

    int_part = splits[0].lstrip("+")
    if int_part.startswith('-'):
        # handle minus sign recursively :-)
        return get_int(int_part[1:]) * -1
    # successful 'and' returns last truth-y value (cast is always valid)
    return int_part.isdigit() and int(int_part)


def is_int(s):
    with suppress(ValueError, SyntaxError):
        return isinstance(literal_eval(s), int)
    return False


def string_to_key(s):
    """
    See https://stackoverflow.com/questions/55105045/python-invalid-base64-encoded-string-number-of-data-characters-5-cannot-be-1
    :param s:
    :return:
    """
    import base64
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    # password = b"password"
    s = s.encode("UTF-8")
    # s = b"blavla"
    hkdf = HKDF(
        algorithm=hashes.SHA256(),  # You can swap this out for hashes.MD5()
        length=32,
        salt=None,    # You may be able to remove this line but I'm unable to test
        info=None,    # You may also be able to remove this line
        backend=default_backend()
    )
    key = hkdf.derive(s)
    return base64.urlsafe_b64encode(key)


def decrypt(msg, password):
    key = password
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
        print(msg)
    if isinstance(password, str):
        key = string_to_key(password)
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(msg)


def encrypt(msg, password):
    password = password
    key = password
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
    if isinstance(password, str):
        key = string_to_key(password)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(msg)


def utf8len(s):
    return len(s.encode('utf-8'))


def merge(shared_key, *iterables):
    result = defaultdict(dict)
    for dictionary in itertools.chain.from_iterable(iterables):
        result[dictionary[shared_key]].update(dictionary)
    for dictionary in result.values():
        dictionary.pop(shared_key)
    return result
