from data.migrate.migrate import migrate_version_114_115
import argparse

migration_table = [{'old': '1.14', 'new': '1.15', 'script': migrate_version_114_115},]

def migrate(database, old_version, new_version):
    for migration in migration_table:
        if migration['old'] == old_version and migration['new'] == new_version:
            migration['script'](database)
            return True
    return False

parser = argparse.ArgumentParser()
parser.add_argument('database', type=str, help = 'database name (full filename)')
parser.add_argument('old_version', type=str, help = 'old version database')
parser.add_argument('new_version', type=str, help = 'new version database')
args = parser.parse_args()
if migrate(args.database, args.old_version, args.new_version):
    print(f'Migration {args.database} to {args.new_version} complete.')
else:
    print(f'Migration {args.old_version} to {args.new_version} not supported.')