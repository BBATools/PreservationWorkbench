import subprocess, os, shutil, argparse, sys, signal, zipfile, re, glob
import pathlib
import pandas as pd
from pathlib import Path
from configparser import SafeConfigParser
from pgmagick.api import Image
from pdfy import Pdfy
from extract_user_input import add_config_section
from functools import reduce

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

# elif file_type in ('text/plain; charset=windows-1252',
#                     'text/plain; charset=ISO-8859-1',
#                     'text/plain; charset=UTF-8', 'application/xml'):


def x2utf8(file_path, norm_path, tmp_path, file_type):
    ok = False

    if file_type in ('text/plain; charset=windows-1252',
                     'text/plain; charset=ISO-8859-1'):
        # WAIT: Juster så mindre repetisjon under
        if file_type == 'text/plain; charset=windows-1252':
            command = ['iconv', '-f', 'windows-1252']
        elif file_type == 'text/plain; charset=ISO-8859-1':
            command = ['iconv', '-f', 'ISO-8859-1']

        command.extend(['-t', 'UTF8', file_path, '-o', tmp_path])
        run_shell_command(command)
    else:
        file_copy(file_path, tmp_path)

    if os.path.exists(tmp_path):
        repls = (
            ('‘', 'æ'),
            ('›', 'ø'),
            ('†', 'å'),
        )

        # WAIT: Legg inn validering av utf8 -> https://pypi.org/project/validate-utf8/
        file = open(norm_path, "w")
        with open(tmp_path, 'r') as file_r:
            for line in file_r:
                file.write(reduce(lambda a, kv: a.replace(*kv), repls, line))

        if os.path.exists(norm_path):
            ok = True

    return ok


