import argparse

from data.migrate.migrate import migrate_version
  
parser = argparse.ArgumentParser()
parser.add_argument('database', type=str, help = 'database name (full filename)')
parser.add_argument('old_version', type=str, help = 'old version database')
parser.add_argument('new_version', type=str, help = 'new version database')
args = parser.parse_args()
if migrate_version(args.database, args.old_version, args.new_version):
    print(f'Migration {args.database} to {args.new_version} complete.')
else:
    print(f'Migration {args.old_version} to {args.new_version} not completed.')