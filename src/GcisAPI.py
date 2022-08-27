from typing import List
from dataclasses import dataclass
import requests


@dataclass
class APIURL:
    """API Url"""
    url = "https://data.gcis.nat.gov.tw/od/data/api/"

    # Search category(company, branch office or business)
    search_category = f"{url}673F0FC0-B3A7-429F-9041-E9866836B66D"

    # Comapny API
    company_1 = f"{url}5F64D864-61CB-4D0D-8AD9-492047CC1EA6"
    # company_2 = f"{url}F05D1060-7D57-4763-BDCE-0DAF5975AFE0"
    company_3 = f"{url}236EE382-4942-41A9-BD03-CA0709025E7C"

    # Branch office API
    branch = f"{url}23632BB3-5DB7-4423-9643-1D4AC140D479"

    # Business API
    business_1 = f"{url}7E6AFA72-AD6A-46D3-8681-ED77951D912D"
    # business_2 = f"{url}F570BC9A-DA4C-4813-8087-FB9CE95F9D38"
    business_3 = f"{url}426D5542-5F05-43EB-83F9-F1300F14E1F1"


class GcisInfo:
    """
    Parameters
    ----------
    uni: str
        Unified Business No.
    """

    def __init__(self, uni: str) -> None:
        self._uni = uni
        # self.type = self.get_businessitem_type()

    @property
    def uni(self) -> str | None:
        """uni getter"""
        return self._uni

    @uni.setter
    def uni(self, value):
        self._uni = value

    @property
    def category(self) -> str:
        """
        Get type of a businessitem(Company, Branch or Business).

        Return
        ------
        category: str
            Company, Branch or Business
        """

        query = APIURL.search_category + \
            f"?$format=json&$filter=No%20eq%20{self.uni}"
        json = requests.get(query).json()
        if json[0]["exist"] == "Y":
            category = "Company"
        elif json[1]["exist"] == "Y":
            category = "Branch"
        elif json[2]["exist"] == "Y":
            category = "Business"
        else:
            category = "No data"

        return category


