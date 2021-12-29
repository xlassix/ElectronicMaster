from selenium import webdriver
from os import listdir, path, makedirs
import pandas as pd
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date, datetime


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


def parseDate(_date: str) -> date:
    """This function takes a date string in the format m/d/y and returns a datetime object

    Args:
        _date (str): date string Example 5/30/22
    Returns:
        date: datetime.date
    """
    return datetime.strptime(_date.strip(), "%m/%d/%y").date()


def parseFloat(_number: str) -> float:
    """This function takes in a string strips unwanted symbols like $ and + and parses it to a float

    Args:
        _number (str): for example $5.0 or 10000+

    Returns:
        float: 
    """
    return float(_number.strip().strip("+").strip("$"))


def getPriceList(browser: webdriver) -> dict:
    """This function get the Price list(dict) For ElectoricMaster.com on a product page

    Args:
        browser (webdriver): Selenium.WebDriver

    Returns:
        dict
    """
    data = getTextById(browser, 'divPriceListLeft').split("\n")[3:]
    del data[2::3]
    return(dict(("PB{} Qty".format(index//2+1), parseFloat(i)) if(index % 2 == 0)
                else ("PB{} $".format(index//2+1), parseFloat(i)) for index, i in enumerate(data[:20])))


def parseDefault(_str: str):
    _data = _str.split('can ship')
    result = [None, None]
    if(len(_data) == 2):
        try:
            result[0] = parseFloat(_data[0])
        except:
            result[0] = None
        result[1] = parseDate(_data[1])

    return result


def getMfrDetail(browser: webdriver) -> dict:
    """The function get manafacturers For ElectoricMaster.com on a product page

    Args:
        browser (webdriver): Selenium.WebDriver

    Returns:
        dict
    """
    result = {}
    data = getTextByXPath(browser, '//*[@id="divDefault"]/div/div').split("\n")
    data = dict((i, j) for i, j in zip(data[::2], data[1::2]))
    if ("Factory Lead-Time" in data):
        result['Lead-Time'] = parseFloat(
            data["Factory Lead-Time"].lower().split("weeks")[0])
    if('Manufacturer Stock:' in data):
        [result['Mfr Stock'], result["Mfr Stock Date"]
         ] = parseDefault(data['Manufacturer Stock:'])
    if('On Order:' in data):
        [result['On-Order'], result["On-Order Date"]
         ] = parseDefault(data['On Order:'])
    if('Minimum Order:' in data):
        result["Min Order"] = parseFloat(data['Minimum Order:'])
    return result


def getExcels(path: str) -> [str]:
    """This function returns the list of excel in path

    Args:
        path (str)

    Returns:
        [str]: list of excel(.xlsx) in path
    """
    return (list(filter(lambda elem: elem.endswith(".csv") or elem.endswith(".xlsx"), listdir(path))))


def getItem(browser: webdriver, item: str) -> bool:
    """This Function Checks if an item query as any results on the current page
        it returns true to indicate if on the right page and false if the search item returns no results

    Args:
        browser (webdriver):Selenium.WebDriver
        item (str): Query

    Returns:
        bool
    """
    url = (
        "https://www.masterelectronics.com/en/keywordsearch?text={0}".format(item))
    browser.get(url)
    if(browser.current_url == url):
        browser.find_element(by=By.XPATH,
                             value='//*[@id="search-content-results"]/div/div[2]/a[1]').click()
    elif("https://www.masterelectronics.com/en/requestfornotifications" in browser.current_url):
        return False
    return True


def main():
    # initialise Browser
    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()))

    _columns = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
                'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order",
                "PB1 Qty", "PB2 Qty", "PB3 Qty", "PB4 Qty", "PB5 Qty", "PB6 Qty", "PB7 Qty", "PB8 Qty",	"PB9 Qty", "PB10 Qty", "PB1 $",	"PB2 $", "PB3 $",	"PB4 $",	"PB5 $",	"PB6 $",	"PB7 $",	"PB8 $",	"PB9 $", "PB10 $",	"URL"]

    for excel in (getExcels(_dir)):
        print('\n\n\n')
        result_df = pd.DataFrame(columns=_columns)
        timestamp = datetime.now()
        raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
            '.xlsx') else pd.read_csv(path.join(_dir, excel))
        present_columns = set(raw_data.columns).intersection(
            ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
        print(raw_data)
        if ("Query" in present_columns):
            for index, row in enumerate(raw_data.to_dict(orient='records')):
                print("currently at index: {} \nData\t:{}".format(index, row))
                if getItem(browser, row["Query"]):
                    row['Run Datetime'] = timestamp
                    row['Mfr'] = getTextByXPath(
                        browser, '//*[@id="product-details"]/a')
                    row["Mfr PN"] = getTextByXPath(
                        browser, '//*[@id="product-details"]/h1')
                    mfr_date = getTextById(browser, 'lblDateFactory')
                    row["Mfr Stock Date"] = "#N/A" if len(
                        mfr_date) == 0 else parseDate(mfr_date)
                    row["Stock"] = parseFloat(getTextByXPath(
                        browser, '//*[@id="divInInstock"]/span'))
                    row.update(getMfrDetail(browser))
                    row.update(getPriceList(browser))
                    row["URL"] = browser.current_url
                result_df = result_df.append(
                    row, ignore_index=True, sort=False)
        else:
            print("could not find `Query` in {}".format(excel))
        result_df[_columns].to_excel(
            path.join(_output_dir, str(timestamp)+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx")), index=False)
    browser.close()


C
