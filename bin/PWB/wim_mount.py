import subprocess
import os
import pathlib

wim_info_file = os.path.abspath("tmp/wim_info")
filepath = ""

open(wim_info_file, 'w').close()
if os.name == "posix":
    try:
        filepath = subprocess.check_output(
            # WAIT: Husk valgt mappe til neste gang og bruk som default under
            "zenity --file-selection --filename=/media/sf_D_DRIVE/Arkimint/In/ 2> >(grep -v 'GtkDialog' >&2)", shell=True, executable='/bin/bash').decode("utf-8").strip()
    except subprocess.CalledProcessError:
        pass

    file_ext = pathlib.Path(filepath).suffix
    if file_ext != ".wim":
        try:
            subprocess.call("zenity --error --text='Not a valid wim archive.' 2> >(grep -v 'GtkDialog' >&2)",
                            shell=True, executable='/bin/bash')
        except subprocess.CalledProcessError:
            pass
        exit()
    else:
        f = open(wim_info_file, "w")
        f.write(filepath)
else:
    import tkinter
    from tkinter import ttk, messagebox
    root = tkinter.Tk()
    root.overrideredirect(1)
    root.withdraw()
    messagebox.showinfo("Info", "Only supported on PWLinux")
    # WAIT: Også sjekk på om PWLinux og ikke annen Linux
    root.destroy()
    exit()

in_dir = os.path.dirname(filepath) + "/"
sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = os.path.abspath("../_DATA/" + sys_name + "_mount")

pathlib.Path(mount_dir).mkdir(parents=True, exist_ok=True)
if len(os.listdir(mount_dir)) == 0:
    subprocess.run("GVFS_DISABLE_FUSE=1; export GVFS_DISABLE_FUSE; wimmountrw --allow-other " + in_dir + sys_name +
                   ".wim " + mount_dir, shell=True)
