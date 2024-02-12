import argparse
from database.aapa_database import DBVERSION
from migrate.migrate import init_database
from general.sql_coll import SQLcollectors
from general.log import init_logging

if __name__== '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('database', type=str, help = 'database name (full filename)')
    parser.add_argument('json_file', type=str, help = 'json file containing "sql-collected" commands')
    parser.add_argument('-debug', action='store_true', dest='debug', help=argparse.SUPPRESS) #forceer debug mode in logging system
    args = parser.parse_args()

    init_logging(f'sql_exec {args.json_file}_{args.database}.log', debug=args.debug)    
    if (database := init_database(args.database, DBVERSION, 'import JSON')):
        print(f'Executing {args.json_file} on {args.database}.')
        sqlcolls = SQLcollectors.read_from_dump(args.json_file)
        sqlcolls.execute_sql(database)
        database.commit()
        print('Succes!')