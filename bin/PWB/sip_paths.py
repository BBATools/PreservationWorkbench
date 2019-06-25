#! python3
import pathlib
import os
import argparse
import subprocess

parser = argparse.ArgumentParser()
# Default is None:
parser.add_argument("--system", "-n", help="set system")
parser.add_argument("--database", "-d", help="set database")
parser.add_argument("--schema", "-s", help="set schema")
args = parser.parse_args()

system = args.system
database = args.database
schema = args.schema
basepath = '../../_DATA/'
subsystem_path = None
subsystem_file = os.path.abspath("../tmp/SubSystemName")

def unique_dir(directory):
    counter = 0
    while True:
        counter += 1
        path = pathlib.Path(directory + str(counter))
        if not path.exists():
            return path


open(subsystem_file, 'w').close()
if len(system.strip()) > 0:
    pathlib.Path(basepath + system +
                 '/administrative_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + system +
                 '/descriptive_metadata/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(basepath + system +
                 '/content/documentation/').mkdir(parents=True, exist_ok=True)
    if len(schema.strip()) > 0 and len(database.strip()) > 0:
        subsystem_path = basepath + system + \
            '/content/sub_systems/' + database + '_' + schema
    else:
        subsystem_path = str(unique_dir(basepath + system + '/content/sub_systems/' +
                                        system))

    pathlib.Path(subsystem_path +
                 '/header/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(subsystem_path +
                 '/content/documents/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(subsystem_path +
                 '/content/documents/').mkdir(parents=True, exist_ok=True)
    pathlib.Path(subsystem_path +
                 '/documentation/dip/').mkdir(parents=True, exist_ok=True)


    f = open(subsystem_file, "w")
    f.write(subsystem_path.split('/')[-1])
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
