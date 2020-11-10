from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(
    name='Chronos',
    packages=find_packages(),
    license='End-User License Agreement: https://www.eulatemplate.com/live.php?token=0wBzlp7nGlsG4MeC1SLAVR5r40H1dMRv',
    author='timelyart',
    version='0.2',
    author_email='timelyart@protonmail.com',
    description='A bot that can execute trades based on tradingview webhook alerts! Forked from https://github.com/Robswc/tradingview-webhooks-bot',
    long_description=long_description,
    install_requires=['flask', 'PyYAML', 'psutil', 'ccxt', 'jinja2', 'ordereddict', 'simplejson', 'werkzeug', 'wtforms',
                      'sqlalchemy', 'visitor', 'dominate', 'email-validator == 1.0.5', 'cfscrape'],
)
