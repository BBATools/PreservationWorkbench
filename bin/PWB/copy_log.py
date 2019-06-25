#! python3
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p", help="set path")
args = parser.parse_args()

shutil.copyfile('../tmp/PWB.log', args.path)
