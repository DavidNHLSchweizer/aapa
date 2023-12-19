import sys
from data.migrate.sql_coll import SQLcollectors

if __name__=='__main__':
    def test_json(json_filename: str):
        sql_coll = SQLcollectors.read_from_dump(json_filename)
        sql_coll.execute_sql(None, True)
    test_json(r'2021-2022_Periode 1.json')