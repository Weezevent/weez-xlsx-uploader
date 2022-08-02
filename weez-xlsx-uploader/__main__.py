import argparse
from os import path

parser = argparse.ArgumentParser(description='WEEZ XLSX UPLOADER')
parser.add_argument('file', type=str, help='path to the xlsx file you want to import')
parser.add_argument('api_key', type=str, help='API KEY to use weezevent legacy API - see readme to find how to find it')
parser.add_argument('api_username', type=str, help='API username to use weezevent legacy API - see readme to find how to find it')
parser.add_argument('api_password', type=str, help='API password to use weezevent legacy API - see readme to find how to find it')
parser.add_argument('event_id', type=str, help='Event ID where to import this file')

args = parser.parse_args()

# 1. Some validation
if not path.exists(args.file):
    print(f"ERROR: {args.file} not found.")
    exit(1)

# 2. Read the file
from .uploader import XslxUploader
file = XslxUploader(args.file)
print(file.tickets)

# 3. Prepare API (Ensure rate exists / form exists ...)
file.prepare_event_config(
    api_key=args.api_key,
    username=args.api_username,
    password=args.api_password,
    event_id=args.event_id
)

# 4. Process file and push to API
file.send()



