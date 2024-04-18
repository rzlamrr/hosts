#!/bin/bash
sudo apt update

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

sudo apt-get install -y chromium-chromedriver

pip install pyyaml python-whois selenium-wire

sudo apt purge google-chrome-stable
rm google-chrome-stable_current_amd64.deb

python utils/lookup.py
