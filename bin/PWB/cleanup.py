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

import subprocess, os, shutil, glob
from configparser import SafeConfigParser

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
wim_file = config.get('ENV', 'wim_path')

process = config.get('ENV', 'process')
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
package_dir = data_dir + "/" + sys_name
mount_dir = package_dir + "_mount"

shutil.rmtree(mount_dir, ignore_errors=True)

if process == 'file':
  md5sum_file = os.path.splitext(wim_file)[0]+'_md5sum.txt'
  if os.path.isfile(md5sum_file):
    os.remove(md5sum_file)
elif process == 'meta':
  documentation_folder = package_dir + "/content/documentation/"
  done_files = glob.glob(documentation_folder + "*_done")
  for f in done_files:
    os.remove(f)

  sub_systems_path = package_dir + "/content/sub_systems/"
  subfolders = os.listdir(sub_systems_path)
  for folder in subfolders:
    header_xml_file = sub_systems_path + folder + "/header/metadata.xml"
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)) and os.path.isfile(header_xml_file):
      sub_documentation_folder = sub_systems_path + folder + "/documentation/"
      header_folder = sub_systems_path + folder + "/header/"

      mod_xml = sub_documentation_folder + "metadata_mod.xml"
      header_xml = header_folder + "metadata.xml"
      shutil.copyfile(mod_xml, header_xml)
      os.remove(mod_xml)

      mod_sql = sub_documentation_folder + "metadata.sql"
      header_sql = header_folder + "metadata.sql"
      shutil.copyfile(mod_sql, header_sql)
      os.remove(mod_sql)

      sub_done_files = glob.glob(sub_documentation_folder + "*_done")
      for f in sub_done_files:
        os.remove(f)
