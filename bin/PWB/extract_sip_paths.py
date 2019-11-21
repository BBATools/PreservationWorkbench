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
import pathlib, os, subprocess
from verify_md5sum import pwb_message
from extract_user_input import add_config_section

def unique_dir(directory):
    counter = 0
    while True:
        counter += 1
        path = pathlib.Path(directory + str(counter))
        if not path.exists():
            return path

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
sys_name = None
subsys_name = None

if config.has_option('ENV', 'wb_dir'):
    basepath = config.get('ENV', 'wb_dir') + "_DATA/"
if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')
if config.has_option('DATABASE', 'db_name'):
    database = config.get('DATABASE', 'db_name')
if config.has_option('DATABASE', 'db_schema'):
    schema = config.get('DATABASE', 'db_schema')

subsystem_path = None
db_args = ""
doc_args= ""

if sys_name:
    if config.has_option('DOCUMENTS', 'dir1'):
        doc_args = "ok"

    if schema and database:
        subsystem_path = basepath + sys_name + \
            '/content/sub_systems/' + database + '_' + schema
        db_args = "ok"
    elif doc_args:
        subsystem_path = str(unique_dir(basepath + sys_name + '/content/sub_systems/' +
                                        sys_name))
                                        
    if db_args or doc_args:
        pathlib.Path(basepath + sys_name +
                 '/administrative_metadata/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(basepath + sys_name +
                 '/descriptive_metadata/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(basepath + sys_name +
                 '/content/documentation/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(subsystem_path +
                    '/header/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(subsystem_path +
                    '/content/documents/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(subsystem_path +
                    '/content/documents/').mkdir(parents=True, exist_ok=True)
        pathlib.Path(subsystem_path +
                    '/documentation/dip/').mkdir(parents=True, exist_ok=True)

        subsys_name = subsystem_path.split('/')[-1]
        config.set('SYSTEM', 'subsys_name', subsys_name)
    else:
        pwb_message("'Illegal or missing values in user input'", "error")
else:
    pwb_message("'Illegal or missing values in user input'", "error")

add_config_section(config, 'DATABASE')
config.set('DATABASE', 'db_args', db_args)
with open(conf_file, "w+") as configfile:
    config.write(configfile, space_around_delimiters=False)