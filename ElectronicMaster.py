from selenium import webdriver
from os import listdir, path, makedirs
import pandas as pd
from datetime import datetime
from helper import getBinDriver
options = webdriver.ChromeOptions()

options.binary_location = ""  # set preferred chromium browser[optional]
chrome_driver_binary = ""  # set driver path[optional]

# or Defaults

chrome_driver_binary,options.binary_location=getBinDriver()

# basic input folders
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
    return browser.find_element_by_id(_id).text.replace(",", "")


def getTextByXPath(browser: webdriver, xpath: str) -> str:
    """This Function Gets Text from the WebDriver Instance that matches the Xpath

    Args:
        browser (webdriver): Selenium.WebDriver,
        _id(str): id HTMLAttribute

    Returns:
        str: String that matches the query
    """
    return browser.find_element_by_xpath(xpath).text.replace(",", "")


def getPriceList(browser: webdriver) -> dict:
    """This function get the Price list(dict) For ElectoricMaster.com on a product page

    Args:
        browser (webdriver): [description]

    Returns:
        dict
    """
    data = getTextById(browser, 'divPriceListLeft').split("\n")[3:]
    del data[2::3]
    return(dict(("PB{} Qty".format(index//2+1), i.strip()) if(index % 2 == 0)
                else ("PB{} $".format(index//2+1), i.strip().strip("$")) for index, i in enumerate(data[:20])))


def getMfrDetail(browser: webdriver) -> dict:
    """The function get manafacturers For ElectoricMaster.com on a product page

    Args:
        browser (webdriver): [description]

    Returns:
        dict
    """
    result = {}
    data = getTextByXPath(browser, '//*[@id="divDefault"]/div/div').split("\n")
    data = dict((i, j) for i, j in zip(data[::2], data[1::2]))
    if ("Factory Lead-Time" in data):
        result['Lead-Time'] = data["Factory Lead-Time"].lower().split("weeks")[0]
    if('Manufacturer Stock:' in data):
        [result['Mfr Stock'], result["Mfr Stock Date"]
         ] = data['Manufacturer Stock:'].split('can ship')
    if('On Order:' in data):
        [result['On-Order'], result["On-Order Date"]
         ] = data['On Order:'].split('can ship')
    if('Minimum Order:' in data):
        result["Min Order"] = data['Minimum Order:']
    return result


def getCsvs(path: str) -> [str]:
    return(list(filter(lambda elem: elem.endswith(".csv"), listdir(path))))


# initialise Browser
browser = webdriver.Chrome(chrome_driver_binary, chrome_options=options)


def getItem(item) -> None:
    url = (
        "https://www.masterelectronics.com/en/keywordsearch?text={0}".format(item))
    browser.get(url)
    if(browser.current_url == url):
        browser.find_element_by_xpath(
            '//*[@id="search-content-results"]/div/div[2]/a[1]').click()


_columns = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
            'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order",
            "PB1 Qty", "PB2 Qty", "PB3 Qty", "PB4 Qty", "PB5 Qty", "PB6 Qty", "PB7 Qty", "PB8 Qty",	"PB9 Qty", "PB10 Qty", "PB1 $",	"PB2 $", "PB3 $",	"PB4 $",	"PB5 $",	"PB6 $",	"PB7 $",	"PB8 $",	"PB9 $", "PB10 $",	"URL"]

for csv in (getCsvs(_dir)):
    result_df = pd.DataFrame(columns=_columns)
    timestamp = str(datetime.now())
    raw_data = pd.read_csv(path.join(_dir, csv))
    present_columns = set(raw_data.columns).intersection(
        ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
    if ("Query" in present_columns):
        for row in raw_data.to_dict(orient='records'):
            getItem(row["Query"])
            row['Run Datetime'] = timestamp
            row['Mfr'] = getTextByXPath(
                browser, '//*[@id="product-details"]/a')
            row["Mfr PN"] = getTextByXPath(
                browser, '//*[@id="product-details"]/h1')
            row["Mfr Stock Date"] = getTextById(browser, 'lblDateFactory')
            row["Stock"] = getTextByXPath(
                browser, '//*[@id="divInInstock"]/span')
            row.update(getMfrDetail(browser))
            row.update(getPriceList(browser))
            row["URL"] = browser.current_url
            result_df = result_df.append(row, ignore_index=True, sort=False)
    else:
        print("could not find `Query` in {}".format(csv))
    result_df[_columns].to_csv(
        path.join(_output_dir, timestamp+"_"+csv), index=False)
browser.close()