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

import shutil, os, time, sys, datetime, subprocess
from configparser import SafeConfigParser
from appJar import gui
if os.name == "posix":
    from ttkthemes import ThemedTk
    # TODO: Bruk zenity direkte med subprocess heller -> fjerner gtk fm samt færre begrensninger
    #from zenipy import file_selection

# WAIT: Splitt ut zenity kode som egen def 

def percentage(part, whole):
  return 100 * float(part)/float(whole)

def copy(src, dst, callback=None):
    blksize = 1048576 # 1MiB
    try:
        s = open(src, 'rb')
        d = open(dst, 'wb')
    except (KeyboardInterrupt, Exception) as e:
        if 's' in locals():
            s.close()
        if 'd' in locals():
            d.close()
        raise
    try:
        total = os.stat(src).st_size
        pos = 0
        start_elapsed = datetime.datetime.now()
        start_update = datetime.datetime.now()
        while True:
            buf = s.read(blksize)
            bytes_written = d.write(buf)
            end = datetime.datetime.now()
            pos += bytes_written
            diff = end - start_update
            if callback and diff.total_seconds() >= 0.2:
                callback(pos, total, end - start_elapsed)
                start_update = datetime.datetime.now()
            if bytes_written < len(buf) or bytes_written == 0:
                break
    except (KeyboardInterrupt, Exception) as e:
        s.close()
        d.close()
        raise
    else:
        callback(total, total, end - start_elapsed)
        s.close()
        d.close()

def progress(pos, total, elapsed):
    if pos == total:
        app.setMeter("progressBar", 100, "Done!")
    else:
        app.setMeter("progressBar", percentage(pos, total))

def dummy(success):
    pass


def submit(btn):   
    wim_source_path = app.getEntry("wim_path")                                                
    wim_filename = os.path.basename(wim_source_path) 
    md5sum_source_path = os.path.splitext(wim_source_path)[0] + "_md5sum.txt"
    md5sum_filename = os.path.basename(md5sum_source_path) 
 
    dir_paths = app.getAllListItems("Directories")
    for path in dir_paths:
        md5sum_dest_path = path + "/" + md5sum_filename
        wim_dest_path = path + "/" + wim_filename
        if os.path.isfile(md5sum_dest_path) or os.path.isfile(wim_dest_path):
            if os.name == "posix":
                try:
                    subprocess.call("zenity --error --text='File already exists.' 2> >(grep -v 'GtkDialog' >&2)",
                                    shell=True, executable='/bin/bash')
                    break
                except subprocess.CalledProcessError:
                    pass
            else:
                app.errorBox("title","File already exists.")
        else:
            shutil.copyfile(md5sum_source_path, md5sum_dest_path)
            app.setMeter("progressBar", 0)
            app.threadCallback(copy,dummy,wim_source_path,wim_dest_path,progress)


def clear(btn):
    app.clearAllEntries()
    app.clearAllTextAreas()
    app.clearAllListBoxes()

def add_wim_file(data_dir):
    path = None
    title = "Choose File"
    if os.name == "posix":
        try:
            path = subprocess.check_output(
                "zenity --file-selection  --title='" + title + "' --file-filter='WIM archives (wim) | *.wim' --filename=" + data_dir + "/ 2> >(grep -v 'GtkDialog' >&2)", 
                shell=True, executable='/bin/bash').decode("utf-8").strip()
        except subprocess.CalledProcessError:
            pass
    else:
        if 'app' in globals():
            path = app.openBox(title, data_dir,[("WIM archives", "*.wim")])
        else:
            path = gui(showIcon=False).openBox(title, data_dir,[("WIM archives", "*.wim")])
    return path


def app_add_file(btn):
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    path = add_wim_file(data_dir)  
    if path:
        app.setEntry("wim_path", path)


def app_add_dir(btn):
    title = "Choose Directory"
    path = None
    if os.name == "posix":
        try:
            path = subprocess.check_output("zenity --file-selection --directory --title='" + title + "' 2> >(grep -v 'GtkDialog' >&2)", 
            shell=True, executable='/bin/bash').decode("utf-8").strip()
        except subprocess.CalledProcessError:
            pass
    else:
        path = app.directoryBox(title)

    if path:
        app.setEntry("dir_path", path)
        dir_path = app.getEntry("dir_path")
        app.clearEntry("dir_path")

        dir_paths = app.getAllListItems("Directories")
        duplicate = False
        for path in dir_paths:
            if path == dir_path:
                duplicate = True
        if not duplicate:
            app.addListItem("Directories", dir_path)

def quit(btn):
    app.stop()

if __name__== "__main__":
    config = SafeConfigParser()
    tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
    conf_file = tmp_dir + "/pwb.ini"
    config.read(conf_file)

    app = gui('         Copy wim archive', useTtk=True, colspan=5, showIcon=False)
    # TODO: Hvordan midtstille tittel uten space først?
    app.setLocation("CENTER")
    app.setStretch("column")

    if os.name == "posix":
        app.setTtkTheme('scidmint')
        app.setSize("400x400")
    else:
        app.setSize("400x370")

    app.addLabel("l0", "Choose wim-file:", 0, 0)
    app.addEntry("wim_path", 1, 0, 5)
    app.setSticky("ne")
    app.addButton("    File     ", app_add_file, 1, 4, 1)

    app.setSticky("new")
    app.addLabel("l1", "Add locations to copy to:", 2, 0)

    app.setSticky("new")
    app.addEntry("dir_path", 3, 0, 5)
    app.setSticky("ne")
    app.addButton("Directory", app_add_dir, 3, 4, 1)

    app.setSticky("new")
    app.addLabel("l5", "Directories:", 4, 0)
    app.addListBox("Directories", row=5,rowspan=6)

    app.setEntryDefault("wim_path", "-- enter a filename --")
    app.setEntryDefault("dir_path", "-- enter a directory --")

    app.addLabel("l6", "Progress:", 12, 0)
    app.addMeter("progressBar", 13, 0, 6)
    app.setMeterFill("progressBar", "#ADDFAD")

    app.addButtons(["Submit", "Clear ", " Quit "], [submit, clear, quit], row=14)
    app.go()


                                       
                                                                                                   


