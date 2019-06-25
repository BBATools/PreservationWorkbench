#! python3
import os
import shutil
import argparse
import sys
import win32ui
import winutils

parser = argparse.ArgumentParser()
parser.add_argument("--system", "-s", help="set system")
parser.add_argument("--localpath", "-l", help="local copy path")
parser.add_argument("--remotepath", "-r", help="remote copy path")
args = parser.parse_args()

sys_name = args.system
local = args.localpath
remote = args.remotepath
                                                        
filename = os.path.abspath("../../_DATA/" + sys_name + ".wim")
md5sum_filename = os.path.abspath("../../_DATA/" + sys_name + "_md5sum.txt")

paths = [local, remote, filename, md5sum_filename]
p_exist = [p for p in paths if os.path.exists(p)];
p_missing = list(set(p_exist) ^ set(paths))
error_message = "Missing paths: %s" % p_missing

if not p_missing:  
    winutils.copy(src=filename,dst=remote)
    winutils.copy(src=md5sum_filename,dst=remote)
    winutils.copy(src=filename,dst=local)
    winutils.copy(src=md5sum_filename,dst=local)
else:
    win32ui.MessageBox(error_message, "Error")    
