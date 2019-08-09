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

import hashlib, os, subprocess, pathlib


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
            # WAIT: Endre til zenipy?
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
    import tkinter # WAIT: Endre til appjar?
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
