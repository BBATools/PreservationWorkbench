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
from verify_make_copies import add_wim_file
import tkinter
from tkinter import ttk, messagebox


def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


def pwb_message(message, box_arg):
    if os.name == "posix":
        try:
            subprocess.call("zenity --" + box_arg + " --text=" + message + " 2> >(grep -v 'GtkDialog' >&2)",
                            shell=True, executable='/bin/bash')
        except subprocess.CalledProcessError:
            pass
        exit()
    else:
        root = tkinter.Tk()
        root.overrideredirect(1)
        root.withdraw()
        messagebox.showinfo(box_arg, message)
        root.destroy()


if __name__== "__main__":
    tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    filepath = add_wim_file(data_dir)  

    if filepath:
        md5sum_file = os.path.splitext(filepath)[0]+'_md5sum.txt'
        if not os.path.isfile(md5sum_file):
            pwb_message(os.path.basename(md5sum_file) + "' not in path'", "error")
        else:
            file = open(md5sum_file, "r")
            orig = file.read().replace('\n', '')
            check = md5sum(filepath)

            if check == orig:
                message = "'Checksum Matches'"
                box_arg = "info"
            else:
                message = "'Checksum Mismatch'"
                box_arg = "error"

            pwb_message(message, box_arg)
