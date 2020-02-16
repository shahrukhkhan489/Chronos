![demopic](img/chronos_logo.png)

![](https://img.shields.io/github/license/timelyart/chronos?style=for-the-badge)
![](https://img.shields.io/github/repo-size/timelyart/chronos?style=for-the-badge)
![](https://img.shields.io/github/commit-activity/y/timelyart/chronos?style=for-the-badge)
![](https://img.shields.io/twitter/follow/timelyart?style=for-the-badge)




# Chronos

Chronos is a trading bot, written in python that allows users to place trades with [Kairos](https://github.com/timelyart/Kairos) and tradingview's webhook alerts.

---

## Quickstart

### Installation

* Install setuptools 
```
pip install setuptools
pip install --upgrade setuptools   
```
* Install Chronos dependencies by runing the following command from the Chronos directory:
```
python setup.py install
```
* Start the flask app by running the following command from the Chronos directory:
```
python main.py
```
NOTE: you'll need to have ngrok setup before you can run Chronos (see below)

### Using ngrok for webook data retrieval
Many people are having difficulties with their server properly receiving webhook data from TradingView. The easiest way to get started quickly without ripping your hair out from trying to figure out what's wrong, [ngrok](https://ngrok.com/) can be used to receive the signals. Create a free account, unless you want your server to go down every 8 hours. Navigate to the downloads page, and select your download to match your machine. For example, I am on Ubuntu: `wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip`

### Quick Start Guide
[Here is a quick start guide!](https://github.com/Robswc/tradingview-webhooks-bot/wiki/Quick-Start-Guide) Once everything is set up, you can use this guide to get started!
