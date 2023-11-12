import pytest
import database.dbConst as dbc
from database.SQLtable import SQLTablebase, SQLcreateTable, SQLdelete, SQLdropTable, \
    SQLinsert, SQLselect, SQLupdate
from database.sqlexpr import Ops, SQLexpression as SQE
from database.tabledef import TableDefinition, ColumnFlags 

TEST = 'test'
TABLE2 = 'table2'
COLUMN1 = 'COLUMN1'
COLUMN2 = 'COLUMN2'
COLUMN3 = 'COLUMN3'
COLUMN4= 'COLUMN4'
NUMBER1 = 42
NUMBER2 = 42.42
STRING1 = 'Tanga'
STRING2 = 'Thong'

def test_base_abstract():
    with pytest.raises(TypeError):
        SQLTablebase()

#SQLcreateTable     
def test_create_empty():
    TD = TableDefinition(TEST)
    sql = SQLcreateTable(TD)
    assert sql.query == ''        
    assert sql.parameters == None
def test_create_auto():
    TD = TableDefinition(TEST, autoID=True)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({dbc.ID} {dbc.INTEGER} PRIMARY KEY);'
    assert sql.parameters == None
def test_create_column():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({COLUMN1} {dbc.INTEGER});'
    assert sql.parameters == None
def test_create_columns():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER, primary=True)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({COLUMN1} {dbc.INTEGER} PRIMARY KEY,{COLUMN2} {dbc.TEXT},{COLUMN3} {dbc.REAL});'
    assert sql.parameters == None
def test_create_columns_auto():
    TD = TableDefinition(TEST, autoID=True)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({dbc.ID} {dbc.INTEGER} PRIMARY KEY,{COLUMN1} {dbc.INTEGER},{COLUMN2} {dbc.TEXT},{COLUMN3} {dbc.REAL});'
    assert sql.parameters == None
def test_create_columns_foreign_key():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER, primary=True)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    TD.add_foreign_key(COLUMN2, TABLE2, COLUMN4)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({COLUMN1} {dbc.INTEGER} PRIMARY KEY,{COLUMN2} {dbc.TEXT},{COLUMN3} {dbc.REAL},FOREIGN KEY({COLUMN2}) REFERENCES {TABLE2}({COLUMN4}));'
    assert sql.parameters == None
def test_create_columns_compound_primary_key():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER, primary=True)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL, primary=True)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({COLUMN1} {dbc.INTEGER},{COLUMN2} {dbc.TEXT},{COLUMN3} {dbc.REAL},PRIMARY KEY({COLUMN1},{COLUMN3}));'
    assert sql.parameters == None
def test_create_columns_compound_primary_key_foreign_key():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER, primary=True)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL, primary=True)
    TD.add_foreign_key(COLUMN2, TABLE2, COLUMN4)
    sql = SQLcreateTable(TD)
    assert sql.query == f'CREATE TABLE IF NOT EXISTS {TEST} ({COLUMN1} {dbc.INTEGER},{COLUMN2} {dbc.TEXT},{COLUMN3} {dbc.REAL},PRIMARY KEY({COLUMN1},{COLUMN3}),FOREIGN KEY({COLUMN2}) REFERENCES {TABLE2}({COLUMN4}));'
    assert sql.parameters == None

#SQLdrop
def test_drop():
    TD = TableDefinition(TEST)
    sql = SQLdropTable(TD)
    assert sql.query == f'DROP TABLE IF EXISTS {TEST};'
    assert sql.parameters == None
        
#SQLInsert
def test_insert_empty():
    TD = TableDefinition(TEST)
    sql = SQLinsert(TD)
    assert sql.query == ''
    assert sql.parameters == []
def test_insert_default_auto():
    TD = TableDefinition(TEST, autoID=True)
    sql = SQLinsert(TD)
    assert sql.query == f'INSERT INTO {TEST} DEFAULT VALUES;'
    assert sql.parameters == []
def test_insert_default2_auto():
    TD = TableDefinition(TEST, autoID=True)
    TD.add_column(COLUMN1, dbc.INTEGER)
    sql = SQLinsert(TD, columns=[])
    assert sql.query == f'INSERT INTO {TEST} DEFAULT VALUES;'
    assert sql.parameters == []
def test_insert_default3():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    sql = SQLinsert(TD, columns=[])
    assert sql.query == f'INSERT INTO {TEST} DEFAULT VALUES;'
    assert sql.parameters == []
