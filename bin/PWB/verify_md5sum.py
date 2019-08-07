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
    import win32ui
    file_open = win32ui.CreateFileDialog(1, ".wim", "", 0, "Wim Archives (*.wim)|*.wim|All Files (*.*)|*.*|")
    file_open.SetOFNInitialDir('D:') # TODO: Hent path fra relative path til _DATA
    file_open.DoModal()
    filepath = file_open.GetPathName()	
    file_ext = pathlib.Path(filepath).suffix
    if file_ext != ".wim":
    	win32ui.MessageBox("Not a valid wim archive.", "Error")
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
	win32ui.MessageBox(message, box_arg)
