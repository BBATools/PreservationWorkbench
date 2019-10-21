import subprocess, os, shutil, argparse
import pathlib
import pandas as pd
from pathlib import Path
from configparser import SafeConfigParser
from pgmagick.api import Image
from pdfy import Pdfy

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
wim_file = config.get('ENV', 'wim_path')
in_dir = os.path.dirname(wim_file) + "/"
sys_name = os.path.splitext(os.path.basename(wim_file))[0]
mount_dir = data_dir + "/" + sys_name + "_mount"
convert_done_file = in_dir + sys_name + "_convert_done"
sub_systems_path = mount_dir + "/content/sub_systems"
convert_done = False


def file_copy(src, dst):
    ok = False
    try:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copyfile(src, dst)
    except Exception as e:
        print(e)
        ok = False
    return ok


def image2norm(image_path, norm_path):
    ok = False
    try:
        img = Image(image_path)
        img.write(norm_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


# WAIT: Test denne: https://github.com/xrmx/pylokit
def office2x(file_path, norm_path, format, file_type):
    ok = False
    # command = ['unoconv', '-f', format, '-o', '"' + norm_path + '"','"' + file_path + '"']
    # command = ['unoconv', '-f', format, '-o', norm_path,file_path]
    command = ['unoconv', '-f', format]

    if file_type in (
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ):
        if format == 'pdf':
            command.extend([
                '-d', 'spreadsheet', '-P', 'PaperOrientation=landscape',
                '-eSelectPdfVersion=1'
            ])
            # command.append('-eSelectPdfVersion=1')
            # command.insert(1,'-eSelectPdfVersion=1')
        elif format == 'html':
            command.extend(
                ['-d', 'spreadsheet', '-P', 'PaperOrientation=landscape'])
            # command.insert(1, '-d')
            # command.insert(2, 'spreadsheet')
            # command.insert(1, '-d spreadsheet -P PaperOrientation=landscape')
            # TODO: Noen av valgene her også når til pdf direkte
    elif file_type in ('application/msword', 'application/rtf'):
        command.extend([
            '-d', 'document',
            '-eSelectPdfVersion=1'
        ])

    command.extend(['-o', norm_path, file_path])
    try:
        subprocess.check_call(command)
        ok = True
    except subprocess.CalledProcessError as e:
        print('CalledProcessorError', e)
        ok = False
    return ok


# WAIT: Se for flere gs argumenter: https://superuser.com/questions/360216/use-ghostscript-but-tell-it-to-not-reprocess-images
def pdf2pdfa(pdf_path, pdfa_path):
    # because of a ghostscript bug, which does not allow parameters that are longer than 255 characters
    # we need to perform a directory changes, before we can actually return from the method
    ok = False
    cwd = os.getcwd()
    os.chdir(os.path.dirname(pdfa_path))
    ghostScriptExec = [
        'gs', '-dPDFA', '-dBATCH', '-dNOPAUSE',
        '-sProcessColorModel=DeviceRGB', '-sDEVICE=pdfwrite',
        '-dColorConversionStrategy=/LeaveColorUnchanged',
        '-dEncodeColorImages=false', '-dEncodeGrayImages=false',
        '-dEncodeMonoImages=false', '-dPDFACompatibilityPolicy=1'
    ]
    try:
        subprocess.check_output(
            ghostScriptExec +
            ['-sOutputFile=' + os.path.basename(pdfa_path), pdf_path])
        ok = True
    except subprocess.CalledProcessError as e:
        ok = False
        raise RuntimeError(
            "command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output))
    os.chdir(cwd)
    return ok


# WAIT: Brukes for annet enn html? Støtter alt chrome kan lese
def html2pdf(file_path, tmp_path):
    ok = False
    try:
        p = Pdfy()
        p.html_to_pdf(file_path, tmp_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


def file_convert(file_full_path, file_type, tmp_ext, norm_ext):
    file_name = os.path.basename(file_full_path)
    if tmp_ext:
        tmp_file_full_path = folder + '_normalized/' + file_rel_path + '.tmp.' + tmp_ext
    else:
        tmp_file_full_path = folder + '_normalized/' + file_rel_path + '.tmp.pwb'
    norm_folder_full_path = folder + '_normalized/' + os.path.dirname(
        file_rel_path)
    norm_file_full_path = norm_folder_full_path + '/' + os.path.splitext(
        file_name)[0] + '.norm.' + norm_ext

    if not os.path.isfile(norm_file_full_path):
        pathlib.Path(norm_folder_full_path).mkdir(parents=True, exist_ok=True)
        norm_exists = False
        tmp_exists = False
        if (not os.path.isfile(tmp_file_full_path)
                or tmp_ext == None):  #TODO: Trengs ext-sjekk lenger?
            if file_type in ('image/tiff', 'image/jpeg'):
                tmp_exists = image2norm(file_full_path, tmp_file_full_path)
            elif file_type == 'image/gif':
                norm_exists = image2norm(file_full_path, norm_file_full_path)
            elif file_type == 'application/pdf':
                norm_exists = pdf2pdfa(file_full_path, norm_file_full_path)
            elif file_type in ('image/png', 'text/plain; charset=ISO-8859-1',
                               'text/plain; charset=UTF-8'):
                norm_exists = file_copy(file_full_path, norm_file_full_path)
            elif file_type in (
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ):
                if tmp_ext == None:
                    norm_exists = office2x(file_full_path, norm_file_full_path,
                                           'pdf', file_type)
                else:
                    tmp_exists = office2x(file_full_path, tmp_file_full_path,
                                          'html', file_type)
            elif file_type.startswith('text/html'):
                tmp_exists = html2pdf(file_full_path, tmp_file_full_path)
            elif file_type in ('application/msword', 'application/rtf'):
                norm_exists = office2x(file_full_path, norm_file_full_path,
                                       'pdf', file_type)
        if tmp_exists:
            if tmp_ext == 'pdf':
                norm_exists = pdf2pdfa(tmp_file_full_path, norm_file_full_path)
            elif tmp_ext == 'html':
                norm_exists = office2x(tmp_file_full_path, norm_file_full_path,
                                       'pdf')

        if norm_exists and tmp_exists:
            os.remove(tmp_file_full_path)
        # TODO: Oppdater tsv her eller i kode som looper tsv under ?
        # TODO: Legg inn hvilken originalfiler som skal slettes


if not os.path.isfile(convert_done_file):
    pathlib.Path(mount_dir).mkdir(parents=True, exist_ok=True)
    if len(os.listdir(mount_dir)) == 0:
        subprocess.run(
            "GVFS_DISABLE_FUSE=1; export GVFS_DISABLE_FUSE; wimmountrw --allow-other "
            + in_dir + sys_name + ".wim " + mount_dir,
            shell=True)

    sub_folders = [
        f.path for f in os.scandir(sub_systems_path)
        if f.is_dir() and len(os.listdir(f)) != 0
    ]  # TODO: samme lengdesjekk i "file_check.py"?
    for dir in sub_folders:
        doc_folders = [
            f.path for f in os.scandir(dir + "/content")
            if (f.is_dir() and f.name in ('documents', 'data_documents'))
        ]

        for folder in doc_folders:
            tmp_folder = folder + "_tmp"
            pathlib.Path(tmp_folder).mkdir(parents=True, exist_ok=True)

            for dirpath, dirnames, filenames in os.walk(folder):
                structure = os.path.join(tmp_folder,
                                         os.path.relpath(dirpath, folder))
                pathlib.Path(structure).mkdir(parents=True, exist_ok=True)

            header_file = (dir + "/header/" + os.path.basename(
                os.path.dirname(folder + "/")) + ".tsv")

            # TODO: Oppdatere tsv først med hva som skal bli og så loope gjennom og så sjekke på disk?
            # TODO: Bruk for å legge til rette extension på .data-filer? https://github.com/timothyryanwalsh/addext
            # WAIT: Test denne for filer Tika ikke tar? https://github.com/h2non/filetype.py/blob/master/README.rst
            # TODO: Generer DDL for "header_file" -> må først legge til kode for fjerning av flere kolonner
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
            if 'normalized_relative_path' not in df:
                df['normalized_relative_path'] = 'Not processed'

            pd_line_count = len(df)
            print(pd_line_count)
            # TODO: Teller line_count med header -> sjekk manuelt at stemmer
            os_line_count = sum(
                [len(files) for r, d, files in os.walk(folder)])

            if os_line_count > pd_line_count:
                print("Filreferanser mangler i tsv")
                # TODO: Endre i melding med appjar på engelsk -> stop prosess
                # TODO: Også finnes hvilken som mangler?

            df.tika_batch_fs_relative_path = df.tika_batch_fs_relative_path.fillna(
                'embedded file')

            # TODO: For BIR trenger vi også disse typene (mulig at noen av de bare embedded):
            # text/plain, image/png, image/jpeg, application/x-msdownload,
            # application/vnd.wordperfect, application/vnd.ms-excel, application/pdf, application/msword,
            # application/rtf, application/vnd.ms-project, application/x-tika-msoffice, image/emf,
            # image/gif, text/html, image/unknown, image/wmf

            # TODO: Utflating av mappestruktur:
            # * https://stackoverflow.com/questions/17547273/flatten-complex-directory-structure-in-python
            # * https://stackoverflow.com/questions/19777292/recursively-copy-and-flatten-a-directory-with-python
            # * https://stackoverflow.com/questions/18383384/python-copy-files-to-a-new-directory-and-rename-if-file-name-already-exists

            # -> fjerne kolonner: https://nitratine.net/blog/post/remove-columns-in-a-csv-file-with-python/

            # TODO: Verifisere pdf/a:
            # * verapdf (i gammelt arkimintscript?)
            # * sally(https://github.com/CDSP/sallypy)
            # * jhove(https://github.com/AndreasPetter/PDF2PDFa/blob/master/de/pettersystems/pdf2pdfa/pdf2pdfa.py)
            row_iterator = df.iterrows()
            df['next_file_rel_path'] = df['tika_batch_fs_relative_path'].shift(
                1)
            for index, row in row_iterator:
                file_rel_path = str(row['tika_batch_fs_relative_path'])
                if (file_rel_path != 'embedded file'):
                    file_full_path = folder + '/' + file_rel_path

                    # print(str(index + 2), path)  # index +2 så ihht exel/libre
                    # TODO: Sjekk først at antall linjer stemmer med antall filer på disk -> dialog hvis ikke
                    # TODO: Må ha sjekk på encoding og endre ved behov for de som ikke kan vises i ff (av rent tekst som ikke er html)
                    file_type = str(row['Content_Type'])
                    if file_type == 'application/pdf':
                        # TODO: Sjekke føst om allerede er pdf/a -> se lenker over
                        file_convert(file_full_path, file_type, None, 'pdf')
                    elif file_type in ('image/tiff', 'image/jpeg'):
                        file_convert(file_full_path, file_type, 'pdf', 'pdf')
                        # TODO: Oppdatere tsv her eller i funksjon?
                    elif file_type == 'image/png':
                        file_convert(file_full_path, file_type, None, 'png')
                    elif file_type in ('text/plain; charset=ISO-8859-1',
                                       'text/plain; charset=UTF-8'):
                        file_convert(file_full_path, file_type, None, 'txt')
                    elif file_type == 'image/gif':
                        file_convert(file_full_path, file_type, None, 'png')
                    elif file_type in (
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ):
                        next_file_rel_path = str(row['next_file_rel_path'])
                        if (next_file_rel_path == 'embedded file'):
                            file_convert(file_full_path, file_type, None,
                                         'pdf')
                        else:
                            file_convert(file_full_path, file_type, 'html',
                                         'pdf')
                    elif file_type.startswith('text/html'):
                        file_convert(file_full_path, file_type, 'pdf', 'pdf')
                    elif file_type in ('application/msword',
                                       'application/rtf'):
                        file_convert(file_full_path, file_type, None, 'pdf')
                    elif file_type in ('application/x-tika-msoffice'):
                        # TODO: Er dette alltid Thumbs.db ?
                        print("office")
                    else:
                        print(file_type)
