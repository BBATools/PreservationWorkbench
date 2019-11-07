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

import subprocess, os, shutil, sys
from configparser import SafeConfigParser
from verify_md5sum import pwb_message

print("Unmounting wim image ...")
sys.stdout.flush()

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
wim_file = config.get('ENV', 'wim_path')
log_file = config.get('ENV', 'log_file')
process = config.get('ENV', 'process')
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
package_dir = data_dir + "/" + sys_name
mount_dir = package_dir + "_mount"
log_dir = ""

if log_file != None:
    log_dir = mount_dir + "/content/documentation/"
    log_file = log_dir + log_file
    if not os.path.isfile(log_file):
        shutil.copyfile(tmp_dir + '/PWB.log', log_file)

if process == 'file':
    subprocess.run("wimunmount --commit --force " + mount_dir, shell=True)
elif process == 'meta':
    shutil.copytree(
        mount_dir,
        package_dir)  # TODO: Test å legge inn cli progress bar på denne
    subprocess.run("wimunmount --force " + mount_dir, shell=True)

pwb_message("'Done!'", "info")
