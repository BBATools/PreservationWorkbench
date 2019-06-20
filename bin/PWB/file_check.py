#! python3
import subprocess, os, argparse, pathlib, glob, shutil, json, csv, sys
import pandas as pd

# TODO: Legg inn sjekk på om wim-fil er mountet og msgbox og sys.exit hvis ikke

parser = argparse.ArgumentParser()
parser.add_argument("--wim", "-w", help="set wim path")
args = parser.parse_args()

wim_file = args.wim
in_dir = os.path.dirname(wim_file) + "/"
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
mount_dir = os.path.abspath("../_DATA/" + sys_name + "_mount")
sav_file = "/tmp/savscan_result.txt"
av_done_file = mount_dir + "/content/documentation/av_done"
meta_done_file = mount_dir + "/content/documentation/meta_done"
viruses = False
sub_systems_path = mount_dir + "/content/sub_systems"
tika_path = "~/bin/tika/tika-app-1.20.jar"

def flatten_folder(destination, tsv_log = None):
    all_files = []
    first_loop_pass = True
    for root, _dirs, files in os.walk(destination):
        if first_loop_pass:
            first_loop_pass = False
            continue
        for filepath in files:
            all_files.append(os.path.join(root, filepath))
    for filepath in all_files:
        filename = os.path.basename(filepath)
        file_ext = pathlib.Path(filename).suffix
        file_base = os.path.splitext(filename)[0]
        uniq = 1
        new_path = destination + "/%s%d%s" % (file_base, uniq, file_ext)

        while os.path.exists(new_path):
            new_path = destination + "/%s%d%s" % (file_base, uniq, file_ext)
            uniq += 1
        shutil.move(filepath, new_path)

def to_string(s):
    try:
        return str(s)
    except:
        # Change the encoding type if needed
        return self.encode("utf-8")


def reduce_item(key, value):
    global reduced_item
    # Reduction Condition 1
    if type(value) is list:
        i = 0
        for sub_item in value:
            reduce_item(to_string(i), sub_item)
            i = i + 1
    # Reduction Condition 2
    elif type(value) is dict:
        sub_keys = value.keys()
        for sub_key in sub_keys:
            reduce_item(
                to_string(sub_key).replace(":", "_").replace("-", "_"), value[sub_key]
            )
    # Base Condition
    else:
        reduced_item[to_string(key)] = to_string(value)

if not os.path.isfile(av_done_file):
    subprocess.run('echo "Checking for viruses...."', shell=True)
    subprocess.run(
        ">"
        + sav_file
        + " && savscan -sc -rec -c -archive -suspicious --stay-on-filesystem --stay-on-machine --backtrack-protection --preserve-backtrack --examine-x-bit -p="
        + sav_file
        + " "
        + mount_dir,
        shell=True,
    )
    with open(sav_file) as f:
        if "No viruses were discovered." in f.read():
            with open(av_done_file, "w+") as file:
                file.write(" ")
        else:
            viruses = True

# TODO: Melding + hva hvis finnes virus?
if not viruses:
    with open(av_done_file, "w+") as file:
        file.write(" ")


if not os.path.isfile(meta_done_file):
    subprocess.run('echo "Extracting metadata from files...."', shell=True)
    sub_folders = [f.path for f in os.scandir(sub_systems_path) if f.is_dir()]
    for dir in sub_folders:
        doc_folders = [
            f.path
            for f in os.scandir(dir + "/content")
            if (f.is_dir() and f.name != "data" and not f.name.endswith("_tmp"))
        ]
        for folder in doc_folders:
            tmp_folder = folder + "_tmp"
            pathlib.Path(tmp_folder).mkdir(parents=True, exist_ok=True)
            header_file = (
                dir
                + "/header/"
                + os.path.basename(os.path.dirname(folder + "/"))
                + ".tsv"
            )

            if os.path.isfile(header_file):
                continue

            # TODO: Fjerne først evt filer som er 0kb ?
            # Process with Tika:
            if len(os.listdir(tmp_folder)) == 0:
                subprocess.run(
                    "java -jar "
                    + tika_path
                    + " -J -m -i "
                    + folder
                    + " -o "
                    + tmp_folder,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    shell=True,
                )

            # Flatten tmp folder structure before merging of json-files
            flatten_folder(tmp_folder)

            # Merge Tika-generated files:
            if not os.path.isfile(tmp_folder + "/merged.json"):
                glob_data = []
                for file in glob.glob(tmp_folder + "/*.json"):
                    with open(file) as json_file:
                        data = json.load(json_file)
                        i = 0
                        while i < len(data):
                            glob_data.append(data[i])
                            i += 1

                with open(tmp_folder + "/merged.json", "w") as f:
                    json.dump(glob_data, f, indent=4)

            # Convert merged file to tsv:
            if os.path.isfile(tmp_folder + "/merged.json") and not os.path.isfile(
                tmp_folder + "/merged.tsv"
            ):
                node = ""
                fp = open(tmp_folder + "/merged.json", "r")
                json_value = fp.read()
                raw_data = json.loads(json_value)
                fp.close()

                try:
                    data_to_be_processed = raw_data[node]
                except:
                    data_to_be_processed = raw_data

                processed_data = []
                header = []
                for item in data_to_be_processed:
                    reduced_item = {}
                    reduce_item(node, item)
                    header += reduced_item.keys()
                    processed_data.append(reduced_item)

                header = list(set(header))
                header.sort()

                with open(tmp_folder + "/merged.tsv", "w+") as f:
                    writer = csv.DictWriter(f, header, delimiter="\t")
                    writer.writeheader()
                    for row in processed_data:
                        writer.writerow(row)

                # Remove some columns
                df = pd.read_csv(tmp_folder + "/merged.tsv", sep="\t")
                df.drop(
                    [
                        "0",
                        "1",
                        "X_TIKA_parse_time_millis",
                        "access_permission_assemble_document",
                        "access_permission_can_modify",
                        "access_permission_can_print",
                        "access_permission_can_print_degraded",
                        "access_permission_extract_content",
                        "access_permission_extract_for_accessibility",
                        "access_permission_fill_in_form",
                        "access_permission_modify_annotations",
                    ],
                    axis=1,
                    errors="ignore",
                    inplace=True,
                )
                df.to_csv(header_file, index=False, sep="\t")
                # TODO: Aktiver linjer under igjen når feil over fikset 
                if os.path.isfile(header_file):
                    shutil.rmtree(tmp_folder)

# TODO: Legg inn tester før linjer under kjøres
with open(meta_done_file, "w+") as file:
    file.write(" ")

