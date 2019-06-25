import subprocess
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--path", "-p", help="set path")
parser.add_argument("--system", "-s", help="set system")
parser.add_argument("--subsystem", "-b", help="set subsystem")
parser.add_argument(
    "--datapackage",
    "-dp",
    help="Capture to SIP?",
    default=False,
    type=lambda x: (str(x).lower() == "true"),
)
args = parser.parse_args()

sys_name = args.system
path = args.path
subsystem = args.subsystem
dp = args.datapackage

if dp:
    new_path = "../../_DATA/" + sys_name + ".wim"
else:
    uniq = 1
    new_base_path = "../../_DATA/" + sys_name + \
        "/content/sub_systems/" + subsystem + "/content/documents"
    new_path = new_base_path + "/%s%d%s" % ("dir", uniq, ".wim")

    while os.path.exists(new_path):
        new_path = new_base_path + "/%s%d%s" % ("dir", uniq, ".wim")
        uniq += 1

wim_cmd = r"..\PWB\wimlib-imagex capture "
if os.name == "posix":
    wim_cmd = "wimcapture "
subprocess.run(wim_cmd + path + " " + new_path +
               " --no-acls --compress=none", shell=True)
