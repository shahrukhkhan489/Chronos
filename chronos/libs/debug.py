# File: debug.py
import logging
import os
import re
import sys

from datetime import datetime

log_path = './log'  # project dir
file_name = 'debug.log'

if not os.path.exists(log_path):
    os.mkdir(log_path)


# noinspection PyArgumentList
def create_log(mode='a'):
    file = os.path.join(r"" + log_path, file_name)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(file, mode=mode),
            logging.StreamHandler(sys.stdout)
        ])
    return logging.getLogger()


def shutdown_logging():
    logging.shutdown()


# noinspection PyBroadException
def load_console_log(browser, log_type):
    try:
        return browser.get_log(log_type)
    except Exception:
        return None


def write_console_log(browser, mode='a'):
    import os
    from chronos.libs import tools
    from datetime import datetime
    from datetime import timedelta

    logs = {
        'browser': load_console_log(browser, 'browser'),
        'driver': load_console_log(browser, 'driver'),
        'server': load_console_log(browser, 'server'),
        'client': load_console_log(browser, 'client'),
        'performance': load_console_log(browser, 'performance')
    }

    match = re.search(r".*(/d+)", file_name)
    postfix = ""
    if match:
        postfix = "_".format(match.group(1))

    offset = tools.get_time_offset()
    for log_name in logs:
        if logs[log_name]:
            fn = "{}{}.log".format(str(log_name), postfix)
            file = os.path.join(r"" + log_path, fn)
            f = open(file, mode)
            lines = logs[log_name]
            for line in lines:
                level = line['level']
                message = line['message']
                timestamp = datetime(1970, 1, 1, ) + timedelta(microseconds=line['timestamp']*1000) + offset
                s_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                # apparently, the webdriver adds a carriage return ('\r') after each entry but no line feed ('\n')
                output = "{} {} \t {} \n".format(s_timestamp, level, message)
                f.write(output)
            f.close()


def log(level, method, msg):
    t = datetime.now()
    ms = t.strftime("%f")[:3]
    print("{}.{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ms), level, method, msg)
