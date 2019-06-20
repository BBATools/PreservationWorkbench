#! python3
import argparse
import hashlib
import os

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p", help="set path")
args = parser.parse_args()


def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


file = args.path
md5sumFile = os.path.splitext(file)[0] + "_md5sum.txt"

check = md5sum(file)
print(check)

f = open(md5sumFile, "w+")
f.write(check)
f.close()
