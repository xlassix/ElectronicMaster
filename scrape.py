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

def parseDate(dateStr: str,dateFormat:str="%m/%d/%y") -> date:
    """This function takes a date string in the format `dateFormat` and returns a datetime object

    Args:
        dateStr (str)       : date string Example 5/30/22
        dateFormat (str)    : date format for example "%m/%d/%y"
    Returns:
        date: datetime.date
    """
    return datetime.strptime(dateStr.strip(), dateFormat).date()


def parseFloat(_number: str) -> float:
    """This function takes in a string strips unwanted symbols like $ and + and parses it to a float

    Args:
        _number (str): for example $5.0 or 10000+

    Returns:
        float: 
    """
    return float(_number.strip().strip("+").strip("$"))

class Scraper():
    def __init__(self):
        browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()))

