from requests import post
from os import listdir, path, makedirs,environ
import pandas as pd
from datetime import date, datetime
import enum
import re


SEARCH_MOUSER = True


#preset values
_dir = "input"
_output_dir = "output"
_columns_pricing = ["Query", "MPN",
    "Price Break Qty",	"Price Break Price", "source"]
_columns_on_order = ["Query", "MPN",
    "On-Order Date",	"On-Order Qty"	, "Source"]
_columns_part = ['Internal Part Number', 'Description', 'Meducationanufacturer', 'Query',
                 'Qty', 'Run Datetime', "Stock", "Mfr PN", "Mfr", "Mfr Stock", "Mfr Stock Date", "Lead-Time", "Min Order",	"URL"]

class UrlSource(enum.Enum):
    digiKey = "digikey.com"
    mouser = "mouser.com"

class BasicAPIScraper():

    def __init__(self):
        self._timer = 1.5

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

    def extractDigit(self,text: str):
        r = re.search(r'\d+', text.replace(",", ""))
        return (self.parseFloat(r.group(0)) if r else 0)
    
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

class MouserAPIScraper(BasicAPIScraper):

    def __init__(self):
        super().__init__()
        self._source = UrlSource.mouser

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
                "URL": product.get('ProductDetailUrl', None)
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


def main():
    # initialise result DataFrames
    result_df = pd.DataFrame(columns=_columns_part)
    pricing_df = pd.DataFrame(columns=_columns_pricing)
    order_df = pd.DataFrame(columns=_columns_on_order)

    if any([SEARCH_MOUSER]):
        classes=[]
        if SEARCH_MOUSER:
            classes.append(MouserAPIScraper)
        for excel in (BasicAPIScraper.getExcels(path=_dir)):  # get excels
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
                        (result_df, pricing_df, order_df) = instances.fetchByQueryRow(row,result_df, pricing_df, order_df)
                filename = path.join(_output_dir, str(
                        timestamp)+"_"+(excel if excel.endswith(".xlsx") else excel+".xlsx"))
                BasicAPIScraper.writeToFile(filename, result_df, pricing_df,order_df)
            else:
                print("excel doesnt contain column `Query`")

# print(MouserAPIScraper().extract(MouserAPIScraper.fetchByKeyword("LTC3869IUFD#PBF"),{'Query':"LTC3869IUFD#PBF"}))

if __name__ == "__main__":
    main()
