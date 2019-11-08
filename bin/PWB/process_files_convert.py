import subprocess, os, shutil, argparse, sys, signal
import pathlib
import pandas as pd
from pathlib import Path
from configparser import SafeConfigParser
from pgmagick.api import Image
from pdfy import Pdfy
from extract_user_input import add_config_section

config = SafeConfigParser()
pwb_dir = os.path.dirname(__file__)
corrupt_file_pdf = pwb_dir + '/corrupt_file_nb.pdf'
tmp_dir = os.path.abspath(os.path.join(pwb_dir, '..', 'tmp'))
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

# TODO: Juster kode under så returnerer mer dos, unix mm heller for
# newline = None
# eol = get_newline(file_full_path)
# if eol == '\n': newline = 'unix'
# elif eol == '\r\n': newline = 'dos'
# elif eol == '+r': newline = 'mac'

# # print(repr(eol))


def get_newline(filename):
    with open(filename, "rb") as f:
        while True:
            c = f.read(1)
            if not c or c == b'\n':
                break
            if c == b'\r':
                if f.read(1) == b'\n':
                    return '\r\n'
                return '\r'
    return '\n'


def kill(proc_id):
    os.kill(proc_id, signal.SIGINT)


def run_shell_command(command, cwd=None, timeout=30):
    # ok = False
    os.environ['PYTHONUNBUFFERED'] = "1"
    cmd = [' '.join(command)]
    stdout = []
    stderr = []
    mix = []

    print(''.join(cmd))
    sys.stdout.flush()

    proc = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill(proc.pid)

    # while proc.poll() is None:
    #     line = proc.stdout.readline()
    #     if line != "":
    #         stdout.append(line)
    #         mix.append(line)
    #         print(line, end='')

    #     line = proc.stderr.readline()
    #     if line != "":
    #         stderr.append(line)
    #         mix.append(line)
    #         print(line, end='')

    for line in proc.stdout:
        stdout.append(line.rstrip())

    return proc.returncode, stdout, stderr, mix


def file_copy(src, dst):
    print('cp ' + src + ' ' + dst)
    sys.stdout.flush()

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
    print('image2norm(python) ' + image_path + ' ' + norm_path)
    sys.stdout.flush()

    ok = False
    try:
        img = Image(image_path)
        img.write(norm_path)
        ok = True
    except Exception as e:
        print(e)
        ok = False
    return ok


def docbuilder2x(file_path, tmp_path, format, file_type):
    ok = False
    docbuilder_file = tmp_dir + "/x2x.docbuilder"
    docbuilder = None

    # TODO: Annet for rtf?
    if file_type in ('application/msword', 'application/rtf'):
        docbuilder = [
            'builder.OpenFile("' + file_path + '", "");',
            'builder.SaveFile("' + format + '", "' + tmp_path + '");',
            'builder.CloseFile();',
        ]
    elif file_type in (
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ):
        docbuilder = [
            'builder.OpenFile("' + file_path + '", "");',
            'var ws;',
            'var sheets = Api.GetSheets();',
            'var arrayLength = sheets.length;',
            'for (var i = 0; i < arrayLength; i++) {ws = sheets[i];ws.SetPageOrientation("xlLandscape");}',
            'builder.SaveFile("' + format + '", "' + tmp_path + '");',
            'builder.CloseFile();',
        ]

    with open(docbuilder_file, "w+") as file:
        file.write("\n".join(docbuilder))

    command = ['documentbuilder', docbuilder_file]
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


def abi2x(file_path, tmp_path, format, file_type):
    ok = False
    command = ['abiword', '--to=' + format]

    if file_type == 'application/rtf':
        command.append('--import-extension=rtf')

    command.extend(['-o', tmp_path, file_path])
    run_shell_command(command)

    if os.path.exists(tmp_path):
        ok = True

    return ok


# WAIT: Test denne: https://github.com/xrmx/pylokit
# TODO: Legg inn en killall soffice.bin når tar for lang tid
def unoconv2x(file_path, norm_path, format, file_type):
    ok = False
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
        elif format == 'html':
            command.extend(
                ['-d', 'spreadsheet', '-P', 'PaperOrientation=landscape'])
    elif file_type in ('application/msword', 'application/rtf'):
        command.extend(['-d', 'document', '-eSelectPdfVersion=1'])

    command.extend(['-o', norm_path, file_path])
    run_shell_command(command)

    if os.path.exists(norm_path):
        ok = True

    return ok


