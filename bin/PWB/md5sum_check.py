#! python3
import hashlib
import os
import subprocess
import pathlib


def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


filepath = ""
if os.name == "posix":
    try:
        filepath = subprocess.check_output(
            # WAIT: Husk valgt mappe til neste gang og bruk som default under. Samme for tkinter-variant under
            "zenity --file-selection --filename=../_DATA/ 2> >(grep -v 'GtkDialog' >&2)", shell=True, executable='/bin/bash').decode("utf-8").strip()
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
    import tkinter
    from tkinter import ttk, messagebox
    from tkinter.filedialog import askopenfilename
    root = tkinter.Tk()
    root.overrideredirect(1)
    root.withdraw()

    filepath = askopenfilename(initialdir="../_DATA",
                               filetypes=("Wim Archive", "*.wim"),
                               title="Choose a file."
                               )

    file_ext = pathlib.Path(filepath).suffix
    if file_ext != ".wim":
        messagebox.showinfo("Error", "Not a valid wim archive.")
    root.destroy()
    exit()

file = open(os.path.splitext(filepath)[0]+'_md5sum.txt', "r")
mount_dir = os.path.splitext(filepath)[0] + '_mount'
orig = file.read().replace('\n', '')
check = md5sum(filepath)

if check == orig:
    message = "'Checksum Matches'"
    box_arg = "info"
else:
    message = "'Checksum Mismatch'"
    box_arg = "error"

if os.name == "posix":
    try:
        subprocess.call("zenity --" + box_arg + " --text=" + message + " 2> >(grep -v 'GtkDialog' >&2)",
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
    messagebox.showinfo(box_arg, message)
    root.destroy()