class Company(GcisInfo):
    """
    Parameters
    ----------
    uni: str
        Unified Business No.
    """

    def __init__(self, uni: str) -> None:
        super().__init__(uni)

        self._company_1 = self.__get_company_1()
        self._company_3 = self.__get_company_3()
        self.information = self.__turn_company_info_to_dict()

    def __get_company_1(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        query = APIURL.company_1 + \
            f"?$format=json&$filter=Business_Accounting_NO%20eq%20{self.uni}"
        result: list = requests.get(query).json()
        result = result[0]

        return result

    def __get_company_3(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        query = APIURL.company_3 + \
            f"?$format=json&$filter=Business_Accounting_NO%20eq%20{self.uni}"
        result: list = requests.get(query).json()
        result = result[0]

        return result

    def __combine_company_info(self) -> dict:
        """合併公司登記基本資料-應用一與應用三"""
        info1 = self.__get_company_1()
        info3 = self.__get_company_3()

        return {**info1, **info3}

    def __turn_company_info_to_dict(self) -> dict:
        """將公司資料轉為dict"""
        data = self.__combine_company_info()

        business_item_list = None
        business_item_desc_list = None
        if "Cmp_Business" in data:
            if isinstance(data["Cmp_Business"], list):
                business_item_list = [x["Business_Item"]
                                      for x in data["Cmp_Business"]]
                business_item_desc_list = [x["Business_Item_Desc"]
                                           for x in data["Cmp_Business"]]
            elif isinstance(data["Cmp_Business"], str):
                business_item_list = [""]
                business_item_desc_list = [data["Cmp_Business"]]
        else:
            pass

        result = {"category": "Company",
                  "uni": self.uni,
                  "name": data["Company_Name"],
                  "address": data["Company_Location"],
                  "register_funds": data["Capital_Stock_Amount"],
                  "responsible_name": data["Responsible_Name"],
                  "case_status_code": data["Case_Status"],
                  "case_status_name": data["Case_Status_Desc"],
                  "status_code": data["Company_Status"],
                  "status_name": data["Company_Status_Desc"],
                  "business_item_code": business_item_list,
                  "business_item_name": business_item_desc_list
                  }

        return result


class Branch(GcisInfo):
    """
    Parameters
    ----------
    uni: str
        Unified Business No.

    Note
    ----
    ! This program requires an IP license.
    """

    def __init__(self, uni: str) -> None:
        super().__init__(uni)

        self._branch = self.__turn_branch_info_to_dict()
        self._company_name = self.__get_company_name()
        self.information = {"name": self._company_name + "-" + self._branch["branch_name"],
                            **self._branch}

    def __get_branch(self) -> List[dict]:
        """
        Return
        ------
        API_result: List[dict]

        Note
        ----
        Use of the API may result in multiple reports(incloud early information)        
        """
        query = APIURL.branch + \
            f"?$format=json&$filter=Branch_Office_Business_Accounting_NO eq {self.uni}"

        # ! JSONDecodeError if IP unlicensed.
        result = requests.get(query).json()
        return result

    def __get_last_branch_info(self) -> dict:
        """
        Return
        ------
        API_result: dict

        Note
        ----
        Since direct use of the API may result in multiple reports(incloud early information), 
        this function needs to include a process for determining the latest information.
        """

        branch_data_list = self.__get_branch()

        branch_office_status_list = [
            x["Branch_Office_Status"] for x in branch_data_list]
        chg_app_date_list = [int(x["CHG_APP_DATE"])
                             for x in branch_data_list]

        # Process for determining the latest information.
        if "01" in branch_office_status_list:
            index = branch_office_status_list.index("01")
        else:
            max_date = max(chg_app_date_list)
            index = chg_app_date_list.index(max_date)

        result = branch_data_list[index]

        return result

    def __turn_branch_info_to_dict(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        data = self.__get_last_branch_info()

        result = {"category": "Branch",
                  "uni": self.uni,
                  "company_uni": data["Business_Accounting_NO"],
                  "branch_name": data["Branch_Office_Name"],
                  "address": data["Branch_Office_Location"],
                  "responsible_name": data["Branch_Office_Manager_Name"],
                  "status_code": data["Branch_Office_Status"],
                  "status_name": data["Branch_Office_Status_Desc"]
                  }

        return result

    def __get_company_name(self) -> str:
        """
        Return
        ------
        company_name: str
        """
        company_name = Company(
            self._branch["company_uni"]).information["firm_name"]

        return company_name


class Business(GcisInfo):
    """
    Parameters
    ----------
    uni: str
        Unified Business No.
    """

    def __init__(self, uni: str) -> None:
        super().__init__(uni)

        self._business_3 = self.__get_last_business_info()
        self._business_1 = self.__get_business_1()
        self.information = self.__turn_business_info_to_dict()

    def __get_business_3(self) -> List[dict]:
        """
        Return
        ------
        API_result: List[dict]

        Note
        ----
        Use of the API may result in multiple reports(incloud early information)        
        """

        query = APIURL.business_3 + \
            f"?$format=json&$filter=President_No%20eq%20{self.uni}"
        result = requests.get(query).json()

        return result

    def __get_last_business_info(self) -> dict:
        """
        Return
        ------
        API_result: dict

        Note
        ----
        Since direct use of the API may result in multiple reports(incloud early information), 
        this function needs to include a process for determining the latest information.
        """
        business_data_list = self.__get_business_3()

        business_current_status_list = [
            x["Business_Current_Status"] for x in business_data_list]

        # Process for determining the latest information.
        if "01" in business_current_status_list:
            index = business_current_status_list.index("01")
        else:
            for i in business_current_status_list:
                if i != "05":
                    index = business_current_status_list.index(i)
                    break

        result = business_data_list[index]

        return result

    def __get_business_1(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        data_3: dict = self._business_3
        query = APIURL.business_1 + \
            f"?$format=json&$filter=President_No%20eq%20{self.uni}"\
            f"%20and%20Agency%20eq%20{data_3['Agency']}"
        result = requests.get(query).json()
        result = result[0]

        return result

    def __combine_business_info(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        data3 = self._business_3
        data1 = self._business_1

        return {**data1, **data3}

    def __turn_business_info_to_dict(self) -> dict:
        """
        Return
        ------
        API_result: dict
        """
        business_data = self.__combine_business_info()

        if isinstance(business_data["Business_Item_Old"], list):
            # business_seq_no = [x["Business_Item"] for x in js3[0]["Business_Seq_No"]]
            business_item_list = [x["Business_Item"]
                                  for x in business_data["Business_Item_Old"]]
            business_item_desc_list = [x["Business_Item_Desc"]
                                       for x in business_data["Business_Item_Old"]]

        elif isinstance(business_data["Business_Item_Old"], str):
            business_item_list = None
            business_item_desc_list = [business_data["Business_Item_Old"]]

        data = {"category": "Business",
                "uni": self.uni,
                "name": business_data["Business_Name"],
                "address": business_data["Business_Address"],
                "register_funds": business_data["Business_Register_Funds"],
                "responsible_name": business_data["Responsible_Name"],
                "status_code": business_data["Business_Current_Status"],
                "status_name": business_data["Business_Current_Status_Desc"],
                "business_item_code": business_item_list,
                "business_item_name": business_item_desc_list
                }

        return data


def get_gcis_information(uni: str) -> dict:
    """
    Parameters
    ----------
    uni: str
        Unified Business No.
    """
    category = GcisInfo(uni).category
    match category:
        case "Company":
            return Company(uni).information
        case "Branch":
            return Branch(uni).information
        case "Business":
            return Business(uni).information
