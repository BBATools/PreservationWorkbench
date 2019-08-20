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

from configparser import SafeConfigParser
from appJar import gui
import os
if os.name == "posix":
    from ttkthemes import ThemedTk
    # TODO: Bruk zenity direkte med subprocess heller -> fjerner gtk fm samt færre begrensninger
    from zenipy import file_selection

# WAIT: Legg inn meny for å velge connection profiles definert i WbProfiles.xml
# WAIT: Lag sjekkboks for å velge om eksport til fil eller h2
# WAIT: http://appjar.info/pythonEvents/#stopping-the-gui

def add_config_section(s, section_name):
    if not s.has_section(section_name):
        s.add_section(section_name)


def submit(btn):
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    add_config_section(config, 'ENV')
    config.set('ENV', 'data_dir', data_dir)
    
    add_config_section(config, 'SYSTEM')
    sys_name = app.getEntry("sys_name")
    config.set('SYSTEM', 'sys_name', sys_name)

    add_config_section(config, 'DATABASE')
    db_name = app.getEntry("db_name")
    config.set('DATABASE', 'db_name', db_name)
    db_schema = app.getEntry("db_schema")
    config.set('DATABASE', 'db_schema', db_schema)

    dir_paths = app.getAllListItems("Directories")
    i = 1
    paths = {}
    for path in dir_paths:
        paths["dir" + str(i)] = path
        i += 1
    add_config_section(config, 'DOCUMENTS')
    for key in paths.keys():
        config.set('DOCUMENTS', key, paths[key])

    with open(conf_file, "w+") as configfile:
        config.write(configfile, space_around_delimiters=False)

    # Clear log file:
    open(tmp_dir + "/PWB.log", 'w').close()

    app.stop()


def clear(btn):
    app.clearAllEntries()
    app.clearAllTextAreas()
    app.clearAllListBoxes()


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

    app = gui('         System Details', useTtk=True, colspan=5)
    # TODO: Hvordan midtstille tittel uten space først?
    app.setSize("400x470")
    app.setLocation("CENTER")
    app.setStretch("column")

    if os.name == "posix":
        app.setTtkTheme('scidmint')
    else:
        app.setTtkTheme("winnative")

    app.addLabel("l1", "System Name:", 0, 0)
    app.addEntry("sys_name", 1, 0)
    app.setFocus("sys_name")

    app.addLabel("l2", "Database Name:", 2, 0)
    app.addEntry("db_name", 3, 0)

    app.addLabel("l3", "Database Schema:", 4, 0)
    app.addEntry("db_schema", 5, 0)

    app.addLabel("l4", "Documents:", 6, 0)
    app.setSticky("new")
    app.addEntry("dir_path", 7, 0, 5)
    app.setSticky("ne")
    app.addButton("Directory", add_dir, 7, 4, 1)

    app.setSticky("new")
    app.addLabel("l5", "Directories:", 8, 0)
    app.addListBox("Directories", row=9, rowspan=6)

    app.setEntryDefault("sys_name", "System Name")
    app.setEntryDefault("db_name", "Database Name")
    app.setEntryDefault("db_schema", "Database Schema")
    app.setEntryDefault("dir_path", "-- enter a directory --")

    # WAIT: Splitt ut som egen funksjon:
    if os.path.exists(conf_file):
        config.remove_section("DOCUMENTS")
        if config.has_option('SYSTEM', 'sys_name'):
            conf_sys_name = config.get('SYSTEM', 'sys_name')
            if not conf_sys_name == '':
                app.setEntry("sys_name", conf_sys_name)
        if config.has_option('DATABASE', 'db_name'):
            conf_db_name = config.get('DATABASE', 'db_name')
            if not conf_db_name == '':
                app.setEntry("db_name", conf_db_name)
        if config.has_option('DATABASE', 'db_schema'):
            conf_db_schema = config.get('DATABASE', 'db_schema')
            if not conf_db_schema == '':
                app.setEntry("db_schema", conf_db_schema)

    app.addButtons(["Submit", "Clear ", " Quit "], [submit, clear, quit], row=16)
    app.go()


