#! python3
import subprocess
import os
import argparse
import shutil
import glob

parser = argparse.ArgumentParser()
parser.add_argument("--wim", "-w", help="Set wim path")
parser.add_argument("--proc", "-p", help="Set process name")
args = parser.parse_args()

wim_file = args.wim
proc = args.proc
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
package_dir = os.path.abspath("../_DATA/" + sys_name)
mount_dir = package_dir + "_mount"

shutil.rmtree(mount_dir, ignore_errors=True)

if proc == 'file':
  md5sum_file = os.path.splitext(wim_file)[0]+'_md5sum.txt'
  if os.path.isfile(md5sum_file):
    os.remove(md5sum_file)
elif proc == 'meta':
  documentation_folder = package_dir + "/content/documentation/"
  done_files = glob.glob(documentation_folder + "*_done")
  for f in done_files:
    os.remove(f)

  sub_systems_path = package_dir + "/content/sub_systems/"
  subfolders = os.listdir(sub_systems_path)
  for folder in subfolders:
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)):
      sub_documentation_folder = sub_systems_path + folder + "/documentation/"
      header_folder = sub_systems_path + folder + "/header/"

      mod_xml = sub_documentation_folder + "metadata_mod.xml"
      header_xml = header_folder + "metadata.xml"
      shutil.copyfile(mod_xml, header_xml)
      os.remove(mod_xml)

      mod_sql = sub_documentation_folder + "metadata.sql"
      header_sql = header_folder + "metadata.sql"
      shutil.copyfile(mod_sql, header_sql)
      os.remove(mod_sql)

      sub_done_files = glob.glob(sub_documentation_folder + "*_done")
      for f in sub_done_files:
        os.remove(f)
