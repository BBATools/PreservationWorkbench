#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0') 
from gi.repository import Gtk, Gdk, GObject

def pwb_choose_file(folder = False):
    win = Gtk.Window ()
    result= []
    file_action = Gtk.FileChooserAction.OPEN
    message = 'Open File'
    if folder:
        file_action = Gtk.FileChooserAction.SELECT_FOLDER
        message = 'Open Folder'

    def run_dialog(_None):
        dialog = Gtk.FileChooserDialog(message, win,file_action,(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, Gtk.ResponseType.OK)) 
        dialog.set_modal(True)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            result.append(dialog.get_filename())
        else:
            result.append(None)

        dialog.destroy()
        Gtk.main_quit()

    Gdk.threads_add_idle(GObject.PRIORITY_DEFAULT, run_dialog, None)
    Gtk.main()
    return result[0]

    while Gtk.events_pending():
        Gtk.main_iteration()


