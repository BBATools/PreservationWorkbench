#! python3
import pathlib
import argparse
import platform
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--key", "-k", help="set key")
parser.add_argument("--value", "-v", help="set value")
args = parser.parse_args()

pathlib.Path('tmp').mkdir(parents=True, exist_ok=True)

with open('tmp/' + args.key, 'w') as file:
    file.write(args.value.strip())