def extract_nested_zip(zippedFile, toFolder):
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
    """
    # pathlib.Path(toFolder).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zippedFile, 'r') as zfile:
        zfile.extractall(path=toFolder)
    os.remove(zippedFile)
    for root, dirs, files in os.walk(toFolder):
        for filename in files:
            if re.search(r'\.zip$', filename):
                fileSpec = os.path.join(root, filename)
                extract_nested_zip(fileSpec, root)


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

    for line in proc.stderr:
        stderr.append(line.rstrip())

    # print(stderr)
    return proc.returncode, stdout, stderr, mix


def file_copy(src, dst):
    print('cp ' + src + ' ' + dst)
    sys.stdout.flush()

    ok = False
    try:
        # if os.path.isdir(dst):
        #     dst = os.path.join(dst, os.path.basename(src))
        shutil.copyfile(src, dst)
    except Exception as e:
        print(e)
        ok = False
    return ok


# TODO: Stopper opp med Exit code: 137 noen ganger -> fiks
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
    if file_type in (
            'application/msword', 'application/rtf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ):
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


def wkhtmltopdf(file_path, tmp_path):
    ok = False
    command = ['wkhtmltopdf', '-O', 'Landscape', file_path, tmp_path]
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


def html2pdf(file_path, tmp_path):
    print('html2pdf(python) ' + file_path + ' ' + tmp_path)
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


# file_full_path = folder + '/' + file_rel_path
# TODO: Feil at ikke file_rel_path er arg i def under
def file_convert(file_full_path, file_type, tmp_ext, norm_ext, in_zip):
    # file_full_path = folder + '/' + file_rel_path
    normalized_file = 0  # Not converted
    file_name = os.path.basename(file_full_path)
    if tmp_ext:
        tmp_file_full_path = folder + '_normalized/' + file_rel_path + '.tmp.' + tmp_ext
    else:
        tmp_file_full_path = folder + '_normalized/' + file_rel_path + '.tmp.pwb'
    norm_folder_full_path = folder + '_normalized/' + os.path.dirname(
        file_rel_path)
    norm_folder_full_path = norm_folder_full_path.replace('//', '/')
    norm_file_full_path = norm_folder_full_path + '/' + os.path.splitext(
        file_name)[0] + '.norm.' + norm_ext

    # TODO: Bør heller sjekke på annet enn at fil finnes slik at evt corrupt-file kan overskrives ved nytt forsøk
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
            elif file_type in ('text/plain; charset=windows-1252',
                               'text/plain; charset=ISO-8859-1',
                               'text/plain; charset=UTF-8', 'application/xml'):
                norm_ok = x2utf8(file_full_path, norm_file_full_path,
                                 tmp_file_full_path, file_type)

            elif file_type == 'image/png':
                norm_ok = file_copy(file_full_path, norm_file_full_path)
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
                # tmp_ok = unoconv2x(file_full_path, tmp_file_full_path,
                #                        'html', file_type)
            elif file_type.startswith('text/html'):
                tmp_ok = html2pdf(file_full_path, tmp_file_full_path)
            elif file_type == 'application/xhtml+xml; charset=UTF-8':
                tmp_ok = wkhtmltopdf(file_full_path, tmp_file_full_path)
            elif file_type in (
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    'application/vnd.wordperfect'):
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,'pdf', file_type)
                norm_ok = unoconv2x(file_full_path, norm_file_full_path, 'pdf',
                                    file_type)
            elif file_type == 'application/rtf':
                # TODO: Bør først prøve med abiword og så unoconv for de den ikke klarer -> eller omvendt hvis kan forhindre heng av LO
                # tmp_ok = docbuilder2x(file_full_path, tmp_file_full_path,
                #                       'pdf', file_type)
                norm_ok = unoconv2x(file_full_path, norm_file_full_path, 'pdf',
                                    file_type)
                # tmp_ok = abi2x(file_full_path, tmp_file_full_path, 'pdf',
                #                file_type)
            elif file_type == 'application/x-msdownload':  # TODO: Trengs denne?
                norm_ok = False
            else:
                normalized_file = 3  # Conversion not supported

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

        # if os.path.isfile(norm_file_full_path):
        if glob.glob(os.path.splitext(norm_file_full_path)[0] + '.*'):
            if norm_ok:
                normalized_file = 1  # Converted now automatically
            else:
                normalized_file = 2  # Converted now manually
    else:
        normalized_file = 4  # Converted earlier

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
    ]
    for dir in sub_folders:
        doc_folders = [
            f.path for f in os.scandir(dir + "/content")
            if (f.is_dir() and f.name in ('documents', 'data_documents'))
        ]

        for folder in doc_folders:
            header_file = (dir + "/header/" + os.path.basename(
                os.path.dirname(folder + "/")) + ".tsv")

            # TODO: Oppdatere tsv først med hva som skal bli og så loope gjennom og så sjekke på disk?
            # WAIT: Test denne for filer Tika ikke tar? https://github.com/h2non/filetype.py/blob/master/README.rst, evt 'file' bare
            # TODO: Generer DDL for "header_file" -> må først legge til kode for fjerning av flere kolonner
            # TODO: Generer også (samtidig som telle antall filer) en tsv som bare inneholder viktigste kolonner
            # --> legge denne i data-mappe for import til innsyn mens den originale med alt blir liggende i header?
            # tika_file_ext er det som var på filen og sier ikke at det stemmer med formatet
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
                lambda x: True if (x['tika_batch_fs_relative_path'] != 'embedded file' and 'zip:' not in x['tika_batch_fs_relative_path']) else False,
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

            zip_row_iterator = df.iterrows()
            zip_rel_dir = None
            for index, row in zip_row_iterator:
                file_rel_path = str(row['tika_batch_fs_relative_path'])
                if file_rel_path != 'embedded file' and 'zip:' not in file_rel_path:  # TODO: Håndtere zip i zip-fil hvordan?
                    if str(row['Content_Type']) == 'application/zip':
                        zip_dir = folder + '_normalized/' + os.path.dirname(
                            file_rel_path) + '/' + os.path.splitext(
                                os.path.basename(file_rel_path))[0] + '.norm'
                        zip_rel_dir = str(
                            Path(zip_dir).relative_to(folder + '_normalized/'))

                        zippedFileTmp = "/tmp/tmp.zip"
                        file_copy(folder + '/' + file_rel_path, zippedFileTmp)
                        extract_nested_zip(zippedFileTmp, zip_dir)
                        # TODO: Oppdater i tsv for zip-linje etter unzip
                    else:
                        zip_rel_dir = None
                else:
                    if zip_rel_dir:
                        df.loc[
                            index,
                            'tika_batch_fs_relative_path'] = 'zip:' + zip_rel_dir + '/' + str(
                                row['resourceName'])

            row_iterator = df.iterrows()
            df['next_file_rel_path'] = df['tika_batch_fs_relative_path'].shift(
                -1)
            in_zip = False
            for index, row in row_iterator:
                file_rel_path = str(row['tika_batch_fs_relative_path'])
                # TODO: Sjekk tika kolonne om PDF/a allerede
                if file_rel_path != 'embedded file':
                    if 'zip:' in file_rel_path:
                        file_rel_path = file_rel_path[4:]
                        file_full_path = folder + '_normalized/' + file_rel_path
                        in_zip = True  # TODO: Legg inn sjekk på denne i file_convert(at alltid slettes etterpå)
                    else:
                        file_full_path = folder + '/' + file_rel_path

                    normalized = (
                        0,
                        "")  # WAIT: Endre slik at 0 og ikke 3 er default verdi
                    norm_ext = None
                    keep_original = False

                    file_type = str(row['Content_Type'])
                    if file_type == 'application/pdf':
                        # TODO: Sjekke føst om allerede er pdf/a? -> se lenker over
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    elif file_type in ('image/tiff', 'image/jpeg'):
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext, in_zip)
                        # TODO: Oppdatere tsv her eller i funksjon?
                    elif file_type == 'image/png':
                        norm_ext = 'png'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    elif file_type in ('text/plain; charset=ISO-8859-1',
                                       'text/plain; charset=UTF-8',
                                       'text/plain; charset=windows-1252',
                                       'application/xml'):
                        norm_ext = 'txt'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    elif file_type == 'image/gif':
                        norm_ext = 'png'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    elif file_type in (
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ):
                        norm_ext = 'pdf'
                        keep_original = True
                        next_file_rel_path = str(row['next_file_rel_path'])

                        if (next_file_rel_path == 'embedded file'):
                            normalized = file_convert(file_full_path,
                                                      file_type, None,
                                                      norm_ext, in_zip)
                        else:
                            normalized = file_convert(file_full_path,
                                                      file_type, 'pdf',
                                                      norm_ext, in_zip)
                            # normalized_file = file_convert(
                            #     file_full_path, file_type, 'html', 'pdf')
                    elif file_type.startswith('text/html'):
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext, in_zip)
                    elif file_type == 'application/xhtml+xml; charset=UTF-8':  # TODO: Slå sammen med den over?
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext, in_zip)
                    elif file_type in (
                            'application/msword',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            'application/vnd.wordperfect'):
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    elif file_type == 'application/rtf':
                        # WAIT: Abiword best å bruke først. Docbuilder klarer bare noen få ekstra som ikke abiword klarer (og sikkert en del motsatt)
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  'pdf', norm_ext, in_zip)
                    elif (file_type == 'application/x-tika-msoffice'
                          and os.path.basename(file_full_path) == 'Thumbs.db'):
                        if os.path.exists(file_full_path):
                            os.remove(file_full_path)
                        df.drop(index, inplace=True)
                    # TODO: Hvis zip, bare sjekk at pakket ut riktig og angi så som ok (husk distinksjon med zip i zip)
                    # elif file_type == 'application/zip':
                    #     normalized = file_convert(file_full_path, file_type,
                    #                               'pdf', 'pdf')

                    elif file_type == 'application/x-msdownload':
                        norm_ext = 'pdf'
                        normalized = file_convert(file_full_path, file_type,
                                                  None, norm_ext, in_zip)
                    # elif file_type == 'application/vnd.ms-project':
                    #     norm_ext = 'pdf'
                    #     normalized = file_convert(file_full_path, file_type,
                    #                               None, norm_ext, in_zip)
                    else:
                        normalized = file_convert(file_full_path, file_type,
                                                  None, 'pwb', in_zip)

                    if normalized[0] == 3:  # Conversion not supported
                        conversion_not_supported.append(
                            file_full_path + ' (' + file_type + ')')
                        df.loc[index, 'normalization'] = "Format not supported"
                        norm_ok = False

                    elif normalized[0] in (0, 1, 2):  # Not converted earlier
                        if normalized[0] == 0:  # Corrupt file
                            norm_ok = False

                        elif normalized[0] == 1:  # Converted now automatically
                            norm_ok = True
                            if norm_ext == 'pdf':  # WAIT: Legg inn sjekk for andre arkivformat? Bruke mediaconch?
                                command = [
                                    'verapdf.sh', '--format', 'text',
                                    normalized[1]
                                ]
                                result = run_shell_command(command)
                                stdout = ''.join(result[1])
                                if "does not appear to be a valid PDF file and could not be parsed" in stdout:
                                    norm_ok = False

                        elif normalized[0] == 2:  # Converted now manually
                            norm_ok = True

                        if norm_ok:
                            df.loc[index, 'normalization'] = "Ok"

                            norm_rel_path = Path(normalized[1]).relative_to(
                                folder + '_normalized/')

                        else:
                            conversion_failed.append(
                                file_full_path + ' (' + file_type + ')')

                            corrupt_norm_file = os.path.splitext(
                                normalized[1])[0] + '.pdf'
                            norm_rel_path = Path(
                                corrupt_norm_file).relative_to(
                                    folder + '_normalized/')

                            file_copy(corrupt_file_pdf, corrupt_norm_file)
                            df.loc[index, 'normalization'] = "Failed"

                        if (not norm_ok or keep_original):
                            originals = folder + '_normalized/original_documents/'
                            pathlib.Path(originals).mkdir(
                                parents=True, exist_ok=True)

                            # TODO: Håndtere navnekonflikt ved utflating best hvordan?

                            file_copy(
                                file_full_path,
                                originals + os.path.basename(file_full_path))

                        df.loc[index,
                               'normalized_relative_path'] = norm_rel_path

            df.to_csv(header_file, index=False, sep="\t")

    # TODO: Fix at ved ny kjøring så blir en informert om "all successfully" selv om feil ved forrige? (er logget riktig i kolonne 'failed)
    if len(conversion_failed) > 0:
        print("\n")
        print("*** Files not converted (conversion failed) ***")
        print(*conversion_failed, sep="\n")
        print("\n")

    if len(conversion_not_supported) > 0:
        print("\n")
        print("*** Files not converted (conversion not supported) ***")
        print(*conversion_not_supported, sep="\n")
        print("\n")

    not_converted = len(conversion_failed) + len(conversion_not_supported)
    if not_converted > 0:
        add_config_section(config, 'ENV')
        config.set('ENV', 'wim_path', "")
        with open(conf_file, "w+") as configfile:
            config.write(configfile, space_around_delimiters=False)
        print(
            '*** Verify or fix manually any non-converted files and re-run process *** \n'
        )
    else:
        print('*** All files converted successfully. *** \n')
        # TODO: Legg inn auto sletting + renaming av mapper etter at kode for kopiering av org for visse formater på plass
        # shutil.rmtree(folder)
