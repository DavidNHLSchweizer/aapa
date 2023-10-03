import pytest
import database.dbConst as dbc
from database.tabledef import ColumnDefinition, ColumnFlags, TableDefinition, TableFlags

TEST = 'test'
TABLE2 = 'table2'
COLUMN1 = 'COLUMN1'
COLUMN2 = 'COLUMN2'
COLUMN3 = 'COLUMN3'
COLUMN4 = 'COLUMN4'

#TODO: testing default_value attribute

def _test_column_is(column, name, type, **args):
    assert column.name == name
    assert column.type == type
    for info in ColumnFlags.get_attributes_for_args(**args):
        assert getattr(column, info["attribute"]) != info["default"] 
def _test_add_column(type, **args):
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, type, **args)
    _test_column_is(TD.columns[0], COLUMN1, type, **args)

def test_init_default():
    TD = TableDefinition(TEST)
    assert TD.name == TEST
    assert len(TD.columns) == 0
def test_init_auto():
    TD = TableDefinition(TEST, autoID=True)
    assert TD.name == TEST
    assert len(TD.columns) == 1
    assert TD.autoID
    _test_column_is(TD.columns[0], dbc.ID, dbc.INTEGER, primary=True)
def test_add_column_text():
    _test_add_column(dbc.TEXT)
    _test_add_column(dbc.TEXT, primary=True)
    _test_add_column(dbc.TEXT, notnull=True)
    _test_add_column(dbc.TEXT, unique=True)
    _test_add_column(dbc.TEXT, primary=True, notnull=True)
    _test_add_column(dbc.TEXT, primary=True, notnull=True, unique=True)
def test_add_column_integer():
    _test_add_column(dbc.INTEGER)
    _test_add_column(dbc.INTEGER, primary=True)
    _test_add_column(dbc.INTEGER, notnull=True)
    _test_add_column(dbc.INTEGER, unique=True)
    _test_add_column(dbc.INTEGER, primary=True, notnull=True)
    _test_add_column(dbc.INTEGER, primary=True, notnull=True, unique=True)
def test_add_column_real():
    _test_add_column(dbc.REAL)
    _test_add_column(dbc.REAL, primary=True)
    _test_add_column(dbc.REAL, notnull=True)
    _test_add_column(dbc.REAL, unique=True)
    _test_add_column(dbc.REAL, primary=True, notnull=True)
    _test_add_column(dbc.REAL, primary=True, notnull=True, unique=True)
def test_add_columns():
    colnames = [COLUMN1, COLUMN2, COLUMN3, COLUMN4]
    coltypes = [dbc.ID, dbc.TEXT, dbc.INTEGER, dbc.REAL]
    TD = TableDefinition(TEST)
    for i in range(len(colnames)):
        TD.add_column(colnames[i], coltypes[i])
    assert len(TD.columns) == len(colnames)
    for i in range(len(colnames)):
        column = TD.columns[i]
        assert column.name  == colnames[i]
        assert column.type == coltypes[i]
def _test_foreign_key_is(foreign_key, column_name, ref_table, ref_column):
    assert foreign_key.column_name == column_name
    assert foreign_key.ref_table == ref_table
    assert foreign_key.ref_column == ref_column
def test_foreign_key():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.ID, primary=True)
    TD.add_column(COLUMN2, dbc.TEXT)
    TD.add_column(COLUMN3, dbc.INTEGER)
    TD.add_column(COLUMN3, dbc.REAL)
    TD.add_foreign_key(COLUMN3, TABLE2, COLUMN4)
    _test_foreign_key_is(TD.foreign_keys[0], COLUMN3, TABLE2, COLUMN4)
def test_compound_primary():
    TD = TableDefinition(TEST)
    TD.add_column(COLUMN1, dbc.ID, primary=True)
    assert not TD.is_compound_primary() 
    for column in TD.columns:
        assert column.has_primary_clause()
    TD.add_column(COLUMN2, dbc.TEXT, primary=True)
    assert TD.is_compound_primary() 
    for column in TD.columns:
        assert not column.has_primary_clause()
