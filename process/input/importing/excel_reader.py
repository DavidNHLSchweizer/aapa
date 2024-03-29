from typing import Any, Iterable
import pandas as pd
from pythoncom import CoInitialize

from general.pdutil import ncols, nrows
    
class ExcelReader:
    def __init__(self, xls_name: str, expected_columns:list[str]=None):
        self.xls_name = xls_name
        self.dataframe = pd.read_excel(xls_name)
        self.columns = self.dataframe.columns
        if expected_columns:
            self.error = self.__check_expected_columns(expected_columns)
        else:
            self.error = ''
        CoInitialize() #needed for TUI interface, else async or multithreading problems

    def __check_expected_columns(self, expected_columns: list[str])->str:
        try:
            if ncols(self.dataframe) != len(expected_columns):
                return f'Onverwacht aantal kolommen ({ncols(self.dataframe)}) in {self.xls_name}. Verwachting is {len(expected_columns)}.'
            for column,expected_column in zip(self.columns, expected_columns):
                if column.lower() != expected_column.lower():
                    return f'Onverwachte kolom-header: {column} in {self.xls_name}. Verwachte kolommen:\n\t{expected_columns}'
            return ''
        except Exception as E:
            return f'Onverwachte fout in Excel sheet {self.xls_name}: {E}'
    def __get(self, rownr: int, col_name: str)->Any:
        value =self.dataframe.at[rownr, col_name] 
        return value.strip() if isinstance(value,str) else value
    def __read_row(self, row: int)->dict[str, Any]:
        return {column_name: self.__get(row, column_name) for column_name in self.columns}
    def read(self)-> Iterable[dict[str,Any]]:
        for row in range(nrows(self.dataframe)):
            yield(self.__read_row(row))
