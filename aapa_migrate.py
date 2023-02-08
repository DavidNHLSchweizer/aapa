from data.migrate import migrate_version_114_115
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('database', type=str, help = 'database name (full filename)')
parser.add_argument('old_version', type=str, help = 'old version database')
parser.add_argument('new_version', type=str, help = 'new version database')
args = parser.parse_args()
if args.old_version == '1.14' and args.new_version == '1.15':
    migrate_version_114_115(args.database)
else:
    print(f'Migration {args.old_version} to {args.new_version} not supported.')