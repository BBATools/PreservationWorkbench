import subprocess
import os
import argparse
import pathlib
import pandas as pd

# TODO: Legg inn sjekk på om wim-fil er mountet og msgbox og sys.exit hvis ikke

parser = argparse.ArgumentParser()
parser.add_argument("--wim", "-w", help="set wim path")
args = parser.parse_args()

wim_file = args.wim
in_dir = os.path.dirname(wim_file) + "/"
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
mount_dir = os.path.abspath("../_DATA/" + sys_name)
convert_done_file = in_dir + sys_name + "_convert_done"
sub_systems_path = mount_dir + "/content/sub_systems"
convert_done = False

if not os.path.isfile(convert_done_file):
    pathlib.Path(mount_dir).mkdir(parents=True, exist_ok=True)
    if len(os.listdir(mount_dir)) == 0:
        subprocess.run("GVFS_DISABLE_FUSE=1; export GVFS_DISABLE_FUSE; wimmountrw --allow-other " + in_dir + sys_name +
                       ".wim " + mount_dir, shell=True)

    sub_folders = [f.path for f in os.scandir(
        sub_systems_path) if f.is_dir() and len(os.listdir(f)) != 0]  # TODO: samme lengdesjekk i "file_check.py"?
    for dir in sub_folders:
        doc_folders = [
            f.path
            for f in os.scandir(dir + "/content")
            if (f.is_dir() and f.name != "data" and not f.name.endswith("_tmp"))
        ]
        for folder in doc_folders:
            tmp_folder = folder + "_tmp"
            pathlib.Path(tmp_folder).mkdir(parents=True, exist_ok=True)

            for dirpath, dirnames, filenames in os.walk(folder):
                structure = os.path.join(
                    tmp_folder, os.path.relpath(dirpath, folder))
                pathlib.Path(structure).mkdir(parents=True, exist_ok=True)

            header_file = (
                dir
                + "/header/"
                + os.path.basename(os.path.dirname(folder + "/"))
                + ".tsv"
            )

            # TODO: https://stackoverflow.com/questions/43847926/python-loop-through-a-csv-file-row-values
            # TODO: Oppdatere tsv først med hva som skal bli og så loope gjennom og så sjekke på disk?
            # TODO: Bruk for å legge til rette extension på .data-filer? https://github.com/timothyryanwalsh/addext
            # WAIT: Test denne for filer Tika ikke tar? https://github.com/h2non/filetype.py/blob/master/README.rst
            # TODO: Test mot denne filen: "endret extension fra tif.doc"
            # TODO: Generer DDL for "header_file"
            # TODO: Unoconv: test  -P option for converting spreadsheets into PDFs in landscape
            # TODO: Generer også (samtidig som telle antall filer) en tsv som bare inneholder viktigste kolonner
            # --> legge denne i data-mappe for import til innsyn mens den originale med alt blir liggende i header?
            # TODO: Gå gjennom alle pdf til slutt og konvertere til pdf/a hvis ikke allerede?
            # tika_file_ext er det som var på filen og sier ikke at det stemmer med formatet
            # TODO: Fjern alle Thumbs.db
            # TODO: Testede formater med unoconv (eg unoconv -f pdf test.doc):
            #  Virker bra: doc, wp, wps, odt, xls/xlsm/xlsx (unoconv -P PaperOrientation=landscape)
            # Virker ikke bra: tif, mht
            # Ikke aktuelt å konvertere: xsd, xml
            # TODO: Testede formater med ODAFileConverter (eg ODAFileConverter "dffsd/" "dffsd/" "ACAD2013" "DXF" "0" "1" "BK_1_10762480_dwg.dwg"):
            # TODO: en til mange til ukomprimert zip hvis ikke alle kan konverteres til pdf
            # Skriv alle filer som er korrupt eller må manuelt behandles til en tsv-fil til slutt og åpne denne
            # TODO: Test denne for pdf til pdf/a: https://github.com/AndreasPetter/PDF2PDFa/blob/master/de/pettersystems/pdf2pdfa/pdf2pdfa.py
            # --> se også disse:
            #	https://stackoverflow.com/questions/1659147/how-to-use-ghostscript-to-convert-pdf-to-pdf-a-or-pdf-x
            #	https://unix.stackexchange.com/questions/79516/converting-pdf-to-pdf-a
            # 	https://superuser.com/questions/188953/how-to-convert-a-pdf-to-a-pdf-a
            # Filtrere tsv: https://kanoki.org/2019/03/27/pandas-select-rows-by-condition-and-string-operations/
            #		    https://kite.com/blog/python/pandas-tutorial
            df = pd.read_csv(header_file, sep="\t")
            df.tika_batch_fs_relative_path = df.tika_batch_fs_relative_path.fillna(
                'embedded file')  # filer som er embedded i andre
            for index, row in df.iterrows():
                path = str(row['tika_batch_fs_relative_path'])
                if(path != 'embedded file'):
                    # print(str(index + 2), path)  # index +2 så ihht exel/libre
                    # TODO: Sjekk først at antall linjer stemmer med antall filer på disk -> dialog hvis ikke
                    type = row['Content_Type']
                    if type == 'application/pdf':
                        print("pdf")
                    elif type in ('application/x-tika-msoffice'):
                        print("office")
