import pandas as pd
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date, datetime
import enum


_dir = "input"
_output_dir = "output"
makedirs(_output_dir, exist_ok=True)


def parseDate(dateStr: str, dateFormat: str = "%m/%d/%y") -> date:
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


def getExcels(path: str) -> [str]:
    """This function returns the list of excel in path

    Args:
        path (str)

    Returns:
        [str]: list of excel(.xlsx) in path
    """
    return (list(filter(lambda elem: elem.endswith(".csv") or elem.endswith(".xlsx"), listdir(path))))


  
class UrlSource(enum.Enum):
    masterElectronics='masterelectronics.com'
    miniCircuit ='mini-circuits.com'

class Scraper():
    def __init__(self, source: str):
        assert source.lower() in ['masterelectronics.com', 'mini-circuits.com']
        self._browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()))
        self._source = UrlSource.masterElectronics if UrlSource.masterElectronics.value==source.lower else UrlSource.miniCircuit if UrlSource.miniCircuit.value==source.lower() else None

    def getTextById(self, _id: str) -> str:
        """This Function Gets Text from the WebDriver Instance that matches the HTML AttributeId

        Args:
            _id(str): id HTMLAttribute

        Returns:
            str: String that matches the query
        """
        return self._browser.find_element(by=By.ID, value=_id).text.replace(",", "")

    def getTextByXPath(self, xpath: str) -> str:
        """This Function Gets Text from the WebDriver Instance that matches the Xpath

        Args:
            _id(str): id HTMLAttribute

        Returns:
            str: String that matches the query
        """
        return self._browser.find_element(by=By.XPATH, value=xpath).text.replace(",", "")

    def getItem(item: str) -> bool:
        """This Function Checks if an item query as any results on the current page
            it returns true to indicate if on the right page and false if the search item returns no results

        Args:
            item (str): Query

        Returns:
            bool
        """
        url = "https://www.masterelectronics.com/en/keywordsearch?text={0}".format(
            item) if self._source == UrlSource.masterElectronics else "https://www.minicircuits.com/WebStore/modelSearch.html?model={0}".format(item)
        self._browser.get(url)
        if self._source==UrlSource.miniCircuit:
            if len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/header/a/img')) == 0:
                sleep(8)  # bypass access denial
                getItem(self._browser, item)
            elif len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/label[1]')) > 0:
                return False
            if len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/div[1]')) > 0:
                search_result_elem = self._browser.find_element(by=By.XPATH,
                                                        value='//*[@id="wrapper"]/section/div[1]/div[1]/a')
                if(self._browser.current_url == url):
                    search_result_elem.click()
            return True
        if self._source==UrlSource.masterElectronics:
            if(self._browser.current_url == url):
                self._browser.find_element(by=By.XPATH,
                                        value='//*[@id="search-content-results"]/div/div[2]/a[1]').click()
            elif("https://www.masterelectronics.com/en/requestfornotifications" in self._browser.current_url):
                return False
            return True
        return False
