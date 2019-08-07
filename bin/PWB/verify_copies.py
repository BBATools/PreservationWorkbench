#! python3
import shutil, os, time, threading, sys
import tkinter as tk
from tkinter import ttk
import queue as Queue
from configparser import SafeConfigParser
from appJar import gui
from extract_user_input import add_config_section
if os.name == "posix":
    from ttkthemes import ThemedTk
    # TODO: Bruk zenity direkte med subprocess heller -> fjerner gtk fm samt færre begrensninger
    from zenipy import file_selection

def submit(btn):
    
    wim_path = app.getEntry("wim_path")
    file_path = os.path.dirname(wim_path)                                                      

    dir_paths = app.getAllListItems("Directories")
    app.stop()

    for path in dir_paths:
        fileFilter = (filename,md5sum_filename)  
        copyTreeGUI(file_path, remote, fileFilter)
    
    
    
    
    # filename = os.path.basename(file_path + sys_name + ".wim")                      
    # md5sum_path = file_path + sys_name + "_md5sum.txt"
    # md5sum_filename = os.path.basename(md5sum_path)
    # fileFilter = (filename,md5sum_filename)             
    # copyTreeGUI(file_path, remote, fileFilter)
    # copyTreeGUI(file_path, local, fileFilter)


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

# WAIT: Legg inn "batch variabel" som argument slik at det vises som text eg "batch 1 av 2"
class CopyGui(ttk.Frame):
    def __init__(self, parent, queue, jobTotal=0, jobSize=0):
        ttk.Frame.__init__(self, parent)
        self.queue = queue
        self.parent = parent
        self.parent.resizable(width=False, height=False)
        self.parent.title(' ')
        self.parent.wm_attributes('-topmost', 1)
        self.parent.iconbitmap(r'')
        self.jobSize = jobSize
        self.jobTotal = jobTotal
        self.statTitleLbl = ttk.Label(self,
                    text='Copying {:,} item{:.1} ({} {})'.format(jobTotal,
                                                       's'*(jobTotal-1),
                                                       *sizeNotator(self.jobSize)),
                    font=(100))
        self.statTitleLbl.grid(row=0, column=0, columnspan=4, sticky=tk.W,
                            padx=30, pady=10)
        self.statNameLbl = ttk.Label(self, text='Name:')
        self.statNameLbl.grid(row=2, column=0, sticky=tk.W, padx=(30,0))
        self.statFromLbl = ttk.Label(self, text='From:')
        self.statFromLbl.grid(row=3, column=0, sticky=tk.W, padx=(30, 0))
        self.statToLbl = ttk.Label(self, text='To:')
        self.statToLbl.grid(row=4, column=0, sticky=tk.W, padx=(30,0))
        self.statRemainLbl = ttk.Label(self, text='Items remaining:')
        self.statRemainLbl.grid(row=5, column=0, sticky=tk.W, padx=(30,0))

        self.dynNameLbl = ttk.Label(self)
        self.dynNameLbl.grid(row=2, column=1, columnspan=3, sticky=tk.W)
        self.dynFromLbl = ttk.Label(self)
        self.dynFromLbl.grid(row=3, column=1, columnspan=3, sticky=tk.W)
        self.dynToLbl = ttk.Label(self)
        self.dynToLbl.grid(row=4, column=1, columnspan=3, sticky=tk.W)
        self.dynRemainLbl = ttk.Label(self)
        self.dynRemainLbl.grid(row=5, column=1, columnspan=3, sticky=tk.W)

        self.dynProBar = ttk.Progressbar(
            self, length=400, maximum=self.jobTotal+1)
        self.dynProBar.grid(row=6, column=0, columnspan=4, sticky=tk.W, padx=30,
                      pady=15)

        ttk.Separator(self).grid(row=1, column=0, columnspan=4,
                                   sticky=tk.EW, pady=(0,10))
        ttk.Separator(self).grid(row=7, column=0, columnspan=4,
                                   sticky=tk.EW)

        self.cancelBtn = ttk.Button(self, text='Cancel', command=self.Cancel)
        self.cancelBtn.grid(row=8, column=3, sticky=tk.E, padx=30, pady=15)
        self.grid()
        self.parent.update()
        self.checkQueue()

    def checkQueue(self):
        try:
            newName, newFold, newTo, newRemain, newSize, keepUp = self.queue.get(
                block=False)
        except Queue.Empty:
            pass
        else:
            if keepUp:                
                self.upFileName(newName)
                self.upFoldFrom(newFold)
                self.upFoldTo(newTo)
                self.upProBar(1)
                self.upItemRemainig(newRemain, newSize)
            else:
                self.after(1000, self.parent.destroy)
        self.after(50, self.checkQueue)

    def upFileName(self, newName):
        self.dynNameLbl['text'] = newName[:40]
        self.parent.update()

    def upFoldFrom(self, newFold):
        self.dynFromLbl['text'] = folderShortener(newFold, 40)
        self.parent.update()

    def upFoldTo(self, newTo):
        self.dynToLbl['text'] = folderShortener(newTo, 40)
        self.parent.update()

    def upItemRemainig(self, newRemain, newSize):
        self.dynRemainLbl['text'] = '{:,} ({} {})'.format(newRemain,
                                                     *sizeNotator(newSize))
        self.parent.update()

    def upProBar(self, steps):
        self.dynProBar.step(steps)
        self.parent.update()

    def setProBarMax(self, newMax):
        self.dynProBar['maximum'] = newMax
        self.parent.update()

    def Cancel(self):
        self.parent.destroy()
        raise CopyCanceled('Copy job has been canceled by user.')

