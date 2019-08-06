#! python3

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
subsystem_file = tmp_dir + "/SubSystemName"
schema_file = tmp_dir + "/DatabaseSchema"
system_file = tmp_dir + "/SystemName"

def unique_dir(directory):
    counter = 0
    while True:
        counter += 1
        path = pathlib.Path(directory + str(counter))
        if not path.exists():
            return path


open(subsystem_file, 'w').close()
open(schema_file, 'w').close()
if len(sys_name.strip()) > 0:
    pathlib.Path(basepath + sys_name +
                 '/administrative_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + sys_name +
                 '/descriptive_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + sys_name +
                 '/content/documentation/').mkdir(parents=True, exist_ok=True)
    if len(schema.strip()) > 0 and len(database.strip()) > 0:
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
        config.write(configfile)

    with open(system_file, "w+") as f: 
        f.write(sys_name)
    with open(subsystem_file, "w+") as f: 
        f.write(subsys_name)
    with open(schema_file, "w+") as f: 
        f.write(schema)
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
        import tkinter
        from tkinter import ttk, messagebox
        root = tkinter.Tk()
        root.overrideredirect(1)
        root.withdraw()
        messagebox.showinfo("Error", msg)
        root.destroy()
        exit()
