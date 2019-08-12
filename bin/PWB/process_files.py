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

import subprocess
import os
import argparse
import pathlib
import glob
import shutil
import sys

# TODO: Endre så en logg pr subsystem heller

parser = argparse.ArgumentParser()
parser.add_argument("--wim", "-w", help="set wim path")
parser.add_argument(
    "--pre",
    "-p",
    help="pre/post sql processing",
    default=False,
    type=lambda x: (str(x).lower() == "true"),
)
args = parser.parse_args()

pre = args.pre
filepath = args.wim
sql_file = os.path.abspath("tmp/file_process.sql")
in_dir = os.path.dirname(filepath) + "/"
sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = os.path.abspath("../_DATA/" + sys_name + "_mount")
av_done_file = in_dir + sys_name + "_av_done"

open(sql_file, 'w').close()  # Blank out between runs

sub_systems_path = mount_dir + "/content/sub_systems"
subfolders = os.listdir(sub_systems_path)
for folder in subfolders:
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)):
        data_docs_folder = sub_systems_path + "/" + folder + "/content/data_documents"
        docs_folder = sub_systems_path + "/" + folder + "/content/documents"
        data_folder = sub_systems_path + "/" + folder + "/content/data"
        documentation_folder = sub_systems_path + "/" + folder + "/documentation/"

        if pre:
            pathlib.Path(data_docs_folder).mkdir(parents=True, exist_ok=True)
            pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
            pathlib.Path(docs_folder).mkdir(parents=True, exist_ok=True)

        if not pre:
            for data_file in glob.iglob(data_folder + "/*.data"):
                shutil.move(data_file, data_docs_folder)
            if len(os.listdir(data_folder)) == 0:
                os.rmdir(data_folder)

        if pre:
            glob_data = []
            for file in glob.glob(docs_folder + "/*.wim"):
                export_folder = os.path.splitext(file)[0]
                pathlib.Path(export_folder).mkdir(parents=True, exist_ok=True)
                if len(os.listdir(export_folder)) == 0:
                    subprocess.run("wimapply " + file + " " +
                                   export_folder, shell=True)
                    os.remove(file)

        h2_file = documentation_folder + folder
        h2_done_file = documentation_folder + "done"
        if (
            pre
            and os.path.isfile(h2_file + ".mv.db")
            and not os.path.isfile(h2_done_file)
        ):
            sql = [
                "\n",
                "WbConnect -url=" + "jdbc:h2:" + h2_file + " -password='';",
                '''WbVarDef fixColumns= @"SELECT GROUP_CONCAT('ALTER TABLE ' || TABLE_NAME  || ' ALTER COLUMN ' || COLUMN_NAME || ' RENAME TO ' || COLUMN_NAME || '_;') FROM (
                    SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA='PUBLIC'
                    AND COLUMN_NAME='INTERVAL')";''',
                '''WbSysExec basename '$[fixColumns]' > ~/bin/PWB/bin/tmp/wim_h2_fix.sql;''',
                '''WbSysExec sed -i 's/ INTERVAL / "INTERVAL" /' ~/bin/PWB/bin/tmp/wim_h2_fix.sql;''',
                # '''WbSysExec -program="sed" -argument="-i 's/\INTERVAL\/"INTERVAL"/' ~/bin/PWB/bin/tmp/wim_h2_fix.sql";''',
                "WbInclude -file=/home/bba/bin/PWB/bin/tmp/wim_h2_fix.sql -displayResult=false -verbose=false -continueOnError=false;",
                "COMMIT;",
                "WbExport",
                "-type=text",
                "-schema=PUBLIC",
                "-types=TABLE",
                "-sourceTable=*",
                "-outputdir=" + data_folder,
                "-continueOnError=false",
                "-encoding=UTF8",
                "-header=true",
                "-decimal='.'",
                "-maxDigits=0",
                "-lineEnding=crlf",
                "-clobAsFile=true",
                "-blobType=file",
                "-delimiter=\t",
                "-replaceExpression='(\\n|\\r\\n|\\r|\\t)' -replaceWith=' '",
                "-showProgress=10000;",
                "-nullString=''",
                "WbDisconnect;",
                "WbSysExec touch " + documentation_folder + "done;",
            ]

            with open(sql_file, "a+") as file:
                file.write("\n".join(sql))

        # Remove empty folders
        if not pre and os.path.exists(data_docs_folder):
            if len(os.listdir(data_docs_folder)) == 0:
                os.rmdir(data_docs_folder)
        if os.path.exists(docs_folder):
            if len(os.listdir(docs_folder)) == 0:
                os.rmdir(docs_folder)
