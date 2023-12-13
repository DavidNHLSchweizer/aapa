import datetime
class TimeStringConversion:
    AUTOTIMESTAMP = 0
    DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'
    DATE_FORMAT = '%d-%m-%Y'
    SORTABLE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
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
    def get_date_str(value: datetime.datetime)->str:
        def __no_time_part(d: datetime)->bool: 
            return d.time() == datetime.time()
        if __no_time_part(value):
            return datetime.datetime.strftime(value, "%d-%m-%Y")
        else:
            return datetime.datetime.strftime(value, TSC.DATETIME_FORMAT)



TSC = TimeStringConversion


