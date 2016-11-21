# pio
A Python IO-Server for Raspberry Pi

##### IOs:
###### Digital
- Relays or LEDs per direct GPIO

###### PWM
- addressing 12-bit PWM-Driver via I2c with DMX-conform 8-bit adaption ( http://www.adafruit.com/product/815 )

### Prerequirements
- apt-get install python-setuptools
- easy_install -U RPIO
- apt-get install python-smbus

### Install
- clone this repository to /usr/local
- cd /pio
- edit pio.py (PROMPT, pinning, etc... )
- start ./pio.py
- connect to ip:port - Enjoy!

#### Install as Service:
- cp pio_initd /etc/init.d/pio
- sudo update-rc.d pio defaults
