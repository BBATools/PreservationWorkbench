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
import subprocess, os, shutil
from verify_md5sum import pwb_message

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)

if config.has_option('ENV', 'data_dir'):
    data_dir = config.get('ENV', 'data_dir') + "/"

if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')

if config.has_option('SYSTEM', 'subsys_name'):
    subsys_name = config.get('SYSTEM', 'subsys_name')

if sys_name and config.has_option('DOCUMENTS', 'dir1'):
    source_doc_paths = dict(config.items('DOCUMENTS'))
    base_path = data_dir + "/" + sys_name + "/content/sub_systems/" + subsys_name + "/content/documents/"
    pwb_dir = os.path.abspath(os.path.join(tmp_dir, '..', 'PWB'))
    for key, value in source_doc_paths.items():
        source_doc_path = value
        target_doc_path = base_path + key + ".wim"
        wim_cmd = pwb_dir + "/wimlib-imagex capture "
        if os.name == "posix":
            wim_cmd = "wimcapture "
        subprocess.run(wim_cmd + source_doc_path + " " + target_doc_path +
                    " --no-acls --compress=none", shell=True)

# Save log-file to documentation directory
if (sys_name and subsys_name):  
    shutil.copyfile(tmp_dir + "/PWB.log", data_dir + "/" + sys_name + "/content/sub_systems/" + subsys_name + "/documentation/export.log")
    pwb_message("'Done!'", "info")