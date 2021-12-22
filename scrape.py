import pandas as pd
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date, datetime


_dir = "input"
_output_dir = "output"
makedirs(_output_dir, exist_ok=True)


def getTextById(browser: webdriver, _id: str) -> str:
    """This Function Gets Text from the WebDriver Instance that matches the HTML AttributeId

    Args:
        browser (webdriver): Selenium.WebDriver,
        _id(str): id HTMLAttribute

    Returns:
        str: String that matches the query
    """
    return browser.find_element(by=By.ID, value=_id).text.replace(",", "")


def getTextByXPath(browser: webdriver, xpath: str) -> str:
    """This Function Gets Text from the WebDriver Instance that matches the Xpath

    Args:
        browser (webdriver): Selenium.WebDriver,
        _id(str): id HTMLAttribute

    Returns:
        str: String that matches the query
    """
    return browser.find_element(by=By.XPATH, value=xpath).text.replace(",", "")

class Scraper():
    def __init__(self):
        pass
