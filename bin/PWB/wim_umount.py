import subprocess
import os
import argparse
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--wim", "-w", help="Set wim path")
parser.add_argument("--log", "-l", help="Set log filename")
parser.add_argument("--proc", "-p", help="Set process name")
args = parser.parse_args()

wim_file = args.wim
log_file = args.log
proc = args.proc
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
package_dir = os.path.abspath("../_DATA/" + sys_name)
mount_dir = package_dir + "_mount"
log_dir = ""

if log_file != None:
    log_dir = mount_dir + "/content/documentation/"
    shutil.copyfile('tmp/PWB.log', log_dir + log_file)

if proc == 'file':
    subprocess.run("wimunmount --commit --force " + mount_dir, shell=True)
elif proc == 'meta':
    shutil.copytree(mount_dir, package_dir)
    subprocess.run("wimunmount --force " + mount_dir, shell=True)
