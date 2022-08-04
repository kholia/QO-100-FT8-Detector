#!/usr/bin/env python

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import re
import os
import sys
import time
import subprocess
import traceback
from datetime import datetime
import sounddevice as sd
from scipy.io.wavfile import write

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from pyvirtualdisplay import Display

virtual_display = True
# virtual_display = False
delay = 45
sd.default.device = "pulse"

fs = 12000

"""
Execute following manually:

pacmd load-module module-null-sink sink_name=Virtual0
pacmd update-sink-proplist Virtual0 device.description=Virtual0
pacmd update-source-proplist Virtual0.monitor device.description=Virtual0

Next, use `pavucontrol` to redirect the audio output of the browser process to
`Virtual0` stream.

Also, connect the input audio stream of this program to `Virtual0` using
pavucontrol.
"""


def decode_loop():
    while True:
        # run every 15 seconds for ~13 seconds
        now = datetime.now()
        ts = now.time()
        # if now % 15 == 0:  # https://eshail.batc.org.uk/nb/ has some delay?
        if now.second % 15 == 1:
            # print("Running the decode loop!")
            data = sd.rec(int(14 * fs), samplerate=fs, channels=1, dtype="int16")
            sd.wait()  # Wait until recording is finished
            write('/tmp/output.wav', fs, data)  # we assume this is tmpfs and mounted in ram storage
            p = subprocess.run("~/repos/ft8_lib/decode_ft8 /tmp/output.wav", capture_output=True, shell=True)
            if p.stdout != b"":
                print("[%s] FT8 is active on QO-100 satellite!" % ts)
        time.sleep(0.05)


def do():
    if virtual_display:
        disp = Display()
        disp.start()

    # Firefox is a 'snap' now on Ubuntu which doesn't work - hence this hack!
    binary = FirefoxBinary(os.path.expanduser("~/apps/firefox/firefox"))  # change this path manually
    driver = webdriver.Firefox(firefox_binary=binary)

    url = "https://eshail.batc.org.uk/nb/"
    driver.get(url)

    # wait for page to load fully
    try:
        _ = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'statinfo0')))
    except TimeoutException:
        traceback.print_exc()

    time.sleep(2)  # ;)

    # Set freqeuncy and volume
    driver.execute_script("setfreqm(b,10489540,'usb',false);")  # "NB digi"
    driver.execute_script("soundapplet.setvolume(Math.pow(10,4/10.));")  # 6 is max, current is 4

    decode_loop()


if __name__ == "__main__":
    do()
