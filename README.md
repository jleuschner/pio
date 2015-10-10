# pio
A Python IO-Server for Raspberry Pi

### Install
- clone This repository to /usr/local
- cd /pio
- edit pio.py (PROMPT, pinning, etc... )
- start ./pio.py
- connect to ip:port - Enjoy!

#### Install as Service:
- cp pio_initd /etc/initd
- sudo update-rc.d pio defaults
