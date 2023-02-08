from data.migrate import migrate_version_114_115
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('database', type=str, help = 'database name (full filename)')
args = parser.parse_args()
migrate_version_114_115(args.database)