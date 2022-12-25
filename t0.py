from data.AAPdatabase import AAPDatabase

db = AAPDatabase('klit.db')
#db._execute_sql_command('BEGIN;',[])
db._execute_sql_command('insert into bedrijven (id,name) values(?,?)',[5,'naked clown b.v.'])
# db._execute_sql_command('savepoint labia;',[])
db.commit()
db.disable_commit()
db._execute_sql_command('insert into bedrijven (id,name) values(?,?)',[6,'sexy sprite b.v.'])
# db._execute_sql_command('release labia;')
# db._execute_sql_command('ROLLBACK;')
db.disable_commit()
db._execute_sql_command('insert into bedrijven (id,name) values(?,?)',[7,'prudish prick n.v.'])
db.enable_commit()
db._execute_sql_command('insert into bedrijven (id,name) values(?,?)',[8,'MAXIMA1'])
db.rollback()
db.enable_commit()