# --> return ok= False bare da
# WAIT: Se for flere gs argumenter: https://superuser.com/questions/360216/use-ghostscript-but-tell-it-to-not-reprocess-images
def pdf2pdfa(pdf_path, pdfa_path):
    # because of a ghostscript bug, which does not allow parameters that are longer than 255 characters
    # we need to perform a directory changes, before we can actually return from the method
    ok = False

    # TODO: Test om det er noen av valgene under som førte til stooore filer (dEncode-valgene)
    if os.path.exists(pdf_path):
        cwd = os.getcwd()
        os.chdir(os.path.dirname(pdfa_path))
        ghostScriptExec = [
            'gs', '-dPDFA', '-dBATCH', '-dNOPAUSE',
            '-sProcessColorModel=DeviceRGB', '-sDEVICE=pdfwrite', '-dSAFER',
            '-sColorConversionStrategy=UseDeviceIndependentColor',
            '-dEmbedAllFonts=true', '-dPrinted=true',
            '-dPDFACompatibilityPolicy=1', '-dDetectDuplicateImages', '-r150',
            '-dFastWebView=true'
            # '-dColorConversionStrategy=/LeaveColorUnchanged',
            # '-dEncodeColorImages=false', '-dEncodeGrayImages=false',
            # '-dEncodeMonoImages=false', '-dPDFACompatibilityPolicy=1'
        ]

        command = ghostScriptExec + [
            '-sOutputFile=' + os.path.basename(pdfa_path), pdf_path
        ]
        run_shell_command(command)
        os.chdir(cwd)

    if os.path.exists(pdfa_path):
        ok = True

    return ok


# WAIT: Brukes for annet enn html? Støtter alt chrome kan lese
def html2pdf(file_path, tmp_path):
    print('image2norm(python) ' + file_path + ' ' + tmp_path)
    sys.stdout.flush()

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
    normalized_file = 0  # Not converted
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
        # print('Processing ' + norm_file_full_path) #TODO: Vises ikke i wb output
        norm_ok = False
        tmp_ok = False
        if (not os.path.isfile(tmp_file_full_path) or tmp_ext == None):
            if file_type in ('image/tiff', 'image/jpeg'):
                tmp_ok = image2norm(file_full_path, tmp_file_full_path)
            elif file_type == 'image/gif':
                norm_ok = image2norm(file_full_path, norm_file_full_path)
            elif file_type == 'application/pdf':
                norm_ok = pdf2pdfa(file_full_path, norm_file_full_path)
            elif file_type in ('image/png', 'text/plain; charset=ISO-8859-1',
                               'text/plain; charset=UTF-8'):
                norm_ok = file_copy(file_full_path, norm_file_full_path)
                # TODO: Bruk get_newline og legg inn endring til unix hvis er på dos eller mac
            elif file_type in (
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ):
                if tmp_ext == None:
                    norm_ok = unoconv2x(file_full_path, norm_file_full_path,
                                        'pdf', file_type)
                else:
                    tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,
                                          'pdf', file_type)
                # tmp_exists = unoconv2x(file_full_path, tmp_file_full_path,
                #                        'html', file_type)
            elif file_type.startswith('text/html'):
                tmp_ok = html2pdf(file_full_path, tmp_file_full_path)
            # elif file_type in ('application/msword', 'application/rtf'):
            elif file_type == 'application/msword':
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,'pdf', file_type)
                norm_ok = unoconv2x(file_full_path, norm_file_full_path, 'pdf',
                                    file_type)
            elif file_type == 'application/rtf':
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,
                #                       'pdf', file_type)
                tmp_ok = abi2x(file_full_path, tmp_file_full_path, 'pdf',
                               file_type)
        if tmp_ok:
            if tmp_ext == 'pdf':
                norm_ok = pdf2pdfa(tmp_file_full_path, norm_file_full_path)
            elif tmp_ext == 'html':
                norm_ok = unoconv2x(tmp_file_full_path, norm_file_full_path,
                                    'pdf', file_type)
        elif os.path.exists(tmp_file_full_path):
            os.remove(tmp_file_full_path)

        if norm_ok and tmp_ok:
            os.remove(tmp_file_full_path)
        # TODO: Legg inn hvilken originalfiler som skal slettes

        if os.path.isfile(norm_file_full_path):
            normalized_file = 1  # Converted now
    else:
        normalized_file = 2  # Converted earlier

    return normalized_file, norm_file_full_path


