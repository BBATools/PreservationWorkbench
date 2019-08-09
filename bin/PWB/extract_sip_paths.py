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

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)

if config.has_option('ENV', 'data_dir'):
    basepath = config.get('ENV', 'data_dir') + "/"
if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')
if config.has_option('DATABASE', 'db_name'):
    database = config.get('DATABASE', 'db_name')
if config.has_option('DATABASE', 'db_schema'):
    schema = config.get('DATABASE', 'db_schema')

subsystem_path = None

def unique_dir(directory):
    counter = 0
    while True:
        counter += 1
        path = pathlib.Path(directory + str(counter))
        if not path.exists():
            return path

if len(sys_name) > 0:
    pathlib.Path(basepath + sys_name +
                 '/administrative_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + sys_name +
                 '/descriptive_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + sys_name +
                 '/content/documentation/').mkdir(parents=True, exist_ok=True)
    if len(schema) > 0 and len(database) > 0:
        subsystem_path = basepath + sys_name + \
            '/content/sub_systems/' + database + '_' + schema
    else:
        subsystem_path = str(unique_dir(basepath + sys_name + '/content/sub_systems/' +
                                        sys_name))

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
    with open(conf_file, "w+") as configfile:
        config.write(configfile, space_around_delimiters=False)
else:
    msg = "'Illegal or missing values in user input'"
    if os.name == "posix":
        try:
            subprocess.call("zenity --error --text=" + msg + " 2> >(grep -v 'GtkDialog' >&2)",
                            shell=True, executable='/bin/bash')
        except subprocess.CalledProcessError:
            pass
        exit()
    else:
        import tkinter # WAIT: Bruke appjar heller her?
        from tkinter import ttk, messagebox
        root = tkinter.Tk()
        root.overrideredirect(1)
        root.withdraw()
        messagebox.showinfo("Error", msg)
        root.destroy()
        exit()
