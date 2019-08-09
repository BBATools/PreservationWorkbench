#! python3
import shutil, os, time, sys, datetime
from configparser import SafeConfigParser
from appJar import gui
from extract_user_input import add_config_section
if os.name == "posix":
    from ttkthemes import ThemedTk
    # TODO: Bruk zenity direkte med subprocess heller -> fjerner gtk fm samt færre begrensninger
    from zenipy import file_selection

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
    wim_path = app.getEntry("wim_path")                                                
    dir_paths = app.getAllListItems("Directories")
    #wim_size = os.path.getsize(wim_path)
    #source_dir = os.path.dirname(wim_path) 

    # file_path = os.path.dirname(wim_path)   
    filename = os.path.basename(wim_path) 
    # md5sum_path = os.path.splitext(wim_path)[0] + "_md5sum.txt"
    # md5sum_filename = os.path.basename(md5sum_path)
    # fileFilter = (filename,md5sum_filename)  
    for path in dir_paths:
        dest_path = path + "/" + filename
        app.setMeter("progressBar", 0)
        app.threadCallback(copy,dummy,wim_path,dest_path,progress)

def clear(btn):
    app.clearAllEntries()
    app.clearAllTextAreas()
    app.clearAllListBoxes()


def add_file(btn):
    # WAIT: Legg inn filtrering til ext wim -> må bruke zenity direkte da for posix-variant
    if os.name == "posix":
        path = file_selection(filename="*.wim")
    else:
        path = app.openBox()

    if path:
        app.setEntry("wim_path", path)

def add_dir(btn):
    if os.name == "posix":
        path = file_selection(directory=True)
    else:
        path = app.directoryBox()

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

    app = gui('         Copy wim archive', useTtk=True, colspan=5)
    # TODO: Hvordan midtstille tittel uten space først?
    app.setSize("400x400")
    app.setLocation("CENTER")
    app.setStretch("column")

    if os.name == "posix":
        app.setTtkTheme('scidmint')
    else:
        app.setTtkTheme("winnative")

    app.addLabel("l0", "Choose wim-file:", 0, 0)
    app.addEntry("wim_path", 1, 0, 5)
    app.setSticky("ne")
    app.addButton("    File     ", add_file, 1, 4, 1)

    app.setSticky("new")
    app.addLabel("l1", "Add locations to copy to:", 2, 0)

    app.setSticky("new")
    app.addEntry("dir_path", 3, 0, 5)
    app.setSticky("ne")
    app.addButton("Directory", add_dir, 3, 4, 1)

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


                                       
                                                                                                   


