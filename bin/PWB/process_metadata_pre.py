#! python3

# Copyright (C) 2020 Morten Eek

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

import subprocess, os, pathlib, glob, sys, copy, collections
if os.name == "posix":
    # from lxml import etree as ET
    import xml.etree.ElementTree as ET
    import pandas as pd

from functools import reduce
from configparser import SafeConfigParser
from appJar import gui
from process_files_pre import mount_wim, quit
# from lxml import etree # TODO: Fjern fra arkimint også hvis ikke trengs andre steder lenger heller
from toposort import toposort, toposort_flatten
from tempfile import NamedTemporaryFile
import shutil
import csv
import petl as etl
from process_files_pre import indent
from common.gui import pwb_add_wim_file
from common.dialog import pwb_yes_no_prompt
from common.dictionary import pwb_lower_dict
from common.file import pwb_replace_in_file
from common.config import pwb_add_config_section
from common.petl import pwb_lower_case_header

csv.field_size_limit(sys.maxsize)

# TODO: Se for mapping mellom navn og nummer for jdbc typer: http://www.docjar.com/html/api/java/sql/Types.java.html
#                        jdbc-id  iso-name              jdbc-name
jdbc_to_iso_data_type = {'2005' : 'text', 
                         '2011' : 'text',
                         '2004' : 'text',
                         '-3'   : 'text',
                         '-4'   : 'text',
                         '-1'   : 'text',               # LONGVARCHAR
                         '-16'  : 'text',
                         '93'   : 'timestamp',                                                                                                    
                         '92'   : 'time',  
                         '1'    : 'varchar()',          # CHAR
                         '-15'  : 'varchar()',                           
                         '4'    : 'integer',            # INTEGER 
                         '-5'   : 'integer',            # BIGINT
                         '5'    : 'integer',            # SMALLINT
                         '-6'   : 'integer',            # TINYINT                                                                          
                         '8'    : 'double precision',   # DOUBLE 
                         '7'    : 'real',               # REAL
                         '6'    : 'float',              # FLOAT   
                         '16'   : 'varchar(5)',    
                         '-7'   : 'varchar(5)',         # BIT                          
                         '2'    : 'numeric',            # NUMERIC  # TODO: Se xslt for ekstra nyanser på denne  
                         '3'    : 'numeric',            # DECIMAL   
                         '12'   : 'varchar()',          # VARCHAR 
                         '-9'   : 'varchar()'                                                                                                                                                                                                                                                                                                                                                           
}


def sort_dependent_tables(table_defs, base_path):
    deps_dict = {}
    for table_def in table_defs:
        table_name = table_def.find("table-name")
        disposed = table_def.find("disposed")
        if disposed.text != "true":
            deps_dict.update({
                table_name.text:
                get_table_deps(table_name, table_def, deps_dict,
                                empty_tables, illegal_tables)
            })
    deps_list = toposort_flatten(deps_dict)

    return deps_list


def get_table_deps(table_name, table_def, deps_dict, empty_tables,
                   illegal_tables):
    table_deps = set()
    foreign_keys = table_def.findall("foreign-keys/foreign-key")
    for foreign_key in foreign_keys:
        constraint_name = foreign_key.find("constraint-name")
        ref_table = foreign_key.find("references/table-name")
        ref_table_value = ref_table.text.lower()
        if ref_table_value not in table_deps and ref_table_value not in empty_tables:
            if ref_table_value in deps_dict.keys():
                if table_name.text in deps_dict[ref_table_value]:
                    constraint_name.text = "_disabled_" + constraint_name.text
                    continue
            if ref_table.text in illegal_tables:
                ref_table_value = illegal_tables[ref_table.text].lower()
            table_deps.add(ref_table_value)

    if len(table_deps) == 0:
        table_deps.add(table_name.text)
    return table_deps


def tsv_fix(base_path, new_file_name, pk_set, illegal_columns_lower_case):
    tempfile = NamedTemporaryFile(
        mode='w', dir=base_path + "/content/data/", delete=False)

    pwb_replace_in_file(new_file_name, '\0', '')  # Remove null bytes
    table = etl.fromcsv(
        new_file_name,
        delimiter='\t',
        skipinitialspace=True,
        quoting=csv.QUOTE_NONE,
        quotechar='',
        escapechar='')

    table = pwb_lower_case_header(table)
    table = etl.rename(table, illegal_columns_lower_case, strict=False)
    row_count = etl.nrows(table)

    print(new_file_name)
    for pk in pk_set:
        table = etl.convert(table, pk.lower(),
                            lambda a: a if len(str(a)) > 0 else '-')

    writer = csv.writer(
        tempfile,
        delimiter='\t',
        quoting=csv.QUOTE_NONE,
        quotechar='',
        escapechar='',
        lineterminator='\n')
    writer.writerows(table)

    shutil.move(tempfile.name, new_file_name)
    return row_count

