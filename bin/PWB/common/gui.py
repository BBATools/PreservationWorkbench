#! python3

# Copyright (C) 2020 Morten Eek

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

import subprocess, os

def pwb_add_wim_file(data_dir):
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