class CopyCanceled(Exception):
    pass

def sizeNotator(sizeInBytes):
    notation = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB')
    for i in range(8):
        if len(str(int(sizeInBytes/(1024**i)))) < 4:
            return round(sizeInBytes/(1024**i),1), notation[i]

def prepareFiles(srcDir, dstDir, filFilter):
    fileTotal = 0
    sizeTotal = 0
    newDirs = []
    readyFiles = [[], [], []]
    for path, dirs, files in os.walk(srcDir):
        files = [file for file in files if file in fileFilter]
        srcFiles = [os.path.join(path, file) for file in files]
        dstFiles = [file.replace(srcDir, dstDir) for file in srcFiles]
        fileSizes = [os.path.getsize(file) for file in srcFiles]
        dirs = [os.path.join(path, dirdir) for dirdir in dirs]
        newDirs.extend([dirdir.replace(srcDir, dstDir) for dirdir in dirs])
        fileTotal += len(files)
        sizeTotal += sum(fileSizes)
        readyFiles[0].extend(srcFiles)
        readyFiles[1].extend(dstFiles)
        readyFiles[2].extend(fileSizes)
    readyFiles = tuple(zip(*readyFiles))
    newDirs = uniqueDirs(newDirs)
    return fileTotal, sizeTotal, tuple(newDirs), readyFiles

def uniqueDirs(dirs):
    for dirA in list(dirs):
        for dirB in list(dirs):
            if dirB in dirA and dirB != dirA:
                dirs.pop(dirs.index(dirB))
                return uniqueDirs(dirs)
            elif dirA in dirB and dirB != dirA:
                dirs.pop(dirs.index(dirA))
                return uniqueDirs(dirs)
    return dirs

def copyTreeGUI(srcDir, dstDir, fileFilter):
    structureFiles = prepareFiles(srcDir, dstDir, fileFilter)
    queue = Queue.Queue()
    if os.name == "posix":
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="scidmint")
    else:
        root = tk.Tk()
    CopyGui(root, queue, structureFiles[0], structureFiles[1])
    copyTreeTHREAD(queue, structureFiles)
    root.mainloop()


def copyTreeTHREAD(queue, structureFiles):
    fileCount, totalSize, newDirs, files = structureFiles
    for newDir in newDirs:
        os.makedirs(newDir, exist_ok=True)
    for file in files:

        fileCount -= 1
        totalSize -= file[2]
        forQueue = (os.path.basename(file[0]), os.path.dirname(file[0]),
                    os.path.dirname(file[1]), fileCount, totalSize, 1)
        queue.put(forQueue)
        shutil.copy(file[0], file[1])
    queue.put((0, 0, 0, 0, 0, 0))

def folderShortener(folder, length):
    if len(folder) <= length:
        return folder
    else:
        splitFolder = folder.split('\\')
        if folder.startswith('\\\\'):
            pass
        else:
            if len(splitFolder[1]+splitFolder[-1])+9 <= length:
                return '\\'.join((splitFolder[0], splitFolder[1], '...',
                                  splitFolder[-1]))
            else:
                if len(splitFolder[1]) > len(splitFolder[-1]):
                     diff = (len(splitFolder[1]+splitFolder[-1])+8) - length
                     splitFolder[1] = splitFolder[1][:-(abs(length)+3)] + '...'
                     return '\\'.join((splitFolder[0], splitFolder[1],
                                       splitFolder[-1]))
                else:
                     diff = (len(splitFolder[1]+splitFolder[-1])+8) - length
                     splitFolder[-1] = '...' + splitFolder[-1][(abs(length)+3):]
                     return '\\'.join((splitFolder[0], splitFolder[1],
                                       splitFolder[-1]))

if __name__== "__main__":
    config = SafeConfigParser()
    tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
    conf_file = tmp_dir + "/pwb.ini"
    config.read(conf_file)

    app = gui('         Copy wim archives', useTtk=True, colspan=5)
    # TODO: Hvordan midtstille tittel uten space først?
    app.setSize("400x370")
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

    app.addButtons(["Submit", "Clear"], [submit, clear], row=12)
    app.go()


                                       
                                                                                                   