if __name__ == "__main__":
    config = SafeConfigParser()
    pwb_dir = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.abspath(os.path.join(pwb_dir, '..', 'tmp'))
    conf_file = tmp_dir + "/pwb.ini"
    config.read(conf_file)
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    sql_file = tmp_dir + "/meta_process.sql"
    illegal_terms_file = pwb_dir + '/config/illegal_terms.txt'

    # TODO: Legg også inn sjekk på at mappen ~/.arkimint/ finnes. Flere steder?
    if os.name != "posix":
        app = gui(useTtk=True)
        app.setLocation("CENTER")
        app.setTtkTheme("winnative")
        app.errorBox("Error", "Only supported on Arkimint")
        quit(conf_file)

    filepath = pwb_add_wim_file(data_dir)

    if filepath:
        pwb_add_config_section(config, 'ENV')
        config.set('ENV', 'wim_path', filepath)
        config.set('ENV', 'log_file', "system_process_metadata.log")
        config.set('ENV', 'process', "meta")
        with open(conf_file, "w+") as configfile:
            config.write(configfile, space_around_delimiters=False)
    else:
        quit(conf_file)

    sys_name = os.path.splitext(os.path.basename(filepath))[0]
    mount_dir = data_dir + "/" + sys_name + "_mount"

    empty_tables = []
    illegal_terms_set = set(map(str.strip, open(illegal_terms_file)))   
    d = {s:s + '_' for s in illegal_terms_set}
    illegal_tables = d.copy()
    illegal_columns = d.copy()

    # TODO: Feil at sletter logg i tilfelle reruns? Endre så en logg pr subsystem heller
    open(tmp_dir + "/PWB.log", 'w').close()  # Clear log file
    mount_wim(filepath, mount_dir)

    # TODO: Er linje under riktig etter endring til native test av import når flere sub_systems ?
    open(sql_file, 'w').close()  # Blank out between runs

    sub_systems_path = mount_dir + "/content/sub_systems/"
    proceed = pwb_yes_no_prompt("Remove manually any disposable data from \n'"
                                + sub_systems_path + "'.\n\n Proceed?")


    if not proceed:
        sys.exit()

    subfolders = os.listdir(sub_systems_path)
    for folder in subfolders:
        base_path = sub_systems_path + folder
        ddl_file = base_path + "/documentation/metadata.sql"
        oracle_dir = base_path + "/documentation/oracle_import/"
        header_xml_file = base_path + "/header/metadata.xml"
        mod_xml_file = base_path + "/documentation/metadata_mod.xml"

        pathlib.Path(oracle_dir).mkdir(parents=True, exist_ok=True)

        if os.path.isdir(
                os.path.join(os.path.abspath(sub_systems_path),
                             folder)) and os.path.isfile(header_xml_file):
            tree = ET.parse(header_xml_file)
            tree_lookup = ET.parse(header_xml_file)
            illegal_columns_lower_case = pwb_lower_dict(illegal_columns)

            t_count = 0
            c_count = 0
            deps_dict = {}
            table_defs = tree.findall("table-def")
            for table_def in table_defs:
                table_name = table_def.find("table-name")
                # table_name_attrib = table_def.attrib['name']
                old_table_name = ET.Element("original-table-name")
                old_table_name.text = table_name.text

                # TODO: Menyvalg for dispose trenger bare fjerne tsv-fil

                # Add tables names too long for oracle to 'illegal_tables'
                if len(table_name.text
                       ) > 30 and table_name.text not in illegal_tables:
                    t_count += 1
                    illegal_tables[
                        table_name.
                        text] = table_name.text[:26] + "_" + str(t_count) + "_"

                file_name = base_path + "/content/data/" + table_name.text.lower(
                ) + ".txt"
                new_file_name = os.path.splitext(file_name)[0] + '.tsv'
                if os.path.isfile(file_name):
                    os.rename(file_name, new_file_name)

                if table_name.text in illegal_tables:
                    table_name.text = illegal_tables[table_name.text]

                    ill_new_file_name = os.path.splitext(file_name)[0] + '_.tsv'
                    if os.path.isfile(new_file_name):
                        os.rename(new_file_name, ill_new_file_name)
                    new_file_name = ill_new_file_name

                table_name.text = table_name.text.lower()
                table_def.insert(3, old_table_name)
                table_def.set('name', table_name.text)

                pk_set = set()
                column_defs = table_def.findall("column-def")
                for column_def in column_defs:
                    column_name = column_def.find('column-name')
                    primary_key = column_def.find('primary-key')
                    column_name_length = len(column_name.text)

                    if column_name_length > 30 and column_name.text not in illegal_columns:
                        c_count += 1
                        illegal_columns[
                            column_name.
                            text] = column_name.text[:26] + "_" + str(c_count)

                    if primary_key.text == 'true':
                        if column_name.text in illegal_columns:
                            pk_set.add(illegal_columns[column_name.text])
                        else:
                            pk_set.add(column_name.text)

                # Add row-count/disposed-info:
                disposed = ET.Element("disposed")
                disposed.text = "false"
                disposal_comment = ET.Element("disposal_comment")
                disposal_comment.text = " "
                rows = ET.Element("rows")

                # TODO: Legg inn sjekk så ikke leser rader på nytt hvis gjort før -> tull med row_count da?
                if os.path.exists(new_file_name):
                    row_count = tsv_fix(base_path, new_file_name, pk_set,
                                        illegal_columns_lower_case)

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

                table_def.insert(5, rows)
                table_def.insert(6, disposed)
                table_def.insert(7, disposal_comment)

            # Sort tables in dependent order:
            deps_list = sort_dependent_tables(table_defs, base_path)
            with open(base_path + '/documentation/import_order.txt','w') as file:
                for val in deps_list:
                    file.write('%s\n' % val)

            self_dep_dict = {}
            ddl_columns = {}
            for table_def in table_defs:
                table_name = table_def.find("table-name")
                dep_position = ET.Element("dep-position")
                disposed = table_def.find("disposed")
                self_dep_set = set()
                index = 0

                ora_ctl_file = oracle_dir + table_name.text + '.ctl'
                ora_ctl_list = []
                if disposed.text != "true":
                    ora_ctl = [
                        'LOAD DATA', 'CHARACTERSET UTF8 LENGTH SEMANTICS CHAR',
                        'INFILE ' + table_name.text + '.tsv',
                        'INSERT INTO TABLE ' + str(table_name.text).upper(),
                        "FIELDS TERMINATED BY '\\t' TRAILING NULLCOLS", '(#'
                    ]
                    ora_ctl_list.append('\n'.join(ora_ctl))

                if table_name.text in deps_list:
                    index = int(deps_list.index(table_name.text))

                dep_position.text = str(index + 1)
                table_def.insert(6, dep_position)
                i = 0

                foreign_keys = table_def.findall("foreign-keys/foreign-key")
                for foreign_key in foreign_keys:
                    tab_constraint_name = foreign_key.find("constraint-name")
                    old_tab_constraint_name = ET.Element(
                        "original-constraint-name")
                    old_tab_constraint_name.text = tab_constraint_name.text

                    if str(tab_constraint_name.text).startswith('SYS_C'):
                        tab_constraint_name.text = tab_constraint_name.text + '_'

                    tab_constraint_name.text = tab_constraint_name.text.lower()
                    foreign_key.insert(1, old_tab_constraint_name)

                    fk_references = foreign_key.findall('references')
                    for fk_reference in fk_references:
                        tab_ref_table_name = fk_reference.find("table-name")
                        old_tab_ref_table_name = ET.Element(
                            "original-table-name")
                        old_tab_ref_table_name.text = tab_ref_table_name.text

                        if tab_ref_table_name.text.lower() in empty_tables:
                            tab_constraint_name.text = "_disabled_" + tab_constraint_name.text
                        elif tab_ref_table_name.text in illegal_tables:
                            tab_ref_table_name.text = tab_ref_table_name.text + '_'

                        tab_ref_table_name.text = tab_ref_table_name.text.lower(
                        )
                        fk_reference.insert(3, old_tab_ref_table_name)

                    # WAIT: Slå sammen de to under til en def
                    source_columns = foreign_key.findall('source-columns')
                    for source_column in source_columns:
                        source_column_names = source_column.findall('column')

                        for source_column_name in source_column_names:
                            old_source_column_name = ET.Element(
                                "original-column")
                            old_source_column_name.text = source_column_name.text

                            if source_column_name.text in illegal_columns:
                                source_column_name.text = illegal_columns[
                                    source_column_name.text]

                            source_column_name.text = source_column_name.text.lower(
                            )
                            source_column.insert(10, old_source_column_name)

                    referenced_columns = foreign_key.findall(
                        'referenced-columns')
                    for referenced_column in referenced_columns:
                        referenced_column_names = referenced_column.findall(
                            'column')

                        for referenced_column_name in referenced_column_names:
                            old_referenced_column_name = ET.Element(
                                "original-column")
                            old_referenced_column_name.text = referenced_column_name.text

                            if referenced_column_name.text in illegal_columns:
                                referenced_column_name.text = illegal_columns[
                                    referenced_column_name.text]

                            referenced_column_name.text = referenced_column_name.text.lower(
                            )
                            referenced_column.insert(
                                10, old_referenced_column_name)

                column_defs = table_def.findall("column-def")

                column_defs[:] = sorted(
                    column_defs,
                    key=lambda elem: int(elem.findtext('dbms-position')))
                # WAIT: Sortering virker men blir ikke lagret til xml-fil. Fiks senere når lage siard/datapackage-versjoner

                ddl_columns_list = []
                for column_def in column_defs:
                    column_name = column_def.find('column-name')
                    java_sql_type_name = column_def.find('java-sql-type-name')
                    java_sql_type = column_def.find('java-sql-type')
                    dbms_data_size = column_def.find('dbms-data-size')
                    dbms_data_type = column_def.find('dbms-data-type')
                    old_column_name = ET.Element("original-column-name")
                    old_column_name.text = column_name.text

                    if column_name.text in illegal_columns:
                        column_name.text = illegal_columns[
                            column_name.text].lower()
                    else:
                        column_name.text = column_name.text.lower()

                    column_def.insert(2, old_column_name)
                    column_def.set('name', column_name.text)

                    col_references = column_def.findall('references')
                    for col_reference in col_references:
                        ref_column_name = col_reference.find('column-name')
                        col_ref_table_name = col_reference.find('table-name')
                        col_constraint_name = col_reference.find(
                            'constraint-name')
                        old_col_constraint_name = ET.Element(
                            "original-constraint-name")
                        old_col_constraint_name.text = col_constraint_name.text
                        old_ref_column_name = ET.Element(
                            "original-column-name")
                        old_ref_column_name.text = ref_column_name.text
                        old_ref_table_name = ET.Element("original-table-name")
                        old_ref_table_name.text = col_ref_table_name.text

                        if ref_column_name.text in illegal_columns:
                            ref_column_name.text = illegal_columns[
                                ref_column_name.text]
                            column_def.insert(3, old_ref_column_name)

                        if col_ref_table_name.text in illegal_tables:

                            col_ref_table_name.text = illegal_tables[
                                col_ref_table_name.text]
                            col_reference.insert(3, old_ref_table_name)

                        old_col_constraint_fix = False
                        if str(col_constraint_name.text).startswith('SYS_C'):
                            col_constraint_name.text = col_constraint_name.text + '_'
                            old_col_constraint_fix = True

                        if col_ref_table_name.text.lower() in empty_tables:
                            col_constraint_name.text = "_disabled_" + col_constraint_name.text
                            old_col_constraint_fix = True

                        if old_col_constraint_fix:
                            col_reference.insert(2, old_col_constraint_name)

                        if col_ref_table_name.text.lower(
                        ) == table_name.text and col_ref_table_name.text.lower(
                        ) not in empty_tables:
                            self_dep_set.add(ref_column_name.text.lower() +
                                             ':' + column_name.text.lower())

                        xpath_str = "table-def[table-name='" + col_ref_table_name.text + "']/column-def[column-name='" + old_ref_column_name.text + "']"
                        ref_column = tree_lookup.find(xpath_str)

                        if ref_column:
                            ref_column_data_size = ref_column.find(
                                'dbms-data-size')
                            if ref_column_data_size.text != dbms_data_size.text:
                                dbms_data_size.text = ref_column_data_size.text
                                print("table: " + col_ref_table_name.text)
                                print("col:   " + ref_column_name.text)
                                print(ref_column_data_size.text)


                    if disposed.text != "true":
                        # TODO: Juster så denne koden er koblet mot jdbc_to_iso_data_type (3-veis mapping da?)
                        ora_ctl_type = ''
                        if (java_sql_type_name.text in ('NVARCHAR', 'VARCHAR',
                                                        'CHAR')):
                            ora_ctl_type = 'CHAR'
                        elif (java_sql_type_name.text == 'DECIMAL'):
                            ora_ctl_type = 'DECIMAL EXTERNAL'
                        elif (java_sql_type_name.text == 'TIMESTAMP'):
                            ora_ctl_type = 'TIMESTAMP "YYYY-MM-DD HH24:MI:SS"'
                        elif (java_sql_type_name.text == 'INTEGER'):
                            ora_ctl_type = 'INTEGER EXTERNAL'                            
                        elif (java_sql_type_name.text == 'FLOAT'):
                            ora_ctl_type = 'FLOAT EXTERNAL'
                        elif (java_sql_type_name.text == 'DOUBLE'):
                            ora_ctl_type = 'DOUBLE EXTERNAL'                            
                        elif (java_sql_type_name.text in ('VARBINARY',
                                                          'LONGVARCHAR',
                                                          'CLOB')):
                            ora_ctl_type = 'CHAR(1000000)'  # WAIT: Finn absolutte maks som kan brukes
                        else:
                            print(
                                "Missing oracle ctl-file datatype mapping for "
                                + java_sql_type_name.text + '(' + java_sql_type.text + ')')

                        if dbms_data_type.text.find(
                                '(') != -1 and java_sql_type_name.text not in (
                                    'FLOAT', 'VARBINARY', 'LONGVARCHAR',
                                    'CLOB'):
                            ora_ctl_type = ora_ctl_type + '(' + dbms_data_size.text + ')'

                        ora_ctl_list.append(
                            column_name.text + ' ' + ora_ctl_type)

                        iso_data_type = jdbc_to_iso_data_type[java_sql_type.text]
                        ddl_columns_list.append(column_name.text + ' ' + iso_data_type + ',')                            

                # Write Oracle SQL Loader control file:
                if disposed.text != "true":
                    with open(ora_ctl_file, "w") as file:
                        file.write((',\n'.join(ora_ctl_list)).replace(
                            '#,', '') + ' TERMINATED BY WHITESPACE \n)')

                if len(self_dep_set) != 0:
                    self_dep_dict.update({table_name.text: self_dep_set})

                ddl_columns[table_name.text.lower()] =  '\n'.join(ddl_columns_list)         

            root = tree.getroot()
            indent(root)
            tree.write(mod_xml_file)

            # Sort lines in files with self constraints correctly:
            # TODO: Gjør om til funksjon
            for key, value in self_dep_dict.items():
                file_name = base_path + "/content/data/" + key + ".tsv"
                tempfile = NamedTemporaryFile(
                    mode='w', dir=base_path + "/content/data/", delete=False)
                table = etl.fromcsv(
                    file_name,
                    delimiter='\t',
                    skipinitialspace=True,
                    quoting=csv.QUOTE_NONE,
                    quotechar='',
                    escapechar='')
                key_dep_dict = {}

                print(file_name)
                for constraint in value:
                    child_dep, parent_dep = constraint.split(':')
                    data = etl.values(table, child_dep, parent_dep)
                    for d in data:
                        key_dep_set = {d[1]}
                        key_dep_dict.update({d[0]: key_dep_set})

                key_dep_list = toposort_flatten(key_dep_dict)
                table = etl.addfield(
                    table, 'pwb_index',
                    lambda rec: int(key_dep_list.index(rec[child_dep])))
                table = etl.sort(table, 'pwb_index')
                table = etl.cutout(table, 'pwb_index')

                writer = csv.writer(
                    tempfile,
                    delimiter='\t',
                    quoting=csv.QUOTE_NONE,
                    quotechar='',
                    lineterminator='\n',
                    escapechar='')

                writer.writerows(table)
                shutil.move(tempfile.name, file_name)

            # Generate ddl:
            sql = [
                "\n",
                "---- Generate DDL -----",
                "WbXslt -inputfile=" + mod_xml_file,
                "-stylesheet=PWB/xslt/metadata2ddl.xslt",
                "-xsltOutput=" + ddl_file + ";",
            ]

            with open(sql_file, "a+") as file:
                file.write("\n".join(sql))


            # TODO: Test python-kode for generering av ddl under her
            # tree = ET.parse(mod_xml_file)
            ddl = []


            # table_defs = tree.findall("table-def")

            for table in deps_list:
                ddl.append('\nCREATE TABLE ' + table + '\n' + ddl_columns[table])

            with open(ddl_file, "a+") as file:
                file.write("\n".join(ddl))                


            # sql = [
            #     "\n",
            #     "---- Generate DDL -----",
            #     "WbXslt -inputfile=" + mod_xml_file,
            #     "-stylesheet=PWB/xslt/metadata2ddl.xslt",
            #     "-xsltOutput=" + ddl_file + ";",
            # ]

            # with open(sql_file, "a+") as file:
            #     file.write("\n".join(sql))
          
