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

import subprocess, os, pathlib, glob, sys, fileinput, copy, collections
if os.name == "posix":
    from lxml import etree as ET
    import pandas as pd

from functools import reduce
from configparser import SafeConfigParser
from verify_make_copies import add_wim_file
from extract_user_input import add_config_section
from appJar import gui
from process_files_pre import mount_wim, quit
from lxml import etree
from toposort import toposort, toposort_flatten

# TODO: Endre så en logg pr subsystem heller


def toposort2(data):
    """Dependencies are expressed as a dictionary whose keys are items
and whose values are a set of dependent items. Output is a list of
sets in topological order. The first set consists of items with no
dependences, each subsequent set consists of items that depend upon
items in the preceeding sets.

>>> print '\\n'.join(repr(sorted(x)) for x in toposort2({
...     2: set([11]),
...     9: set([11,8]),
...     10: set([11,3]),
...     11: set([7,5]),
...     8: set([7,3]),
...     }) )
[3, 5, 7]
[8, 11]
[2, 9, 10]

"""

    # Ignore self dependencies.
    for k, v in data.items():
        v.discard(k)
    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.itervalues()) - set(
        data.iterkeys())
    # Add empty dependences where needed
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item, dep in data.iteritems() if not dep)
        if not ordered:
            break
        yield ordered
        data = {
            item: (dep - ordered)
            for item, dep in data.iteritems() if item not in ordered
        }
    assert not data, "Cyclic dependencies exist among these items:\n%s" % '\n'.join(
        repr(x) for x in data.iteritems())


# def sortchildrenby(parent, attr):
#     parent[:] = sorted(parent, key=lambda child: child.get(attr))

# def dependency_order(dep_list):
#     rem_tables = list(set([t[0] for t in dep_list] + [t[1] for t in dep_list]))
#     rem_dep = copy.copy(dep_list)
#     sortkey = 1
#     ret_list = []
#     while len(rem_dep) > 0:
#         tbls = [
#             tbl for tbl in rem_tables
#             if tbl not in [dep[0] for dep in rem_dep]
#         ]
#         ret_list.extend([(tb, sortkey) for tb in tbls])
#         rem_tables = [tbl for tbl in rem_tables if tbl not in tbls]
#         rem_dep = [dep for dep in rem_dep if dep[1] not in tbls]
#         sortkey += 1
#     if len(rem_tables) > 0:
#         ret_list.extend([(tb, sortkey) for tb in rem_tables])
#     ret_list.sort(cmp=lambda x, y: cmp(x[1], y[1]))
#     return [item[0] for item in ret_list]


# TODO: Denne ikke god nok -> får flere med samme -> eller er feil lenger nede når flere constraints pr tabell?
def tsort(pairs):
    """topological sort

    Just like unix tsort(1)

    >>> tsort([(1, 2), (7, 8), (8, 10), (7, 4), (2, 3), (4, 10)])
    [1, 7, 2, 8, 4, 3, 10]
    >>> try:
    ...     tsort([(1,2), (2,1)])
    ... except CycleError as e:
    ...     print(e)
    ([], Counter({1: 1, 2: 1}), {1: [2], 2: [1]})
    """
    # inspired by http://mail.python.org/pipermail/python-list/1999-July/002831.html
    successors = {}
    predecessor_counts = collections.Counter()
    for x, y in pairs:
        successors.setdefault(x, []).append(y)
        predecessor_counts.setdefault(x, 0)
        predecessor_counts[y] += 1
    ordered = [x for x in predecessor_counts if predecessor_counts[x] == 0]
    for x in ordered:
        del predecessor_counts[x]
        for y in successors.get(x, ()):
            predecessor_counts[y] -= 1
            if predecessor_counts[y] == 0:
                ordered.append(y)
    # if predecessor_counts:
    #     raise CycleError(ordered, predecessor_counts, successors)
    return ordered


def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b:
            break
        yield b


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


config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
sql_file = tmp_dir + "/meta_process.sql"

