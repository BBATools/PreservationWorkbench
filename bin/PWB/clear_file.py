#! python3
import shutil, argparse

# TODO: Ha dette som del av wim_mount.py heller?

parser = argparse.ArgumentParser()
parser.add_argument("--file", "-f", help="set filepath")
args = parser.parse_args()

open(args.file, 'w').close()

		