if not os.path.isfile(convert_done_file):
    conversion_failed = []
    conversion_not_supported = []
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

            df = pd.read_csv(header_file, sep="\t", low_memory=False)
            if 'normalized_relative_path' not in df:
                df['normalized_relative_path'] = 'na'

            if 'normalization' not in df:
                df['normalization'] = 'not processed'

            df.tika_batch_fs_relative_path = df.tika_batch_fs_relative_path.fillna(
                'embedded file')

            file_rows = df.apply(
                lambda x: True if x['tika_batch_fs_relative_path'] != 'embedded file' else False,
                axis=1)
            pd_line_count = len(file_rows[file_rows == True].index)

            os_line_count = sum(
                [len(files) for r, d, files in os.walk(folder)])

            # TODO: Endre i melding med appjar på engelsk -> stop prosess
            if os_line_count == pd_line_count:
                print("*** Files listed in '" + header_file +
                      "' matches files on disk. *** \n")
            else:
                print("*** Files listed in '" + header_file +
                      "' doesn't match files on disk. *** \n")

            sys.stdout.flush()

            # TODO: Oppdater i tsv når konvertering feiler - returner ok også på de som er konvertert tidligere

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

            # TODO: Legg inn telleverk i konvertering -> noe sånt: (1/538)

            row_iterator = df.iterrows()
            df['next_file_rel_path'] = df['tika_batch_fs_relative_path'].shift(
                -1)
            for index, row in row_iterator:
                file_rel_path = str(row['tika_batch_fs_relative_path'])
                # TODO: Sjekk tika kolonne om PDF/a allerede
                if (file_rel_path != 'embedded file'):
                    file_full_path = folder + '/' + file_rel_path
                    normalized = (3, "")
                    norm_ext = None

                    # TODO: Må ha sjekk på encoding og endre ved behov for de som ikke kan vises i ff (av rent tekst som ikke er html)
                    file_type = str(row['Content_Type'])
                    if file_type == 'application/pdf':
                        # TODO: Sjekke føst om allerede er pdf/a? -> se lenker over
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext)
                    elif file_type in ('image/tiff', 'image/jpeg'):
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext)
                        # TODO: Oppdatere tsv her eller i funksjon?
                    elif file_type == 'image/png':
                        norm_ext = 'png'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext)
                    elif file_type in ('text/plain; charset=ISO-8859-1',
                                       'text/plain; charset=UTF-8'):
                        norm_ext = 'txt'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext)
                        # TODO: Legg inn endring av encoding hvis ikke av godkjent type
                    elif file_type == 'image/gif':
                        norm_ext = 'png'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext)
                    elif file_type in (
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ):
                        norm_ext = 'pdf'
                        next_file_rel_path = str(row['next_file_rel_path'])
                        if (next_file_rel_path == 'embedded file'):
                            normalized = file_convert(
                                file_full_path, file_type, None, norm_ext)
                        else:
                            normalized = file_convert(
                                file_full_path, file_type, 'pdf', norm_ext)
                            # normalized_file = file_convert(
                            #     file_full_path, file_type, 'html', 'pdf')
                    elif file_type.startswith('text/html'):
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext)
                    elif file_type == 'application/msword':
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext)
                    elif file_type == 'application/rtf':
                        # WAIT: Helst med abiword bare hvis de andre ikke klarer det? -> Mulig docbuilder enda bedre enn abi
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', 'pdf')
                    # elif file_type in ('application/x-tika-msoffice'):
                    #     # TODO: Er dette alltid Thumbs.db ?
                    #     print("office")
                    else:
                        conversion_not_supported.append(
                            file_full_path + ' (' + file_type + ')')
                        df.loc[index, 'normalization'] = "Format not supported"

                    if normalized[0] in (0, 1):  # Not processed on earlier run
                        norm_ok = True
                        norm_rel_path = Path(
                            normalized[1]).relative_to(folder + '_normalized/')
                        df.loc[index,
                               'normalized_relative_path'] = norm_rel_path

                        if normalized[0] == 0:  # Corrupt file
                            norm_ok = False
                        elif normalized[0] == 1:  # Converted now
                            if norm_ext == 'pdf':  # WAIT: Legg inn sjekk for andre arkivformat? Bruke mediaconch?
                                command = [
                                    'verapdf.sh', '--format', 'text',
                                    normalized[1]
                                ]
                                result = run_shell_command(command)
                                stdout = ''.join(result[1])
                                if "does not appear to be a valid PDF file and could not be parsed" in stdout:
                                    norm_ok = False

                        if norm_ok:
                            df.loc[index, 'normalization'] = "Ok"
                        else:
                            conversion_failed.append(
                                file_full_path + ' (' + file_type + ')')
                            file_copy(corrupt_file_pdf, normalized[1])
                            df.loc[index, 'normalization'] = "Failed"

            df.to_csv(header_file, index=False, sep="\t")

            if len(conversion_failed) > 0:
                print("\n")
                print("*** Files not converted (conversion failed) ***")
                print(*conversion_failed, sep="\n")
                print("\n")

            if len(conversion_not_supported) > 0:
                print("*** Files not converted (conversion not supported) ***")
                print(*conversion_not_supported, sep="\n")
                print("\n")

            if len(conversion_failed) == 0 and len(
                    conversion_not_supported) == 0:
                print('*** All files converted successfully. *** \n')

            not_converted = len(conversion_failed) + len(
                conversion_not_supported)
            if not_converted > 0:
                add_config_section(config, 'ENV')
                config.set('ENV', 'wim_path', "")
                with open(conf_file, "w+") as configfile:
                    config.write(configfile, space_around_delimiters=False)
