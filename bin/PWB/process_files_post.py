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

import subprocess, os, glob, shutil
from configparser import SafeConfigParser

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
filepath = config.get('ENV', 'wim_path')
in_dir = os.path.dirname(filepath) + "/"
sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = data_dir + "/" + sys_name + "_mount"
av_done_file = in_dir + sys_name + "_av_done"

sub_systems_path = mount_dir + "/content/sub_systems"
subfolders = os.listdir(sub_systems_path)
for folder in subfolders:
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)):
        data_docs_folder = sub_systems_path + "/" + folder + "/content/data_documents"
        docs_folder = sub_systems_path + "/" + folder + "/content/documents"
        data_folder = sub_systems_path + "/" + folder + "/content/data"
        documentation_folder = sub_systems_path + "/" + folder + "/documentation/"

        for data_file in glob.iglob(data_folder + "/*.data"):
            shutil.move(data_file, data_docs_folder)
        if len(os.listdir(data_folder)) == 0:
            os.rmdir(data_folder)

        # Remove empty folders
        if os.path.exists(data_docs_folder):
            if len(os.listdir(data_docs_folder)) == 0:
                os.rmdir(data_docs_folder)
        if os.path.exists(docs_folder):
            if len(os.listdir(docs_folder)) == 0:
                os.rmdir(docs_folder)
