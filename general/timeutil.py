import datetime
class TimeStringConversion:
    AUTOTIMESTAMP = 0
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    DATE_FORMAT = '%d-%m-%Y'
    @staticmethod
    def rounded_timestamp(value)->datetime:
        #remove possible milliseconds so that the string can be read uniformly from the database if needed
        return TSC.str_to_timestamp(TSC.timestamp_to_str(value)) if value != TSC.AUTOTIMESTAMP else TSC.AUTOTIMESTAMP
    @staticmethod
    def timestamp_to_str(value: datetime.datetime)->str:        
        return datetime.datetime.strftime(value, TSC.DATETIME_FORMAT) if value != TSC.AUTOTIMESTAMP else '' 
    @staticmethod
    def str_to_timestamp(value: str)->datetime.datetime:
        return datetime.datetime.strptime(value, TSC.DATETIME_FORMAT) if value else TSC.AUTOTIMESTAMP
    @staticmethod
    def get_date_str(value: datetime.datetime)->str:
        def __no_time_part(d: datetime)->bool: 
            return d.time() == datetime.time()
        if __no_time_part(value):
            return datetime.datetime.strftime(value, "%d-%m-%Y")
        else:
            return datetime.datetime.strftime(value, TSC.DATETIME_FORMAT)



TSC = TimeStringConversion