def test_insert_default_non():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.TEXT, primary=True)
    sql = SQLinsert(TD, columns=[COLUMN1], values=[STRING1])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1}) VALUES(?);'
    assert sql.parameters == [STRING1]
def test_insert_column():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    sql = SQLinsert(TD, column=COLUMN1, value=NUMBER1)
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1}) VALUES(?);'
    assert sql.parameters == [NUMBER1]
def test_insert_columns():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    sql = SQLinsert(TD, columns = [COLUMN1, COLUMN2], values=[NUMBER1, STRING1])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1},{COLUMN2}) VALUES(?,?);'
    assert sql.parameters == [NUMBER1, STRING1]    
def test_insert_columns2():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, columns = [COLUMN1, COLUMN2, COLUMN3], values = [NUMBER1,STRING1,NUMBER2])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1},{COLUMN2},{COLUMN3}) VALUES(?,?,?);'
    assert sql.parameters == [NUMBER1,STRING1,NUMBER2]
def test_insert_columns_partial():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, columns=[COLUMN1,COLUMN2], values=[NUMBER1,STRING1])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1},{COLUMN2}) VALUES(?,?);'
    assert sql.parameters == [NUMBER1,STRING1]
def test_insert_columns_partial2():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, column=COLUMN1, value = NUMBER1)
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN1}) VALUES(?);'
    assert sql.parameters == [NUMBER1]
def test_insert_columns_partial3():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, column=COLUMN2, value=STRING1)
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN2}) VALUES(?);'
    assert sql.parameters == [STRING1]        
def test_insert_columns_partial4():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, columns=[COLUMN3], values=[NUMBER2])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN3}) VALUES(?);'
    assert sql.parameters == [NUMBER2]
def test_insert_columns_partial5():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, columns=[COLUMN3,COLUMN2,COLUMN1], values = [NUMBER2, STRING1, NUMBER1])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN3},{COLUMN2},{COLUMN1}) VALUES(?,?,?);'
    assert sql.parameters == [NUMBER2, STRING1, NUMBER1]
def test_insert_columns_partial6():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.INTEGER)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.REAL)
    sql = SQLinsert(TD, columns=[COLUMN3,COLUMN2], values = [NUMBER2, STRING1])
    assert sql.query == f'INSERT INTO {TEST} ({COLUMN3},{COLUMN2}) VALUES(?,?);'
    assert sql.parameters == [NUMBER2, STRING1]

#CreateIndex:
#NO LONGER NEEDED, gebruik IndexDefinition
# TODO: should be added to unittests
# def test_create_index_simple():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, column=COLUMN1)
#     assert sql.query == f'CREATE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN1});'
# def test_create_index_simple_unique():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, column=COLUMN1, unique=True)
#     assert sql.query == f'CREATE UNIQUE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN1});'
# def test_create_index_multiple():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, columns=[COLUMN1, COLUMN2])
#     assert sql.query == f'CREATE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN1},{COLUMN2});'
# def test_create_index_multiple_unique():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, columns=[COLUMN1, COLUMN2], unique=True)
#     assert sql.query == f'CREATE UNIQUE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN1},{COLUMN2});'
# def test_create_index_multiple_reverse():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, columns=[COLUMN2, COLUMN1])
#     assert sql.query == f'CREATE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN2},{COLUMN1});'
# def test_create_index_multiple2():
#     INDEX = 'index1'
#     TD = TableDefinition(TEST)
#     TD.add_column(COLUMN1, dbc.INTEGER)
#     TD.add_column(COLUMN2, dbc.TEXT)
#     TD.add_column(COLUMN3, dbc.REAL)
#     sql = SQLcreateIndex(TD, INDEX, columns=[COLUMN1, COLUMN2, COLUMN3])
#     assert sql.query == f'CREATE INDEX IF NOT EXISTS {INDEX} ON {TEST}({COLUMN1},{COLUMN2},{COLUMN3});'

#SQLSelect:
def _get_table_definition():
    td = TableDefinition(TEST)
    td.add_column(COLUMN1, dbc.TEXT)
    td.add_column(COLUMN2, dbc.TEXT)
    td.add_column(COLUMN3, dbc.INTEGER)
    td.add_column(COLUMN4, dbc.REAL)
    return td
def test_select_simple():
    td = _get_table_definition()
    sql = SQLselect(td)
    assert sql.query == f'SELECT * FROM {td.name};'
    assert sql.parameters == None
