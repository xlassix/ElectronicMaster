from selenium import webdriver
from os import listdir, path, makedirs
import pandas as pd
from time import sleep
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date, datetime
import enum


_dir = "input"
_output_dir = "output"
makedirs(_output_dir, exist_ok=True)
_columns = ['Internal Part Number', 'Description', 'Manufacturer', 'Query',
            'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", 'On-Order', 'On-Order Date', "Lead-Time", "Min Order",
            "PB1 Qty", "PB2 Qty", "PB3 Qty", "PB4 Qty", "PB5 Qty", "PB6 Qty", "PB7 Qty", "PB8 Qty",	"PB9 Qty", "PB10 Qty", "PB1 $",	"PB2 $", "PB3 $",	"PB4 $",	"PB5 $",	"PB6 $",	"PB7 $",	"PB8 $",	"PB9 $", "PB10 $",	"URL"]

class UrlSource(enum.Enum):
    masterElectronics = 'masterelectronics.com'
    miniCircuit = 'mini-circuits.com'


class BasicScraper():
    def __init__(self):
        self._browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()))

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
        self._browser.close()

    def __del__(self):
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



    def isElementPresent(self,xpath:str,order=0):
        """This method looks up an xpath if it exists then the first element is return 
        else None

        Args:
            xpath (str): xpath 
            order (int, optional): more than one element that fits this xpath might be found.
             Hence Defaults to 0(first element).

        Returns:
            Option<Str>: String or None
        """
        data=self._browser.find_elements(by=By.XPATH, value=xpath)
        if len(data) != 0:
            return data[order]
        return None


class MasterElectronicsScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source=UrlSource.masterElectronics

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
            item)
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
        return(dict(("PB{} Qty".format(index//2+1), self.parseFloat(i)) if(index % 2 == 0)
                    else ("PB{} $".format(index//2+1), self.parseFloat(i)) for index, i in enumerate(data[:20])))

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

    def scrape(self, input_dir: str, output_dir: str):
        """This method reads all the excels in Xlsx and csv format from the specified input directory and writes the scraped output 
        into the corresponding output directory

        Args:
            input_dir (str): Input directory
            output_dir (str): Output Directory
        """
        for excel in (self.getExcels(input_dir)):
            print('\n\n')
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
                        row.update(self.getPriceList())
                    else:
                        row['Run Datetime'] = timestamp
                        row['Mfr'] = "No Result"
                        row["Mfr PN"] = "No Result"
                    row["Source"] = self._source.value
                    row["URL"] = self._browser.current_url
                    result_df = result_df.append(
                        row, ignore_index=True, sort=False)
            else:
                print("could not find `Query` in {}".format(excel))
            result_df[_columns].to_excel(
                path.join(output_dir, str(timestamp)+self._source.name+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx")), index=False)


class MiniCircuitScraper(BasicScraper):

    def __init__(self):
        super().__init__()
        self._source=UrlSource.miniCircuit

    def getItem(self, item: str) -> bool:
        """This method Checks if an item query as any results on the current page
            it returns true to indicate if on the right page and false if the search item returns no results

        Args:
            item (str): Query

        Returns:
            bool
        """
        url = "https://www.minicircuits.com/WebStore/modelSearch.html?model={0}".format(item)
        self._browser.get(url)
        if len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/header/a/img')) == 0:
            sleep(8)  # bypass access denial
            self.getItem(item)
        elif len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/label[1]')) > 0:
            return False
        if len(self._browser.find_elements(by=By.XPATH, value='//*[@id="wrapper"]/section/div[1]/div[1]')) > 0:
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
        results = []
        list(results.extend([("PB{} Qty".format(index+1), self.parseFloat(i[0])),
                            ("PB{} $".format(index+1), self.parseFloat(i[1]))]) for index, i in enumerate(data[:20]))
        return dict(results)

    def scrape(self, input_dir: str, output_dir: str):
        """This method reads all the excels in Xlsx and csv format from the specified input directory and writes the scraped output 
        into the corresponding output directory

        Args:
            input_dir (str): Input directory
            output_dir (str): Output Directory
        """
        for excel in (self.getExcels(input_dir)): #get excels
            print('\n\n')
            result_df = pd.DataFrame(columns=_columns) # initialise result DataFrame
            timestamp = datetime.now() # current time
            raw_data = pd.read_excel(path.join(_dir, excel)) if excel.endswith(
                '.xlsx') else pd.read_csv(path.join(_dir, excel)) 
            present_columns = set(raw_data.columns).intersection(
                ['Internal Part Number', 'Description', 'Manufacturer', 'Query', 'Qty'])
            print(raw_data)
            if ("Query" in present_columns):
                for index, row in enumerate(raw_data.to_dict(orient='records')):
                    print("currently at index: {} \nData\t:{}".format(index, row))
                    if self.getItem(row["Query"]):
                        row['Run Datetime'] = timestamp
                        row['Mfr'] = "Mini-Circuits"
                        row["Mfr PN"] = self.isElementPresent('//*[@id="content_area_home"]/section/section[1]/label[1]')
                        mfr_date_text = self.isElementPresent('//*[@id="model_price_section"]/div/p/span')
                        if mfr_date_text:
                            row["On-Order Date"] = None if len(
                                mfr_date_text.split(":")) < 2 else self.parseDate(mfr_date_text.split(":")[1].strip("*"), "%m/%d/%Y")
                        if len(self._browser.find_elements(by=By.XPATH, value='//*[@id="model_price_section"]/div/div[2]/span')) != 0:
                            stock = self.getTextByXPath(
                                '//*[@id="model_price_section"]/div/div[2]/span').split(" ")
                            row["Stock"] = ">" + \
                                stock[-1] if len(stock) > 1 else stock[-1]
                        if self.isElementPresent('//*[@id="model_price_section"]/table/thead/tr/th[1]'):
                            row.update(self.getPriceList())
                        if not "Stock" in row:
                            row["Stock"] = "No catalog"
                    else:
                        row['Run Datetime'] = timestamp
                        row['Mfr'] = "No Result"
                        row["Mfr PN"] = "No Result"
                    row["Source"] = self._source.value
                    row["URL"] = self._browser.current_url
                    result_df = result_df.append(
                        row, ignore_index=True, sort=False)
            else:
                print("could not find `Query` in {}".format(excel))
            result_df[_columns].to_excel(
                path.join(output_dir, str(timestamp)+self._source.name+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx")), index=False)

if __name__ == "__main__":
    # scraper = MasterElectronicsScraper()
    # scraper.scrape(input_dir=_dir, output_dir=_output_dir)

    scraper = MiniCircuitScraper()
    scraper.scrape(input_dir=_dir, output_dir=_output_dir)
