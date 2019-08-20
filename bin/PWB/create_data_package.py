#! python3

# Copyright (C) 2019 Morten Eek

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from configparser import SafeConfigParser
import subprocess, os, hashlib, shutil
from verify_md5sum import pwb_message

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)

def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


if config.has_option('ENV', 'data_dir'):
    data_dir = config.get('ENV', 'data_dir') + "/"

if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')
    pwb_dir = os.path.abspath(os.path.join(tmp_dir, '..', 'PWB'))
    
    wim_cmd = pwb_dir + "/wimlib-imagex capture "
    if os.name == "posix":
        wim_cmd = "wimcapture "
    wim_file = data_dir + sys_name + ".wim"
    subprocess.run(wim_cmd + data_dir + sys_name + " " + wim_file +
                " --no-acls --compress=none", shell=True)

    md5sumFile = os.path.splitext(wim_file)[0] + "_md5sum.txt"
    check = md5sum(wim_file)
    print(check)

    f = open(md5sumFile, "w+")
    f.write(check)
    f.close()

    shutil.rmtree(data_dir + sys_name, ignore_errors=True)
    pwb_message("'Done!'", "info")
else:
    pwb_message("'No data to package!'", "error")



