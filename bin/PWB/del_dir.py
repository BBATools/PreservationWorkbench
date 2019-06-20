#! python3
import shutil, argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p", help="set path")
args = parser.parse_args()

wim_file = Path(args.path + '.wim')
if wim_file.is_file():
    shutil.rmtree(args.path, ignore_errors=True)
		

