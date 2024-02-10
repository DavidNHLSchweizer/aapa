""" TESTING: zet hier code in die je tegen de database wilt testen.    
"""

from argparse import ArgumentParser, Namespace
from data.classes.const import FileType
from data.storage.queries.files import FilesQueries
from process.aapa_processor.aapa_processor import AAPARunnerContext

def extra_args(base_parser: ArgumentParser)->ArgumentParser:
    return base_parser

def extra_main(context:AAPARunnerContext, namespace: Namespace):
    mimosa = r':ROOT12:\Cheng, Micky\2023-12-22 Beoordelen Onderzoeksverslag\5 januari 2024 2e kans onderzoeksverslag 2GETR Micky Cheng 4511484.pdf'

    momisa = r':ROOT12:\Cheng, Micky\2023-12-22 Beoordelen Onderzoeksverslag\5 januari 2024 2e kans onderzoeksverslag 2GETR Micky Cheng 4511484.pdf'
    # mimosa2 = ':ROOT12:\\Cheng,  Micky\\2023-12-22 Beoordelen Onderzoeksverslag\\5 januari 2024 2e kans Onderzoeksverslag 2GETR Micky Cheng 4511484.pdf'
    query = f'SELECT id,filename FROM FILES WHERE ((filename = ?) AND (filetype IN (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)));'
    # query2 = f'SELECT id,filename FROM FILES WHERE (filename = "{mimosa2}")'
    print(query)
    params = [momisa]
    for ft in FileType.valid_file_types():
        params.append(int(ft))        
    print(params)
    rows = context.configuration.database._execute_sql_command(query, params, True)
    if rows:
        for row in rows: 
            print(f'{row['id']}   {row['filename']}')
    else:
        print('no rows found')
    queries: FilesQueries = context.configuration.storage.queries('files')
    print (queries.is_known_file(momisa))