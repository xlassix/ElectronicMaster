from sys import exit
import platform
import string
from os import popen,path
def getBinDriver()->(str,str):
    """This Function returns the path to a Os appropriate drivet

    Returns:
        str: path to driver
        str: chrome browser executable
    """
    osname = platform.system()
    if osname == 'Darwin':
        installpath = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"## excutable to chromium browser
    elif osname == 'Windows':
        installpath = "C:\Program Files\Google\Chrome\Application\chrome.exe" ## excutable to chromium browser
    elif osname == 'Linux':
        installpath = "/usr/bin/brave" ## excutable to chromium browser
    else:
        raise NotImplemented(f"Unknown OS '{osname}'")

    if not path.isfile(installpath):
        raise Exception("kindly install Chromium Browser Chrome preferable")
    no_digits = string.printable[10:]
    trans = str.maketrans(no_digits, " "*len(no_digits))

    ver = popen(f"{installpath} --version").read().strip('Google Chrome ').strip()
    if ("96." in ver):
        if osname == 'Darwin':
            chrome_driver_binary = path.join("driver","darwin","chromedriver")
        elif osname == 'Windows':
            chrome_driver_binary = path.join("driver","win","chromedriver")
        elif osname == 'Linux':
            print("download the version that match:{0} at https://chromedriver.storage.googleapis.com/index.html?path={0}".format(ver.translate(trans).split()[0]))
            exit()
    elif ("94." in ver and osname == 'Linux'):
        chrome_driver_binary = path.join("driver","linux","chromedriver")
    else:
        print("download the version that match:{0} at https://chromedriver.storage.googleapis.com/index.html?path={0}".format(ver.translate(trans).split()[0]))
        exit()
    return (chrome_driver_binary,installpath)