# TODO: Legg også inn sjekk på at mappen ~/.arkimint/ finnes. Flere steder?
if os.name != "posix":
    app = gui(useTtk=True)
    app.setLocation("CENTER")
    app.setTtkTheme("winnative")
    app.errorBox("Error", "Only supported on Arkimint")
    quit(conf_file)

filepath = add_wim_file(data_dir)

if filepath:
    add_config_section(config, 'ENV')
    config.set('ENV', 'wim_path', filepath)
    config.set('ENV', 'log_file', "system_process_metadata.log")
    config.set('ENV', 'process', "meta")
    with open(conf_file, "w+") as configfile:
        config.write(configfile, space_around_delimiters=False)
else:
    quit(conf_file)

sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = data_dir + "/" + sys_name + "_mount"

open(tmp_dir + "/PWB.log", 'w').close()  # Clear log file
mount_wim(filepath, mount_dir)
open(sql_file, 'w').close()  # Blank out between runs

# TODO: Prøv å endre loop-in-loop til noe som det under:
# Også 'continue' for å begrense indentering
# def process_item(item):
#     # setups
#     # condition
#     # processing
#     # calculation
#     return result

# results = [process_item(item) for item in item_list]

# WAIT: Sjekk også datatype med pandas og legg til som tag når numerisk: https://stackoverflow.com/questions/22697773/how-to-check-the-dtype-of-a-column-in-python-pandas/22697903
sub_systems_path = mount_dir + "/content/sub_systems/"
subfolders = os.listdir(sub_systems_path)
for folder in subfolders:
    # Fix xml:
    # WAIT: Legg inn endring av alle tabell -og feltnavn til lower-case (ser at xsl gjør det -> nok?)
    base_path = sub_systems_path + folder
    ddl_file = base_path + "/documentation/metadata.sql"
    header_xml_file = base_path + "/header/metadata.xml"
    mod_xml_file = base_path + "/documentation/metadata_mod.xml"
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path),
                                  folder)) and os.path.isfile(header_xml_file):
        # TODO: Sjekk nederste svar her (sammenlign med kode under): https://stackoverflow.com/questions/23921485/update-an-xml-document-using-python-or-a-shell-script
        # TODO: ----> se også på den ift kode for å kassere tabeller
        tree = ET.parse(header_xml_file)
        p_key = tree.findall(
            "table-def/column-def[primary-key='true'][java-sql-type-name='VARCHAR']"
        )
        for child in p_key:
            name = child.find("column-name")
            size = child.find("dbms-data-size")
            dbms_type = child.find("dbms-data-type")
            if int(size.text) > 768:
                dbms_type.text = dbms_type.text.replace(size.text, "768")
                size.text = "768"
        for child in p_key:
            name = child.find("column-name")
            size = child.find("dbms-data-size")
            dbms_type = child.find("dbms-data-type")
            if int(size.text) > 768:
                dbms_type.text = dbms_type.text.replace(size.text, "768")
                size.text = "768"

        empty_tables = []
        illegal_tables = {'WINDOW': 'WINDOW_'}
        illegal_columns = {
            'STORED': 'STORED_',
            'FUNCTION': 'FUNCTION_',
            'SCHEMA': 'SCHEMA_',
            'SYSTEM': 'SYSTEM_',
            'NOTNULL': 'NOTNULL_',
            'COLUMN': 'COLUMN_',
            'PERCENT': 'PERCENT_',
            'DATE': 'DATE_',
            'PUBLIC': 'PUBLIC_',
            'OVER': 'OVER_',
            'SQL': 'SQL_',
            'INTERVAL': 'INTERVAL_'
        }
        t_count = 0
        c_count = 0
        table_def = tree.findall("table-def")
        for table in table_def:
            table_name = table.find("table-name")
            file_name = base_path + "/content/data/" + table_name.text.lower(
            ) + ".txt"
            # TODO: Menyvalg for dispose bare må rename txt-fil
            # TODO: Brukes denne lenger? Eller blir fil bare slettet nå?
            # TODO: Må dette gjøres senere så håndterer at gjør disposed i etterkant av at endret ext til tsv ?
            # TODO: ---> eller heller skrive til xml-fil at disposed? --> Holder å bare slette tsv. Også før endre ext?
            disposed_file_name = base_path + "/content/data/" + table_name.text.lower() + \
                "__disposed.txt"
            # Add tables names too long for oracle to 'illegal_tables'
            if len(table_name.text
                   ) > 30 and table_name.text not in illegal_tables:
                t_count += 1
                illegal_tables[table_name.text] = table_name.text[:25] + \
                    "_" + str(t_count) + "_"

            # Rename illegal tablenames in XML:
            old_table_name = ET.Element("original-table-name")
            old_table_name.text = table_name.text

            if table_name.text in illegal_tables:
                table_name.text = illegal_tables[table_name.text]
            table_name.text = table_name.text.lower()
            table.insert(3, old_table_name)

            # Rename tsv-files except when disposed:
            new_file_name = (
                base_path + "/content/data/" + table_name.text + ".tsv")

            if os.path.isfile(file_name):
                os.rename(file_name, new_file_name)
            elif os.path.isfile(disposed_file_name):
                os.remove(disposed_file_name)

            # Add row-count/disposed-info:
            # TODO: Blir feil med row-count når kjører denne koden flere ganger? (n/a heller enn 0)
            disposed = ET.Element("disposed")
            disposed.text = "false"
            disposal_comment = ET.Element("disposal_comment")
            disposal_comment.text = " "
            rows = ET.Element("rows")
            row_count = 0
            # TODO: Legg inn sjekk så ikke leser rader på nytt hvis gjort før
            if os.path.exists(new_file_name):
                with open(
                        new_file_name, "r", encoding="utf-8",
                        errors='ignore') as f:
                    row_count = sum(bl.count("\n") for bl in blocks(f)) - 1
                if row_count == 0:
                    os.remove(new_file_name)
                    disposed.text = "true"
                    disposal_comment.text = "Empty table"
                    empty_tables.append(table_name.text)
                rows.text = str(row_count)
            else:
                disposed.text = "true"
                disposal_comment.text = "No archival value"
                empty_tables.append(table_name.text)
                rows.text = "n/a"

            table.insert(5, rows)
            table.insert(6, disposed)
            table.insert(7, disposal_comment)

            # Add column names too long for oracle to 'illegal_columns'
            for column_def in table.getchildren():
                if column_def.tag == "column-def":
                    for column in column_def:
                        if column.tag == "column-name":
                            col_length = len(column.text)
                            if col_length > 30 and column.text not in illegal_columns:
                                c_count += 1
                                illegal_columns[column.text] = column.text[:26] + \
                                    "_" + str(c_count)

        # TODO: Mulig senere å kutte ut en egen loop for dette?
        deps_dict = {}

        deps_list = []  # TESTKODE
        # deps_list.append(['no_dependencies', 'test'])
        table_list = []
        for table in table_def:
            dep_count = 0
            table_name = table.find("table-name")
            # table_list.append(table_name.text.lower())
            children = table.getchildren()
            # table_deps = []
            table_deps = set()
            for column_def in children:
                if column_def.tag == "foreign-keys":
                    for fkey_def in column_def:
                        if fkey_def.tag == "foreign-key":
                            for fkey in fkey_def:
                                if fkey.tag == "constraint-name":
                                    c_name = str(fkey.text).lower()
                                    # Ignore Oracle check constraints
                                    if c_name.startswith("sys_c"):
                                        break
                                if fkey.tag == "references":
                                    for fkey_ref in fkey:
                                        if fkey_ref.tag == "table-name":
                                            ref_table = fkey_ref.text.lower()
                                            # if ref_table != table_name.text:  # TESTKODE
                                            #     dep_count += 1
                                            #     deps_list.append([
                                            #         table_name.text.lower(),
                                            #         ref_table
                                            #     ])

                                            if ref_table not in table_deps and ref_table != table_name.text:
                                                table_deps.add(ref_table)
                                                # table_deps.append(ref_table)

            # TODO: Trengs denne og håndterer toposort den? Tom verdi heller?
            if len(table_deps) == 0:
                table_deps.add(table_name.text)
            # if table_deps == []:
            #     table_deps.append("")
            # if dep_count == 0:
            # deps_list.append([table_name.text.lower(), 'no_dependencies'])

            deps_dict.update({table_name.text: table_deps})

        # deps_list = tsort(deps_list)
        # deps_list = deps_list[::-1]

        # for i in deps_dict:
        #     print(i, deps_dict[i])

        # Order tables by dependencies
        # deps_list = flatten(deps_dict)  #Order according to deps

        # deps_set = toposort2(deps_dict)

        # print(deps_set)
        # deps_list = list(deps_set)

        # deps_list = dependency_order(deps_list)
        # dep_tree = DepenendcieTree()
        # dep_tree.add_proj_list(table_list)
        # dep_tree.add_depenendcie_list(deps_list)
        # print(dep_tree.list())
        # deps_list = dep_tree.list()

        # deps_list = DepenOrder(table_list, deps_list)

        # TODO: Legg til toposort pip linje i arkimint hvis ender opp med å bruke den
        deps_list = toposort_flatten(deps_dict)
        # deps_list = toposort_flatten(deps_dict)

        # print(*testlist, sep="\n")
        # print(*deps_list, sep="\n")
        for table in table_def:
            table_name = table.find("table-name")
            index = 0
            if table_name.text in deps_list:
                index = int(deps_list.index(table_name.text))

            children = table.getchildren()
            dep_position = ET.Element("dep-position")
            dep_position.text = str(index + 1)
            table.insert(6, dep_position)
            i = 0
            # Rename illegal column names in XML:
            for column_def in children:
                if column_def.tag == "column-def":
                    for column in column_def:
                        if column.tag == "column-name":
                            if column.text in illegal_columns:
                                old_column_name = ET.Element(
                                    "original-column-name")

                                old_column_name.text = column.text
                                column.text = illegal_columns[column.text]
                                column_def.insert(2, old_column_name)
                                # Update tsv-file:
                                new_file_name = base_path + "/content/data/" + table_name.text + ".tsv"
                                if os.path.isfile(new_file_name):
                                    df = pd.read_csv(
                                        new_file_name,
                                        sep="\t",
                                        low_memory=False)
                                    df.rename(
                                        columns={
                                            old_column_name.text:
                                            column.text.lower(),
                                            old_column_name.text.lower():
                                            column.text.lower()
                                        },  # For reruns
                                        inplace=True,
                                    )
                                    df.to_csv(
                                        new_file_name, index=False, sep="\t")
                        # TODO: Fix feil med bigint:
                        # -> virket når jeg gjorde felt til "numeric" -> fiks i xsl -> se linje 663
                        # -> se også her: https://www.w3resource.com/sql/data-type.php#NUMERIC
                        # if column.tag == "dbms-data-type":
                        # if column.text
                        # size = child.find("dbms-data-size")
                        # dbms_type = child.find("dbms-data-type")
                        if column.tag == "references":
                            for ref in column:
                                if ref.tag == "column-name":
                                    if ref.text in illegal_columns:
                                        old_column_ref = ET.Element(
                                            "original-column-name")
                                        old_column_ref.text = ref.text
                                        # ref.text = ref.text + "_"
                                        ref.text = illegal_columns[ref.text]
                                        column.insert(3, old_column_ref)
                                if ref.tag == "table-name":
                                    if ref.text.lower() in empty_tables:
                                        column_def.remove(column)

                                    if ref.text in illegal_tables:
                                        old_table_ref = ET.Element(
                                            "original-table-name")
                                        old_table_ref.text = ref.text
                                        ref.text = illegal_tables[ref.text]
                                        column.insert(3, old_table_ref)
                                # if ref.tag == "deferrable":
                                # column.remove(ref)
                if column_def.tag == "index-def":
                    for index in column_def:
                        if index.tag == "column-list":
                            for ref in index:
                                if ref.attrib["name"] in illegal_columns:
                                    # ref.attrib["name"] = ref.attrib["name"] + "_"
                                    ref.attrib["name"] = illegal_columns[
                                        ref.attrib["name"]]
                                    # TODO: Legge inn old_name også her?
                if column_def.tag == "foreign-keys":
                    for fkey_def in column_def:
                        # disposed.text = "false"
                        # disposal_comment.text = " "
                        if fkey_def.tag == "foreign-key":
                            for fkey in fkey_def:
                                # ora_check_constraint = False
                                # if fkey.tag == "constraint-name":
                                #     c_name = str(fkey.text).lower()
                                #     # Ignore Oracle check constraints
                                #     if c_name.startswith("sys_c"):
                                #         ora_check_constraint = True
                                if fkey.tag == "references":
                                    for fkey_ref in fkey:
                                        # Fix references to normalized table-names:
                                        if fkey_ref.tag == "table-name":
                                            if fkey_ref.text in illegal_tables:
                                                old_table_ref = ET.Element(
                                                    "original-table-name")
                                                old_table_ref.text = fkey_ref.text
                                                fkey_ref.text = illegal_tables[
                                                    fkey_ref.text]
                                                fkey.insert(3, old_table_ref)
                                            # Remove contraints depending on empty tables:
                                            if fkey_ref.text.lower(
                                            ) in empty_tables:
                                                column_def.remove(fkey_def)
                                                # print(fkey_ref.text.lower())
                                                # disposed.text = "true"
                                                # disposal_comment.text = "References empty table"
                                            # Remove contraints pointing to same table:
                                            # TODO: Sjekk at det faktisk er tilfelle at ikke støttes av div databaser/iso-sql

                                            if fkey_ref.text.lower(
                                            ) == table_name.text:
                                                # print(table_name.text)
                                                # TODO: Tester uten linje under -> ga feil for profdoc
                                                # column_def.remove(fkey_def)

                                                disposed.text = "true"
                                                disposal_comment.text = "Self-referencing constraint"
                                                # TODO: Bruk dispos-tag heller enn å fjerne også andre steder
                                        fkey_ref.insert(1, disposed)
                                        fkey_ref.insert(2, disposal_comment)

                                # fkey.insert(1, disposed)
                                # fkey.insert(2, disposal_comment)

                                if fkey.tag in ("source-columns",
                                                "referenced-columns"):
                                    for column in fkey:
                                        if (column.tag == "column" and
                                                column.text in illegal_columns
                                            ):
                                            old_column_ref = ET.Element(
                                                "original-column-name")
                                            old_column_ref.text = column.text
                                            # column.text = column.text + "_"
                                            column.text = illegal_columns[
                                                column.text]
                                            fkey.insert(1, old_column_ref)
                                # fkey_def.insert(1, disposed)
                                # fkey_def.insert(2, disposal_comment)

                # table-constraints (constraints of type "check")
                if column_def.tag == "table-constraints":
                    for constraint_def in column_def:
                        if constraint_def.tag == "constraint-definition":
                            for word in constraint_def.text.split():
                                word = word.replace("(", "")
                                if word in illegal_columns:
                                    constraint_def.text = constraint_def.text.replace(
                                        word, illegal_columns[word])

        root = tree.getroot()
        indent(root)
        tree.write(mod_xml_file)

        # WAIT: Justere "2html.xslt" tilsvarende til det som er gjort for "2xml" ?
        # Generate html and ddl:
        sql = [
            "\n",
            "---- Generate DDL -----",
            "WbXslt -inputfile=" + mod_xml_file,
            "-stylesheet=PWB/metadata2ddl.xslt",
            "-xsltOutput=" + ddl_file + ";",
        ]
        with open(sql_file, "a+") as file:
            file.write("\n".join(sql))
            file.close()

        # Make all tsv headers lower case
        for fname in glob.iglob(base_path + "/content/data/*.tsv"):
            with open(fname, "r+") as f:
                line = f.readline().strip()
                header = line.strip()
                f.seek(0)  # move file pointer to beginning of file
                f.write(line.replace(header, header.lower()))
