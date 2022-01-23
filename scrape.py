from selenium import webdriver
from os import listdir, path, makedirs,environ
import pandas as pd
from requests import post
from time import sleep
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.utils import ChromeType
from datetime import date, datetime
import enum
import argparse
from urllib.parse import quote
from io import StringIO
import re
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sys import exit


SEARCH_MASTERELECTRONIC = True
SEARCH_MINI_CIRICUIT = False
SEARCH_DIGIKEY = False
SEARCH_MOUSER = True


_dir = "input"
_output_dir = "output"
makedirs(_output_dir, exist_ok=True)
_columns = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
            'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order",
            "PB1 Qty", "PB2 Qty", "PB3 Qty", "PB4 Qty", "PB5 Qty", "PB6 Qty", "PB7 Qty", "PB8 Qty",	"PB9 Qty", "PB10 Qty", "PB1 $",	"PB2 $", "PB3 $",	"PB4 $",	"PB5 $",	"PB6 $",	"PB7 $",	"PB8 $",	"PB9 $", "PB10 $",	"URL"]
_columns_pricing = ["Query", "MPN",
    "Price Break Qty",	"Price Break Price", "source"]
_columns_on_order = ["Query", "MPN",
    "On-Order Date",	"On-Order Qty"	, "Source"]
_columns_part = ['Internal Part Number', 'Description', 'Meducationanufacturer', 'Query',
                 'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", "Lead-Time", "Min Order",	"URL"]


options = webdriver.ChromeOptions()
plt=platform.system()
print(plt)
if plt == "Windows":
    options.binary_location = "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
    print("Your system is Windows")
elif plt == "Linux":
    options.binary_location = "/usr/lib/brave-browser/brave"
    print("Your system is Linux")
elif plt == "Darwin":
    options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    print("Your system is MacOS")
else:
    print("Unidentified system")
    exit()


class UrlSource(enum.Enum):
    masterElectronics = 'masterelectronics.com'
    miniCircuit = 'mini-circuits.com'
    digiKey = "digikey.com"
    mouser = "mouser.com"


class BasicScraper():

    def __init__(self):
        # self._browser = webdriver.Chrome(
        #     service=Service(ChromeDriverManager(cache_valid_range=7).install()))
        self._browser = webdriver.Chrome(
            service=Service(ChromeDriverManager(version="96.0.4664.45", chrome_type=ChromeType.CHROMIUM, cache_valid_range=7).install()), options=options)
        self._timer = 1.5

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

    def close_browser(self):
        sleep(3)
        self._browser.close()

    def scrollIntoView(self, xpath: str) -> None:
        element = self._browser.find_element(by=By.XPATH, value=xpath)
        actions = ActionChains(self._browser)
        actions.move_to_element(element).perform()

    def waitUntilElementIsVisible(self, xpath: str, max_wait: int = 10):
        """[summary]

        Args:
            xpath (str): [description]
            max_wait (int): [description]
        """
        try:
            element = WebDriverWait(self._browser, max_wait).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            return element
        except Exception as e:
            print(e)

    def __del__(self):
        sleep(3)
        self._browser.close()

    @staticmethod
    def parseDate(dateStr: str, dateFormat: str = "%m/%d/%y") -> date:
        """This function takes a date string in the format `dateFormat` and returns a datetime object

        Args:
            dateStr (str)       : date string Example 5/30/22
            dateFormat (str)    : date format for example "%m/%d/%y"
        Returns:
            date: datetime.date
        """
        return datetime.strptime(dateStr.strip(), dateFormat).date()

    @staticmethod
    def parseFloat(_number: str) -> float:
        """This static method takes in a string strips unwanted symbols like $ and + and parses it to a float

        Args:
            _number (str): for example $5.0 or 10000+

        Returns:
            float:
        """
        return float(_number.strip().strip("+").strip("$"))

    @staticmethod
    def getExcels(path: str) -> [str]:
        """This static method returns the list of excel in path

        Args:
            path (str)

        Returns:
            [str]: list of excel(.xlsx) in path
        """
        return (list(filter(lambda elem: elem.endswith(".csv") or elem.endswith(".xlsx"), listdir(path))))

    def extractDigit(self, text: str):
        r = re.search(r'\d+', text.replace(",", ""))
        return (self.parseFloat(r.group(0)) if r else 0)

    def isElementPresent(self, xpath: str, order=0):
        """This method looks up an xpath if it exists then the first element is return
        else None

        Args:
            xpath (str): xpath
            order (int, optional): more than one element that fits this xpath might be found.
             Hence Defaults to 0(first element).

        Returns:
            Option<Str>: String or None
        """
        sleep(self._timer)
        data = self._browser.find_elements(by=By.XPATH, value=xpath)
        if len(data) != 0:
            return data[order].text
        return None

    def scrollDown(self, count=1) -> None:
        body = self._browser.find_element_by_css_selector('body')
        body.send_keys([Keys.PAGE_DOWN]*count)

    @staticmethod
    def writeToFile(filename: str, parts: pd.DataFrame, pricing: pd.DataFrame, on_order: pd.DataFrame = pd.DataFrame()):
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        # Write each dataframe to a different worksheet.
        parts.to_excel(writer, sheet_name='parts', index=False)
        pricing.to_excel(writer, sheet_name='pricing', index=False)
        if len(on_order.index) != 0:
            on_order.to_excel(writer, sheet_name='On-order', index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()


class MasterElectronicsScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source = UrlSource.masterElectronics

    def parseDefault(self, _str: str):
        _data = _str.split('can ship')
        result = [None, None]
        if(len(_data) == 2):
            try:
                result[0] = self.parseFloat(_data[0])
            except:
                result[0] = None
            result[1] = self.parseDate(_data[1])

        return result

    def getItem(self, item: str) -> bool:
        """This Function Checks if an item query as any results on the current page
            it returns true to indicate if on the right page and false if the search item returns no results

        Args:
            item (str): Query

        Returns:
            bool
        """
        url = "https://www.masterelectronics.com/en/keywordsearch?text={0}".format(
            quote(item))
        self._browser.get(url)
        if(self._browser.current_url == url or "https://www.masterelectronics.com/en/productsearch/" in self._browser.current_url):
            self._browser.find_element(by=By.XPATH,
                                       value='//*[@id="search-content-results"]/div/div[2]/a[1]').click()
            return True
        elif("https://www.masterelectronics.com/en/requestfornotifications" in self._browser.current_url):
            return False
        elif self._browser.current_url.endswith(".html"):
            return True
        return False

    def getPriceList(self) -> dict:
        """This function get the Price list(dict) For UrlSource on product page

        Returns:
            dict
        """
        data = self.getTextById('divPriceListLeft').split("\n")[3:]
        del data[2::3]

        return ([{"Price Break Qty": self.parseFloat(elem[0]), "Price Break Price":self.parseFloat(elem[1])} for elem in [data[i:i + 2] for i in range(0, len(data), 2)]])

    def getMfrDetail(self) -> dict:
        """The function get manafacturers For ElectoricMaster.com on a product page

        Returns:
            dict
        """
        result = {}
        data = self.getTextByXPath('//*[@id="divDefault"]/div/div').split("\n")
        data = dict((i, j) for i, j in zip(data[::2], data[1::2]))
        if ("Factory Lead-Time" in data):
            result['Lead-Time'] = self.parseFloat(
                data["Factory Lead-Time"].lower().split("weeks")[0])
        if('Manufacturer Stock:' in data):
            [result['Mfr Stock'], result["Mfr Stock Date"]
             ] = self.parseDefault(data['Manufacturer Stock:'])
        if('On Order:' in data):
            [result['On-Order'], result["On-Order Date"]
             ] = self.parseDefault(data['On Order:'])
        if('Minimum Order:' in data):
            result["Min Order"] = self.parseFloat(data['Minimum Order:'])
        return result

    def fetchByQueryRow(self,
                        row: dict, 
                        result_df: pd.DataFrame, 
                        pricing_df: pd.DataFrame, 
                        order_df: pd.DataFrame=pd.DataFrame(columns=_columns_on_order)
                        ) -> (pd.DataFrame, pd.DataFrame):
        """This function querys MasterElectronic based on row on the input dataframe and return two df
        1. pricing DataFrame
        2. Result DataFrame
        3. Order DataFrame

        Args:
            row(dict): parsedRow containing columns as key and cells as value
            result_df: to append results
            pricing_df: to append pricing
            Order_df:
        Returns:
            result_df
            pricing_df
            order_df
        """
        # current time
        timestamp = datetime.now()

        # get to Product/item Page if it exists
        if self.getItem(row["Query"]):
            row['Run Datetime'] = timestamp
            row['Mfr'] = self.getTextByXPath(
                '//*[@id="product-details"]/a')
            row["Mfr PN"] = self.getTextByXPath(
                '//*[@id="product-details"]/h1')
            mfr_date = self.getTextById('lblDateFactory')
            row["Mfr Stock Date"] = "#N/A" if len(
                mfr_date) == 0 else self.parseDate(mfr_date)
            row["Stock"] = self.parseFloat(
                self.getTextByXPath('//*[@id="divInInstock"]/span'))
            row.update(self.getMfrDetail())
            if ('On-Order' in row):
                order_df=order_df.append({"MPN" : row["Mfr PN"],
                                        "Query" : row["Query"],
                                        "Source": self._source.name, 
                                        "On-Order Qty": row['On-Order'],
                                        "On-Order Date": row["On-Order Date"]},ignore_index=True, sort=False)
                row.pop("On-Order Date"),row.pop('On-Order')
            if prices := self.getPriceList():
                temp_pricing_df = pd.DataFrame(
                    columns=_columns_pricing).append(prices)
                temp_pricing_df["Query"] = row["Query"]
                temp_pricing_df["source"] = self._source.name
                temp_pricing_df["MPN"] = row["Mfr PN"]
                pricing_df = pricing_df.append(temp_pricing_df)
        else:
            row['Run Datetime'] = timestamp
            row['Mfr'] = "No Result"
            row["Mfr PN"] = "No Result"
        row["Source"] = self._source.name
        row["URL"] = self._browser.current_url
        result_df = result_df.append(
            row, ignore_index=True, sort=False)
        return result_df,pricing_df,order_df

    def scrape(self, input_dir: str, output_dir: str):
        """This method reads all the excels in Xlsx and csv format from the specified input directory and writes the scraped output
        into the corresponding output directory

        Args:
            input_dir (str): Input directory
            output_dir (str): Output Directory
        """
        for excel in (self.getExcels(input_dir)):  # get excels
            # print('\n\n')
            _columns_no_price = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
            'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order", "URL"]

            # initialise result DataFrame
            result_df = pd.DataFrame(columns=_columns_no_price)
            pricing_df = pd.DataFrame(columns=_columns_pricing)

            # current time
            timestamp = datetime.now()

            # read csv into pandas
            raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
                '.xlsx') else pd.read_csv(path.join(_dir, excel))

            # query Present columns
            present_columns = set(raw_data.columns).intersection(
                ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
            print(raw_data)

            # check if Query exists
            if ("Query" in present_columns):

                # iterate over each row in the pandas DataFrame
                for index, row in enumerate(raw_data.to_dict(orient='records')):
                    print("currently at row: \t{}\n\t Manufacturer: \t {}\n\t Query:\t {}".format(
                        index+1, row["Manufacturer"], row["Query"]))
                    result_df, pricing_df,order_df = self.fetchByQueryRow(row, result_df, pricing_df)
            else:
                print("could not find `Query` in {}".format(excel))
            filename = path.join(output_dir, str(
                timestamp)+self._source.name+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx"))
            self.writeToFile(filename, parts=result_df, pricing=pricing_df)


class MiniCircuitScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source = UrlSource.miniCircuit

    def getItem(self, item: str) -> bool:
        """This method Checks if an item query as any results on the current page
            it returns true to indicate if on the right page and false if the search item returns no results

        Args:
            item (str): Query

        Returns:
            bool
        """
        url = "https://www.minicircuits.com/WebStore/modelSearch.html?model={0}".format(
            quote(item))
        self._browser.get(url)
        # if permission denial screen retry after 8 secs
        if self.isElementPresent('//*[@id="wrapper"]/header/a/img') is None:
            sleep(8)
            self.getItem(item)
        # if not found tag on page return false
        elif self.isElementPresent('//*[@id="wrapper"]/section/div[1]/label[1]'):
            return False
        # if list of element found
        if self.isElementPresent('//*[@id="wrapper"]/section/div[1]/div[1]'):
            search_result_elem = self._browser.find_element(by=By.XPATH,
                                                            value='//*[@id="wrapper"]/section/div[1]/div[1]/a')
            if(self._browser.current_url == url):
                search_result_elem.click()
        return True

    def getPriceList(self) -> dict:
        """This method get the Price list(dict) For UrlSource on a product page

        Args:
            browser (webdriver): Selenium.WebDriver
        Returns:
            dict
        """
        data = list(map(lambda x: list(map(lambda y: y.split(" ")[0], x.split(
            " $"))), self.getTextByXPath('//*[@id="model_price_section"]/table').split("\n")[1:]))
        return ([{"Price Break Qty": self.parseFloat(elem[0]), "Price Break Price":self.parseFloat(elem[1])} for elem in data])

    def fetchByQueryRow(self, row: dict, result_df: pd.DataFrame, pricing_df: pd.DataFrame, order_df: pd.DataFrame=pd.DataFrame()) -> (pd.DataFrame, pd.DataFrame):
        """This function querys mini-Ciruit based on row on the input dataframe and return two df
        1. pricing DataFrame
        2. Result DataFrame
        3. Order DataFrame

        Args:
            row(dict): parsedRow containing columns as key and cells as value
            result_df: to append results
            pricing_df: to append pricing
            Order_df:
        Returns:
            result_df
            pricing_df
            order_df
        """
        # current time
        timestamp = datetime.now()

        # get to Product/item Page if it exists
        if self.getItem(row["Query"]):
            row['Run Datetime'] = timestamp
            row['Mfr'] = "Mini-Circuits"
            row["Mfr PN"] = self.isElementPresent(
                '//*[@id="content_area_home"]/section/section[1]/label[1]')
            mfr_date_text = self.isElementPresent(
                '//*[@id="model_price_section"]/div/p/span')
            if mfr_date_text:
                row["On-Order Date"] = None if len(
                    mfr_date_text.split(":")) < 2 else self.parseDate(mfr_date_text.split(":")[1].strip("*"), "%m/%d/%Y")
            stock = self.isElementPresent(
                '//*[@id="model_price_section"]/div/div[2]/span')
            if stock:
                stock = stock.split(" ")
                row["Stock"] = ">" + \
                    stock[-1] if len(stock) > 1 else stock[-1]
            if self.isElementPresent('//*[@id="model_price_section"]/table/thead/tr/th[1]'):
                temp_pricing_df = pd.DataFrame(
                    columns=_columns_pricing).append(self.getPriceList())
                temp_pricing_df["Query"] = row["Query"]
                temp_pricing_df["source"] = self._source.name
                temp_pricing_df["MPN"] = row["Mfr PN"]
                pricing_df = pricing_df.append(temp_pricing_df)
            if not "Stock" in row:
                row["Stock"] = "No catalog"
        else:
            # if Item is not found
            row['Run Datetime'] = timestamp
            row['Mfr'] = "No Result"
            row["Mfr PN"] = "No Result"
        row["Source"] = self._source.name
        row["URL"] = self._browser.current_url
        result_df = result_df.append(
            row, ignore_index=True, sort=False)
        return result_df,pricing_df,order_df


    def scrape(self, input_dir: str, output_dir: str):
        """This method reads all the excels in Xlsx and csv format from the specified input directory and writes the scraped output
        into the corresponding output directory

        Args:
            input_dir (str): Input directory
            output_dir (str): Output Directory
        """
        for excel in (self.getExcels(input_dir)):  # get excels
            # print('\n\n')

            # initialise result DataFrame
            _columns_no_price = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
            'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order", "URL"]
            result_df = pd.DataFrame(columns=_columns_no_price)
            pricing_df = pd.DataFrame(columns=_columns_pricing)

            # current time
            timestamp = datetime.now()

            # read csv into pandas
            raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
                '.xlsx') else pd.read_csv(path.join(_dir, excel))

            # query Present columns
            present_columns = set(raw_data.columns).intersection(
                ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
            print(raw_data)

            # check if Query exists
            if ("Query" in present_columns):

                # iterate over each row in the pandas DataFrame
                for index, row in enumerate(raw_data.to_dict(orient='records')):
                    print("currently at row: \t{}\n\t Manufacturer: \t {}\n\t Query:\t {}".format(
                        index+1, row["Manufacturer"], row["Query"]))
                    result_df,pricing_df,order_df = self.fetchByQueryRow(row, result_df, pricing_df)
            else:
                print("could not find `Query` in {}".format(excel))
            filename = path.join(output_dir, str(
                timestamp)+self._source.name+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx"))
            self.writeToFile(filename, parts=result_df, pricing=pricing_df)


class DigiKeyScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source = UrlSource.digiKey
        self._timer = 0.1

    def getItem(self, item: str) -> bool:
        """This method Checks if an item query as any results on the current page
            it returns true to indicate if on the right page and false if the search item returns no results

        Args:
            item (str): Query

        Returns:
            bool
        """
        url = "https://www.digikey.com/"
        self._browser.get(url)
        self._browser.find_element(
            by=By.XPATH, value='//*[@id="header"]/div[1]/div[1]/div/div[2]/div[2]/input').send_keys(item)
        self._browser.find_element(
            by=By.XPATH, value='//*[@id="header-search-button"]').click()
        if self.isElementPresent('//*[@id="__next"]/main/div/div/div/div[2]/div[1]/div[1]/div/span'):
            return {"found": False, "links": []}
        if "https://www.digikey.com/en/products/detail" in self._browser.current_url:
            return {"found": True, "links": []}
        elif "https://www.digikey.com/en/products/filter/" in self._browser.current_url:
            if self.isElementPresent('//*[@id="data-table-0"]/tbody/tr[1]/td[2]/div/div[3]/div[1]/a'):
                self.scrollIntoView(
                    '//*[@id="__next"]/main/section/div/div[2]/div/div[3]/div/div[1]/div/div[1]/div/div[1]')
                sleep(1)
                self._browser.find_element(
                    by=By.XPATH, value='//*[@id="data-table-0"]/tbody/tr[1]/td[2]/div/div[3]/div[1]/a').click()
                self.waitUntilElementIsVisible(
                    '//*[@data-testid="mfr-number"]')
                print("selected from table")
                return {"found": True, "links": []}
        elif "https://www.digikey.com/en/products/category/" in self._browser.current_url:
            self.scrollIntoView('//*[@id="__next"]/main/div/div/div/div[5]')
            sleep(self._timer)
            elems = self._browser.find_elements(
                by=By.XPATH, value='//a[starts-with(@data-testid,"product-card")]')
            sleep(2)
            print([elem.get_attribute('href') for elem in elems])
            return {"found": True, "links": [elem.get_attribute('href') for elem in elems]}
        return {"found": True, "links": []}

    def getPriceList(self, data) -> dict():
        """This method get the Price list(dict) For UrlSource on a product page

        Returns:
            dict: {
                    "found":bool,
                    "list":list
                  }
        """
        return [{"Price Break Qty": self.parseFloat(item[0]), "Price Break Price":self.parseFloat(item[1])} for item in [elem.split("$") for elem in data.replace(",", "").split("\n")]]

    def miniScraper(self, row: dict, pricing_df: pd.DataFrame) -> (dict, pd.DataFrame):
        """This method Scapes all valuable data from the Product Detail page for Digi-Key

        Args:
            row: dict
            pricing_df: DataFrame for pricing

        Returns:
            dict: update Rows
            DataFrame: DataFrame for pricing
        """

        # scrape manufactures Info if it exist
        if mfr := self.isElementPresent('//*[@id="__next"]/main/div/div[1]/div/div[2]/div/table/tbody/tr[2]/td[2]'):
            row["Mfr"] = mfr
        if mfr_pn := self.isElementPresent('//*[@data-testid="mfr-number"]'):
            row["Mfr PN"] = mfr_pn

        # Price Table scraping
        temp_pricing_df = pd.DataFrame(columns=_columns_pricing)
        if priceListData := self.isElementPresent('//*[@id="__next"]/main/div/div[1]/div/div[3]/div/div[4]/span[1]/table/tbody'):
            temp_pricing_df = temp_pricing_df.append(
                self.getPriceList(priceListData), ignore_index=True, sort=False)
        if priceListData_2 := self.isElementPresent('//*[@id="__next"]/main/div/div[1]/div/div[3]/div/div[4]/span[2]/table/tbody'):
            temp_pricing_df = temp_pricing_df.append(self.getPriceList(
                priceListData_2), ignore_index=True, sort=False)
        if priceListData := self.isElementPresent('//*[@id="__next"]/main/div/div[1]/div[2]/div[1]/div/div[4]/span[1]/table/tbody'):
            temp_pricing_df = temp_pricing_df.append(
                self.getPriceList(priceListData), ignore_index=True, sort=False)
        if priceListData_2 := self.isElementPresent('//*[@id="__next"]/main/div/div[1]/div[2]/div[1]/div/div[4]/span[2]/table/tbody'):
            temp_pricing_df = temp_pricing_df.append(self.getPriceList(
                priceListData_2), ignore_index=True, sort=False)
        temp_pricing_df["Query"] = row["Query"]
        temp_pricing_df["source"] = self._source.name
        temp_pricing_df["MPN"] = row["Mfr PN"]
        pricing_df = pricing_df.append(temp_pricing_df)
        if len(temp_pricing_df.index) != 0:
            row["Min Order"] = temp_pricing_df["Price Break Qty"].min()
        del temp_pricing_df  # selete Datafrane after us

        if stock_text := self.isElementPresent('//*[@data-testid="price-and-procure-title"]'):
            row["Stock"] = self.extractDigit(stock_text)
        if leadTime := self.isElementPresent(('//*[@id="stdLeadTime"]')):
            row["Lead-Time"] = leadTime.strip(" Weeks")
        if factoryStock := self.isElementPresent('//*[@data-testid="qty-available-messages"]'):
            row["Mfr Stock"] = self.extractDigit(
                factoryStock[factoryStock.find("Factory Stock:"):].replace(",", ""))
        if orderDate := self.isElementPresent('//*[@class="dk-table"]/tbody'):
            print(orderDate)
        return row, pricing_df

    def fetchByQueryRow(self, row: dict, result_df: pd.DataFrame, pricing_df: pd.DataFrame, order_df: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        """This function querys digitkey based on row on the input dataframe and return two df
        1. pricing DataFrame
        2. Result DataFrame
        3. Order DataFrame

        Args:
            row(dict): parsedRow containing columns as key and cells as value
            result_df: to append results
            pricing_df: to append pricing
            Order_df:
        Returns:
            result_df
            pricing_df
            order_df
        """
        # current time
        timestamp = datetime.now()
        item_status = self.getItem(row["Query"])

        # for Exact match item_status["links"] would be greater than Zero
        if len(item_status["links"]) > 0:
            for link in item_status["links"]:
                # visit each link
                self._browser.get(link)
                row['Run Datetime'] = timestamp
                (row, pricing_df) = self.miniScraper(row, pricing_df)
                row["URL"] = self._browser.current_url
                row["Source"]=self._source.name
                result_df = result_df.append(
                    row, ignore_index=True, sort=False)
            return (result_df, pricing_df, order_df)
        elif item_status["found"]:
            row['Run Datetime'] = timestamp
            (row, pricing_df) = self.miniScraper(row, pricing_df)
        else:
            # if Item is not found
            row['Run Datetime'] = timestamp
            row['Mfr'] = "No Result"
            row["Mfr PN"] = "* NOT FOUND *"
        row["Source"] = self._source.name
        row["URL"] = self._browser.current_url
        result_df = result_df.append(
                        row, ignore_index=True, sort=False)
        return (result_df, pricing_df, order_df)

    def scrape(self, input_dir: str, output_dir: str):
        """This method reads all the excels in Xlsx and csv format from the specified input directory and writes the scraped output
        into the corresponding output directory

        Args:
            input_dir (str): Input directory
            output_dir (str): Output Directory
        """

        for excel in (self.getExcels(input_dir)):  # get excels
            # initialise result DataFrames
            result_df = pd.DataFrame(columns=_columns_part)
            pricing_df = pd.DataFrame(columns=_columns_pricing)

            # current time
            timestamp = datetime.now()

            # read csv into pandas
            raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
                '.xlsx') else pd.read_csv(path.join(_dir, excel))

            # query Present columns
            present_columns = set(raw_data.columns).intersection(
                ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
            print(raw_data)

            # check if Query exists
            if ("Query" in present_columns):

                # iterate over each row in the pandas DataFrame
                for index, row in enumerate(raw_data.to_dict(orient='records')):
                    print("currently at row: \t{}\n\t Manufacturer: \t {}\n\t Query:\t {}".format(
                        index+1, row["Manufacturer"], row["Query"]))
                    # fetch Data
                    (result_df, pricing_df) = self.fetchByQueryRow(
                        row, result_df, pricing_df)
            else:
                print("could not find `Query` in {}".format(excel))
            filename = path.join(output_dir, str(
                timestamp)+self._source.name+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx"))
            self.writeToFile(filename, parts=result_df, pricing=pricing_df)



class MouserAPIScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source = UrlSource.mouser
        self.close_browser()

    def __del__(self):
        pass

    @staticmethod
    def fetchByKeyword(query: str, quantity_return:int=1, API_KEY=environ.get('MOUSER_API_KEY', '')) -> list:
        """This method returns the list of parts fetched from Mouser's API

        Args:
            query (str): [description]
            quantity_return (int, optional): The quantity of object to return. Defaults to 1.
            API_KEY (str, optional): API key from Mouser. Defaults to environ.get('MOUSER_API_KEY', '').

        Returns:
            list: list of parts
        """
        data = post(url="https://api.mouser.com/api/v1/search/keyword?apiKey={}".format(API_KEY), json={
            "SearchByKeywordRequest": {
                "keyword": query,
                "records": quantity_return
            }
        })
        if (data.status_code == 200):
            return (data.json()["SearchResults"]["Parts"])
        return []

    def fetchByQueryRow(self,
                row:dict,
                result_df:pd.DataFrame=pd.DataFrame(columns=_columns_part),
                pricing_df:pd.DataFrame=pd.DataFrame(columns=_columns_pricing),
                order_df:pd.DataFrame=pd.DataFrame(columns=_columns_on_order))->dict:
        data=self.fetchByKeyword(row["Query"])
        for product in data:
            order_df=order_df.append({
            "Query":row["Query"],
            "MPN":product.get('ManufacturerPartNumber', None),
            "Source":self._source.name,
            "On-Order Qty":self.extractDigit(product.get('Availability',"0"))},ignore_index=True)
            row.update({
                "Min Order":product.get("Min", None),
                "Stock":product.get("FactoryStock", None),
                "Lead-Time":product.get("LeadTime", None),
                "Mfr":product.get('Manufacturer', None),
                "Mfr PN": product.get('ManufacturerPartNumber', None),
                "URL": product.get('ProductDetailUrl', None),
                "Run Datetime": datetime.now()
            })
            temp_pricing=pd.DataFrame(columns=_columns_pricing).append(product.get('PriceBreaks', []))
            temp_pricing["Price Break Qty"]=temp_pricing["Quantity"]
            temp_pricing["Price Break Price"]=temp_pricing["Price"].apply(self.parseFloat)
            temp_pricing['source']=self._source.name
            temp_pricing["Query"]=row['Query']
            temp_pricing["MPN"]=product.get('ManufacturerPartNumber', None)
            pricing_df=pricing_df.append(temp_pricing[_columns_pricing])
            result_df=result_df.append(row,ignore_index=True)
            result_df['Source']=self._source.name

        return result_df, pricing_df,order_df


# A dict of scrapers and their corresponding classes
SCRAPER_DICT= {
    'masterelectronics.com': MasterElectronicsScraper,
    'mini-circuits.com': MiniCircuitScraper,
    "digikey.com": DigiKeyScraper,
    "mouser.com": MouserAPIScraper
}
# A dict of scrapers and their corresponding classes


def main():
    # initialise result DataFrames
    result_df = pd.DataFrame(columns=_columns_part)
    pricing_df = pd.DataFrame(columns=_columns_pricing)
    order_df = pd.DataFrame(columns=_columns_on_order)
    valid_url = [i.value for i in UrlSource.__members__.values()]

    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--site",
                    help = "accepted value must be member of {}".format(valid_url))

    args=vars(ap.parse_args())
    if not args["site"] is None:
        args["site"]=args["site"].lower()
        assert args["site"] in valid_url, "site parameter must be of {}".format(
            valid_url)
        # construct the argument parser and parse the arguments

        site= args['site']
        scraper= SCRAPER_DICT[site]()
        scraper.scrape(input_dir =_dir, output_dir=_output_dir)
    elif any([SEARCH_DIGIKEY, SEARCH_MOUSER,SEARCH_MASTERELECTRONIC,SEARCH_MINI_CIRICUIT]):
        classes=[]
        if SEARCH_DIGIKEY:
            classes.append(DigiKeyScraper)
        if SEARCH_MOUSER:
            classes.append(MouserAPIScraper)
        if SEARCH_MASTERELECTRONIC:
            classes.append(MasterElectronicsScraper)
        if SEARCH_MINI_CIRICUIT:
            classes.append(MiniCircuitScraper) 
        for excel in (BasicScraper.getExcels(path=_dir)):  # get excels
            # current time
            timestamp= datetime.now()
            # read csv into pandas
            raw_data= pd.read_excel(path.join(_dir, excel)) if excel.endswith(
                '.xlsx') else pd.read_csv(path.join(_dir, excel))
            if ("Query" in raw_data.columns):
                for _class in classes:
                    instances=_class()
                    for index, row in enumerate(raw_data.to_dict(orient='records')):
                        print("currently at row: \t{}\n\t Manufacturer: \t {}\n\t Query:\t {}".format(
                            index+1, row["Manufacturer"], row["Query"]))
                        (result_df, pricing_df, order_df) = instances.fetchByQueryRow(
                            row, result_df, pricing_df, order_df)
                filename = path.join(_output_dir, str(
                        timestamp)+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx"))
                BasicScraper.writeToFile(filename, result_df, pricing_df,order_df)
            else:
                print("excel doesnt contain column `Query`")


if __name__ == "__main__":
    main()
