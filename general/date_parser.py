from datetime import date, datetime
import re
import locale

def _try_return_date(day_str, month_str, year_str, formats, _locale='nl_NL')->date:
    old_loc,_ = locale.getlocale(locale.LC_TIME)
    if old_loc != _locale:
        locale.setlocale(locale.LC_TIME, _locale)
    try:
        for format in formats:
            try:
                if tm := datetime.strptime(f'{day_str}-{month_str}-{year_str}', format):
                    return tm #date(tm.year, tm.month, tm.day)
            except ValueError:
                pass
    finally:
        if old_loc != _locale:            
            locale.setlocale(locale.LC_TIME, old_loc)
    return None

def try_return_date(day_str, month_str, year_str, formats)->date:
    LOCALES = ['nl_NL', 'en_US']
    for _locale in LOCALES:
        if result := _try_return_date(day_str, month_str, year_str, formats, _locale):
            return result
    return None

class DateParser:
    INT_DATE_REGEX='(?P<day>\d+)[-/\w](?P<month>\d+)[-/\w](?P<year>(\d\d)+)(?P<rest>.*)'
    STR_DATE_REGEX='(?P<day>\d+)[-\/\s]+(?P<month>[a-zA-Z]{3,9})[-\/\s]+(?P<year>(\d\d)+)(?P<rest>.*)'
    def __init__(self):
        self.int_pattern = re.compile(DateParser.INT_DATE_REGEX)
        self.str_pattern = re.compile(DateParser.STR_DATE_REGEX)

    def __parse_date(self, pattern:re.Pattern, s:str, time_format, is_int=False)->tuple[date,str]:
        if match:=pattern.match(s):
            try:
                rest = match.group('rest')
                month = match.group('month')
                if not is_int:
                    month = month.capitalize()                
                return try_return_date(match.group('day'), month, match.group('year'), time_format),rest
            except ValueError as E:
                print(f'Invalid date: {s}: {E}')
        return None,s
    def parse_date(self, s: str)-> tuple[date,str]: 
        try_parse= [{'pattern':self.int_pattern, 'format':["%d-%m-%Y"], 'is_int': True},
                    {'pattern':self.int_pattern, 'format':["%d-%m-%y"], 'is_int': True},
                    {'pattern':self.str_pattern, 'format':["%d-%b-%Y", "%d-%B-%Y"], 'is_int': False},
                    {'pattern':self.str_pattern, 'format':["%d-%b-%y", "%d-%B-%y"], 'is_int': False},
                    ]       
        for try_p in try_parse:
            result, rest = self.__parse_date(try_p['pattern'], s, try_p['format'], try_p['is_int'])
            if result:
                return result,rest
        return None,s

if __name__=='__main__':     
    TESTCASES= ['3-4-1999', '3-4-1999/v1', '01-11-2022', '28-11-2022 / Versie 1', '08 november 2022', '08 maart 2022', '28-11-22 / Versie 1', '08 november 22', '08 maart 22','08 mar 2022', '08 mar 22', '21 november 2022 / v1', '30-02-2022','01-13-2022', '08 branuari 2022']
    DP = DateParser()
    for case in TESTCASES:
        d,v = DP.parse_date(case)
        if d:
            print(f'{case}: {d:%d-%m-%Y}   v:{v}')
        else:
            print(f'{case}: NONE  {v}')

