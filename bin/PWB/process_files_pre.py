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
import pathlib
import glob
import sys
import shutil
from configparser import SafeConfigParser
from common.gui import pwb_add_wim_file
from appJar import gui
import jaydebeapi
import xml.etree.ElementTree as ET
from common.config import pwb_add_config_section

# TODO: Endre så en logg pr subsystem heller


def kill(proc_id):
    os.kill(proc_id, signal.SIGINT)


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def run_shell_command(command, cwd=None):
    ok = False
    os.environ['PYTHONUNBUFFERED'] = "1"
    stdout = []
    stderr = []
    mix = []

    print(command)
    sys.stdout.flush()

    proc = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
    )

    for line in proc.stdout:
        stdout.append(line.rstrip())

    for line in proc.stderr:
        stderr.append(line.rstrip())

    return proc.returncode, stdout, stderr


def quit(conf_file):
    config = SafeConfigParser()
    pwb_add_config_section(config, 'ENV')
    config.set('ENV', 'wim_path', "")
    with open(conf_file, "w+") as configfile:
        config.write(configfile, space_around_delimiters=False)
    sys.exit()


def mount_wim(filepath, mount_dir):
    pathlib.Path(mount_dir).mkdir(parents=True, exist_ok=True)
    if len(os.listdir(mount_dir)) == 0:
        subprocess.run(
            "GVFS_DISABLE_FUSE=1; export GVFS_DISABLE_FUSE; wimmountrw --allow-other "
            + filepath + " " + mount_dir,
            shell=True)


if __name__ == "__main__":
    config = SafeConfigParser()
    bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    tmp_dir = os.path.join(bin_dir, 'tmp')
    conf_file = tmp_dir + "/pwb.ini"
    config.read(conf_file)
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    h2_to_tsv_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'xslt/h2_to_tsv.xslt'))
    wbexport_script = os.path.join(tmp_dir, 'wbexport.sql')

    if os.name != "posix":
        app = gui(useTtk=True)
        app.setLocation("CENTER")
        app.setTtkTheme("winnative")
        app.errorBox("Error", "Only supported on Arkimint")
        sys.exit()

    filepath = pwb_add_wim_file(data_dir)
    if filepath:
        pwb_add_config_section(config, 'ENV')
        config.set('ENV', 'wim_path', filepath)
        config.set('ENV', 'log_file', "system_process_files.log")
        config.set('ENV', 'process', "file")
        with open(conf_file, "w+") as configfile:
            config.write(configfile, space_around_delimiters=False)
    else:
        quit(conf_file)

    sql_file = tmp_dir + "/file_process.sql"
    in_dir = os.path.dirname(filepath) + "/"
    sys_name = os.path.splitext(os.path.basename(filepath))[0]
    mount_dir = data_dir + "/" + sys_name + "_mount"
    av_done_file = in_dir + sys_name + "_av_done"

    open(tmp_dir + "/PWB.log", 'w').close()  # Clear log file
    mount_wim(filepath, mount_dir)
    open(sql_file, 'w').close()  # Blank out between runs

    sub_systems_path = mount_dir + "/content/sub_systems"
    subfolders = os.listdir(sub_systems_path)
    for folder in subfolders:
        if os.path.isdir(
                os.path.join(os.path.abspath(sub_systems_path), folder)):
            data_docs_folder = sub_systems_path + "/" + folder + "/content/data_documents"
            docs_folder = sub_systems_path + "/" + folder + "/content/documents"
            data_folder = sub_systems_path + "/" + folder + "/content/data"
            documentation_folder = sub_systems_path + "/" + folder + "/documentation/"
            header_xml_file = sub_systems_path + "/" + folder + "/header/metadata.xml"
            mod_xml_file = sub_systems_path + "/" + folder + "/documentation/metadata_mod.xml"

            pathlib.Path(data_docs_folder).mkdir(parents=True, exist_ok=True)
            pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
            pathlib.Path(docs_folder).mkdir(parents=True, exist_ok=True)

            glob_data = []
            for file in glob.glob(docs_folder + "/*.wim"):
                export_folder = os.path.splitext(file)[0]
                pathlib.Path(export_folder).mkdir(parents=True, exist_ok=True)
                if len(os.listdir(export_folder)) == 0:
                    subprocess.run(
                        "wimapply " + file + " " + export_folder, shell=True)
                    os.remove(file)

            h2_file = documentation_folder + folder
            h2_done_file = documentation_folder + "done"
            print(h2_done_file)
            if (os.path.isfile(h2_file + ".mv.db")
                    and not os.path.isfile(h2_done_file)):
                conn = jaydebeapi.connect(  # WAIT: Endre til egen def
                    "org.h2.Driver",
                    "jdbc:h2:" + h2_file,
                    ["", ""],
                    bin_dir +
                    "/h2-1.4.196.jar",  # WAIT: Fjern harkodet filnavn
                )

                try:
                    curs = conn.cursor()
                    curs.execute("SHOW TABLES;")
                    data = curs.fetchall()
                    tables_in_h2 = [x[0] for x in data]

                except Exception as e:
                    print(e)

                finally:
                    if curs is not None:
                        curs.close()
                    if conn is not None:
                        conn.close()

                tree = ET.parse(header_xml_file)
                table_defs = tree.findall("table-def")
                for table_def in table_defs:
                    table_name = table_def.find("table-name")
                    disposed = ET.Element("disposed")
                    disposed.text = "false"
                    if table_name.text not in tables_in_h2:
                        disposed.text = "true"

                    table_def.insert(5, disposed)

                root = tree.getroot()
                indent(root)
                tree.write(mod_xml_file)

                xsl = [
                    "\n",
                    "WbXslt -inputfile=" + mod_xml_file,
                    "-stylesheet=" + h2_to_tsv_script,
                    '-xsltParameters="url=jdbc:h2:' + h2_file + '"',
                    '-xsltParameters="outputdir=' + data_folder + '"',
                    "-xsltOutput=" + wbexport_script + ';',
                ]
                with open(tmp_dir + '/h2_to_tsv.sql', "w") as file:
                    file.write("\n".join(xsl))

                # TODO: Lag subprocess def som kalles to ganger her med forskjellige parametre
                cmd = 'java -jar sqlworkbench.jar -script=' + tmp_dir + '/h2_to_tsv.sql'
                returncode, stdout, stderr = run_shell_command(cmd, bin_dir)
                print(stdout)

                cmd = 'java -jar sqlworkbench.jar -script=' + tmp_dir + '/wbexport.sql'
                returncode, stdout, stderr = run_shell_command(cmd, bin_dir)
                print(stdout)

                open(h2_done_file, 'a').close()

            for data_file in glob.iglob(data_folder + "/*.data"):
                shutil.move(data_file, data_docs_folder)
            if len(os.listdir(data_folder)) == 0:
                os.rmdir(data_folder)

            # Remove empty folders
            if os.path.exists(data_docs_folder):
                if len(os.listdir(data_docs_folder)) == 0:
                    os.rmdir(data_docs_folder)
            if os.path.exists(docs_folder):
                if len(os.listdir(docs_folder)) == 0:
                    os.rmdir(docs_folder)
