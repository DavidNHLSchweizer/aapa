from __future__ import annotations
import datetime
import locale
class TimeStringConversion:
    AUTOTIMESTAMP = 0
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    DATE_FORMAT = '%d-%m-%Y'
    SORTABLE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    @staticmethod
    def round_to_day(value: datetime.datetime)->datetime:
        return datetime.datetime(value.year, value.month, value.day)
    @staticmethod
    def date_range(value: datetime.datetime, delta_days: float)->tuple[datetime.datetime, datetime.datetime]:
        """ returns a range of dates spanning delta days around the value """
        d_delta = datetime.timedelta(delta_days * .5)
        return (value - d_delta, value + d_delta)
    @staticmethod
    def equal_in_range(value1: datetime.datetime, value2: datetime.datetime, delta_days: float)->bool:
        min, max = TSC.date_range(value1,delta_days)
        return value2 >= min and value2 <= max
    @staticmethod
    def rounded_timestamp(value)->datetime:
        #remove possible milliseconds so that the string can be read uniformly from the database if needed
        return TSC.str_to_timestamp(TSC.timestamp_to_str(value)) if value != TSC.AUTOTIMESTAMP else TSC.AUTOTIMESTAMP
    @staticmethod
    def __timestamp_to_str(value: datetime.datetime, format: str)->str:        
        return datetime.datetime.strftime(value, format) if value != TSC.AUTOTIMESTAMP else '' 
    @staticmethod
    def __str_to_timestamp(value: str, format: str)->datetime.datetime:
        return datetime.datetime.strptime(value, format) if value else TSC.AUTOTIMESTAMP
    @staticmethod
    def timestamp_to_str(value: datetime.datetime)->str:        
        return TSC.__timestamp_to_str(value, TSC.DATETIME_FORMAT) 
    @staticmethod
    def str_to_timestamp(value: str)->datetime.datetime:
        return TSC.__str_to_timestamp(value, TSC.DATETIME_FORMAT)
    @staticmethod
    def timestamp_to_sortable_str(value: datetime.datetime)->str:        
        return TSC.__timestamp_to_str(value, TSC.SORTABLE_DATETIME_FORMAT) 
    @staticmethod
    def sortable_str_to_timestamp(value: str)->datetime.datetime:
        return TSC.__str_to_timestamp(value, TSC.SORTABLE_DATETIME_FORMAT)
    @staticmethod
    def get_date_str(value: datetime.datetime|datetime.date, date_format: str="%d-%m-%Y", datetime_format=DATETIME_FORMAT)->str:
        def __no_time_part(d: datetime)->bool: 
            return d.time() == datetime.time()
        if isinstance(value,datetime.date) or __no_time_part(value):
            return datetime.datetime.strftime(value, date_format)
        else:
            return datetime.datetime.strftime(value, datetime_format)



TSC = TimeStringConversion
locale.setlocale(locale.LC_TIME, 'nl_nl') # tricky