def test_select_simple2():
    td = _get_table_definition()
    sql = SQLselect(td, columns = [COLUMN2, COLUMN3])
    assert sql.query == f'SELECT {COLUMN2},{COLUMN3} FROM {TEST};'
    assert sql.parameters == None
def test_select_simple_where():
    td = _get_table_definition()
    sqe = SQE(COLUMN3, Ops.LTE, NUMBER1)
    sql = SQLselect(td, columns = [COLUMN1, COLUMN3], where=sqe)
    assert sql.query == f'SELECT {COLUMN1},{COLUMN3} FROM {TEST}\nWHERE ({COLUMN3} {Ops.LTE} ?);'
    assert sql.parameters == [NUMBER1]
def test_select_distinct():
    td = _get_table_definition()
    sql = SQLselect(td, columns = [COLUMN2, COLUMN4], distinct = True)  
    assert sql.query == f'SELECT DISTINCT {COLUMN2},{COLUMN4} FROM {TEST};'
    assert sql.parameters == None
def test_select_simple_join():
    td = _get_table_definition()
    col1 = f'{TEST}.{COLUMN1}'
    col2 = f'{TABLE2}.{COLUMN1}'
    sqe = SQE(col1, Ops.EQ, col2)        
    sql = SQLselect(td, columns = [COLUMN2, col2], join = TABLE2, where=sqe)
    assert sql.query == f'SELECT {COLUMN2},{col2} FROM {TEST},{TABLE2}\nWHERE ({col1} = {col2});'
    assert sql.parameters == []
def test_select_simple_join_2():
    td = _get_table_definition()
    col1 = f'{TEST}.{COLUMN1}'
    col2 = f'{TABLE2}.{COLUMN1}'
    sqe1 = SQE(col1, Ops.EQ, col2)        
    sqe2 = SQE(COLUMN3, Ops.NEQ, STRING1)
    sqe = SQE(sqe1, Ops.AND, sqe2)
    sql = SQLselect(td, columns = [COLUMN2, col2], join = TABLE2, where=sqe)
    assert sql.query == f'SELECT {COLUMN2},{col2} FROM {TEST},{TABLE2}\nWHERE (({col1} = {col2}) {Ops.AND} ({COLUMN3} {Ops.NEQ} ?));'
    assert sql.parameters == [STRING1]

#SQLupdate
def test_update_simple():
    td = _get_table_definition()
    sql = SQLupdate(td, column=COLUMN1, value=NUMBER2)
    assert sql.query == f'UPDATE {TEST} SET {COLUMN1}=?;'
    assert sql.parameters == [NUMBER2]
def test_update_multiple():
    td = _get_table_definition()
    sql = SQLupdate(td, columns=[COLUMN1, COLUMN3], values=[STRING1, NUMBER1])
    assert sql.query == f'UPDATE {TEST} SET {COLUMN1}=?,{COLUMN3}=?;'
    assert sql.parameters == [STRING1, NUMBER1]
def test_update_simple_where():
    td = _get_table_definition()
    sqe = SQE(COLUMN3, Ops.GTE, NUMBER1)
    sql = SQLupdate(td, where=sqe,  column=COLUMN1, value=NUMBER2)
    assert sql.query == f'UPDATE {TEST} SET {COLUMN1}=?\nWHERE ({COLUMN3} {Ops.GTE} ?);'
    assert sql.parameters == [NUMBER2, NUMBER1]
def test_update_multiple_where():
    td = _get_table_definition()
    sqe = SQE(None, Ops.NOT, SQE(COLUMN3, Ops.GTE, NUMBER2), brackets=False)
    sql = SQLupdate(td, where=sqe, columns=[COLUMN1, COLUMN3], values=[STRING1, NUMBER1])
    assert sql.query == f'UPDATE {TEST} SET {COLUMN1}=?,{COLUMN3}=?\nWHERE {Ops.NOT} ({COLUMN3} {Ops.GTE} ?);'
    assert sql.parameters == [STRING1, NUMBER1, NUMBER2]


#SQLdelete
def test_delete_simple():
    td = _get_table_definition()
    sql = SQLdelete(td)
    assert sql.query == f'DELETE FROM {TEST};'
    assert sql.parameters == []
def test_delete_simple_where():
    td = _get_table_definition()
    sqe = SQE(COLUMN1, Ops.GTE, NUMBER1)
    sql = SQLdelete(td, where=sqe)
    assert sql.query == f'DELETE FROM {TEST}\nWHERE ({COLUMN1} {Ops.GTE} ?);'
    assert sql.parameters == [NUMBER1]
