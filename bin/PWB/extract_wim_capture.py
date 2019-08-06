#! python3

from configparser import SafeConfigParser
import subprocess, os, shutil

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)

if config.has_option('ENV', 'data_dir'):
    data_dir = config.get('ENV', 'data_dir') + "/"

if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')

if config.has_option('SYSTEM', 'subsys_name'):
    subsys_name = config.get('SYSTEM', 'subsys_name')

if config.has_option('DOCUMENTS', 'dir1'):
    source_doc_paths = dict(config.items('DOCUMENTS'))
    base_path = data_dir + "/" + sys_name + "/content/sub_systems/" + subsys_name + "/content/documents/"
    pwb_dir = os.path.abspath(os.path.join(tmp_dir, '..', 'PWB'))
    for key, value in source_doc_paths.items():
        source_doc_path = value
        target_doc_path = base_path + key + ".wim"
        wim_cmd = pwb_dir + "/wimlib-imagex capture "
        if os.name == "posix":
            wim_cmd = "wimcapture "
        subprocess.run(wim_cmd + source_doc_path + " " + target_doc_path +
                    " --no-acls --compress=none", shell=True)

# Save log-file to documentation directory
shutil.copyfile(tmp_dir + "/PWB.log", data_dir + "/" + sys_name + "/content/sub_systems/" + subsys_name + "/documentation/export.log")