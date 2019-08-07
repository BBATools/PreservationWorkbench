#! python3

from configparser import SafeConfigParser
import subprocess, os, hashlib, shutil

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)

def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


if config.has_option('ENV', 'data_dir'):
    data_dir = config.get('ENV', 'data_dir') + "/"

if config.has_option('SYSTEM', 'sys_name'):
    sys_name = config.get('SYSTEM', 'sys_name')
    pwb_dir = os.path.abspath(os.path.join(tmp_dir, '..', 'PWB'))
    
    wim_cmd = pwb_dir + "/wimlib-imagex capture "
    if os.name == "posix":
        wim_cmd = "wimcapture "
    wim_file = data_dir + sys_name + ".wim"
    subprocess.run(wim_cmd + data_dir + sys_name + " " + wim_file +
                " --no-acls --compress=none", shell=True)

    md5sumFile = os.path.splitext(wim_file)[0] + "_md5sum.txt"
    check = md5sum(wim_file)
    print(check)

    f = open(md5sumFile, "w+")
    f.write(check)
    f.close()

    shutil.rmtree(data_dir + sys_name, ignore_errors=True)



