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
import
import subprocess, os, pathlib, glob, sys, copy, collections, shutil, csv
if os.name == "posix":
    # from lxml import etree as ET
    import xml.etree.ElementTree as ET
    import pandas as pd

from functools import reduce
from configparser import SafeConfigParser
from appJar import gui
# from lxml import etree # TODO: Fjern fra arkimint også hvis ikke trengs andre steder lenger heller
from toposort import toposort, toposort_flatten
from tempfile import NamedTemporaryFile
import petl as etl
from common.wim import mount_wim
from common.xml import indent
from common.gui import pwb_add_wim_file
from common.dialog import pwb_yes_no_prompt
from common.dictionary import pwb_lower_dict
from common.file import pwb_replace_in_file
from common.config import pwb_add_config_section
from common.petl import pwb_lower_case_header
from common.shell import run_shell_command

csv.field_size_limit(sys.maxsize)

# http://www.docjar.com/html/api/java/sql/Types.java.html
#                        jdbc-id  iso-name               jdbc-name
jdbc_to_iso_data_type = {
                         '-16'  : 'text',               # LONGNVARCHAR
                         '-15'  : 'varchar()',          # NCHAR                       
                         '-9'   : 'varchar()',          # NVARCHAR                                                                                                                                                                                                                                                                                                                                                  
                         '-7'   : 'varchar(5)',         # BIT                          
                         '-6'   : 'integer',            # TINYINT                                                                          
                         '-5'   : 'integer',            # BIGINT
                         '-4'   : 'text',               # LONGVARBINARY
                         '-3'   : 'text',               # VARBINARY
                         '-2'   : 'text',               # BINARY                      
                         '-1'   : 'text',               # LONGVARCHAR
                         '1'    : 'varchar()',          # CHAR
                         '2'    : 'numeric',            # NUMERIC  # TODO: Se xslt for ekstra nyanser på denne  
                         '3'    : 'decimal',            # DECIMAL  # TODO: Se xslt for ekstra nyanser på denne    
                         '4'    : 'integer',            # INTEGER 
                         '5'    : 'integer',            # SMALLINT
                         '6'    : 'float',              # FLOAT   
                         '7'    : 'real',               # REAL
                         '8'    : 'double precision',   # DOUBLE 
                         '12'   : 'varchar()',          # VARCHAR 
                         '16'   : 'varchar(5)',         # BOOLEAN
                         '91'   : 'date',               # DATE                        
                         '92'   : 'time',               # TIME
                         '93'   : 'timestamp',          # TIMESTAMP                                                                                                
                         '2004' : 'text',               # BLOB 
                         '2005' : 'text',               # CLOB
                         '2011' : 'text',               # NCLOB
}

#                            jdbc-id  ora-ctl-name                          jdbc-name
jdbc_to_ora_ctl_data_type = {
                            '-16'  : 'CHAR(1000000)',                      # LONGNVARCHAR # WAIT: Finn absolutte maks som kan brukes
                            '-15'  : 'CHAR()',                             # NCHAR                       
                            '-9'   : 'CHAR()',                             # NVARCHAR                                                                                                                                                                                                                                                                                                                                                  
                            '-7'   : 'CHAR(5)',                            # BIT                          
                            '-6'   : 'INTEGER EXTERNAL',                   # TINYINT                                                                          
                            '-5'   : 'INTEGER EXTERNAL',                   # BIGINT
                            '-4'   : 'CHAR(1000000)',                      # LONGVARBINARY
                            '-3'   : 'CHAR(1000000)',                      # VARBINARY
                            '-2'   : 'CHAR(1000000)',                      # BINARY                      
                            '-1'   : 'CHAR(1000000)',                      # LONGVARCHAR
                            '1'    : 'CHAR()',                             # CHAR
                            '2'    : 'DECIMAL EXTERNAL',                   # NUMERIC  # TODO: Se xslt for ekstra nyanser på denne  
                            '3'    : 'DECIMAL EXTERNAL',                   # DECIMAL  # TODO: Se xslt for ekstra nyanser på denne    
                            '4'    : 'INTEGER EXTERNAL',                   # INTEGER 
                            '5'    : 'INTEGER EXTERNAL',                   # SMALLINT
                            '6'    : 'FLOAT EXTERNAL',                     # FLOAT   
                            '7'    : 'DECIMAL EXTERNAL',                   # REAL
                            '8'    : 'DECIMAL EXTERNAL',                   # DOUBLE 
                            '12'   : 'CHAR()',                             # VARCHAR 
                            '16'   : 'CHAR(5)',                            # BOOLEAN
                            '91'   : 'DATE "YYYY-MM-DD"',                  # DATE                        
                            '92'   : 'TIMESTAMP',                          # TIME
                            '93'   : 'TIMESTAMP "YYYY-MM-DD HH24:MI:SS"',  # TIMESTAMP                                                                                                
                            '2004' : 'CHAR(1000000)',                      # BLOB 
                            '2005' : 'CHAR(1000000)',                      # CLOB
                            '2011' : 'CHAR(1000000)',                      # NCLOB
}


def quit(conf_file):
    config = SafeConfigParser()
    pwb_add_config_section(config, 'ENV')
    config.set('ENV', 'wim_path', "")
    with open(conf_file, "w+") as configfile:
        config.write(configfile, space_around_delimiters=False)
    sys.exit()


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


def normalize_name(name, illegal_dict):
    norm_name = name
    if name in illegal_dict:
        norm_name = illegal_dict[name]
    return norm_name  


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
            ref_table_value = normalize_name(ref_table.text, illegal_tables).lower()
            table_deps.add(ref_table_value)

    if len(table_deps) == 0:
        table_deps.add(table_name.text)
    return table_deps


def tsv_fix(base_path, new_file_name, pk_list, illegal_columns_lower_case, tsv_process):
    if tsv_process:
        pwb_replace_in_file(new_file_name, '\0', '')  # Remove null bytes

    table = etl.fromcsv(
        new_file_name,
        delimiter='\t',
        skipinitialspace=True,
        quoting=csv.QUOTE_NONE,
        quotechar='',
        escapechar='')

    row_count = etl.nrows(table)

    if tsv_process:
        tempfile = NamedTemporaryFile(mode='w', dir=base_path + "/content/data/", delete=False)        

        table = pwb_lower_case_header(table)
        table = etl.rename(table, illegal_columns_lower_case, strict=False)

        print(new_file_name)
        for pk in pk_list:
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
    bin_dir = os.path.abspath(pwb_dir, '..')
    tmp_dir = os.path.join(bin_dir, 'tmp')
    conf_file = tmp_dir + "/pwb.ini"
    config.read(conf_file)
    data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
    h2_to_tsv_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'xslt/h2_to_tsv.xslt'))
    wbexport_script = os.path.join(tmp_dir, 'wbexport.sql')

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
        data_docs_folder = sub_systems_path + "/" + folder + "/content/data_documents"
        docs_folder = sub_systems_path + "/" + folder + "/content/documents"
        data_folder = sub_systems_path + "/" + folder + "/content/data"    
        documentation_folder = sub_systems_path + "/" + folder + "/documentation/"            
        ddl_file = base_path + "/documentation/metadata.sql"
        tsv_done_file = base_path + "/documentation/tsv_done"
        oracle_dir = base_path + "/documentation/oracle_import/"
        header_xml_file = base_path + "/header/metadata.xml"
        mod_xml_file = base_path + "/documentation/metadata_mod.xml"

        pathlib.Path(data_docs_folder).mkdir(parents=True, exist_ok=True)
        pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
        pathlib.Path(docs_folder).mkdir(parents=True, exist_ok=True)
        pathlib.Path(oracle_dir).mkdir(parents=True, exist_ok=True)

        glob_data = []
        for file in glob.glob(docs_folder + "/*.wim"):
            export_folder = os.path.splitext(file)[0]
            pathlib.Path(export_folder).mkdir(parents=True, exist_ok=True)
            if len(os.listdir(export_folder)) == 0:
                subprocess.run(
                    "wimapply " + file + " " + export_folder, shell=True)
                os.remove(file)

        h2_file = documentation_folder + folder
        h2_done_file = documentation_folder + "done"
        print(h2_done_file)
        if (os.path.isfile(h2_file + ".mv.db")
                and not os.path.isfile(h2_done_file)):
            conn = jaydebeapi.connect(  # WAIT: Endre til egen def
                "org.h2.Driver",
                "jdbc:h2:" + h2_file,
                ["", ""],
                bin_dir +
                "/h2-1.4.196.jar",  # WAIT: Fjern harkodet filnavn
            )

            try:
                curs = conn.cursor()
                curs.execute("SHOW TABLES;")
                data = curs.fetchall()
                tables_in_h2 = [x[0] for x in data]

            except Exception as e:
                print(e)

            finally:
                if curs is not None:
                    curs.close()
                if conn is not None:
                    conn.close()

            tree = ET.parse(header_xml_file)
            table_defs = tree.findall("table-def")
            for table_def in table_defs:
                table_name = table_def.find("table-name")
                disposed = ET.Element("disposed")
                disposed.text = "false"
                if table_name.text not in tables_in_h2:
                    disposed.text = "true"

                table_def.insert(5, disposed)

            root = tree.getroot()
            indent(root)
            tree.write(mod_xml_file)

            xsl = [
                "\n",
                "WbXslt -inputfile=" + mod_xml_file,
                "-stylesheet=" + h2_to_tsv_script,
                '-xsltParameters="url=jdbc:h2:' + h2_file + '"',
                '-xsltParameters="outputdir=' + data_folder + '"',
                "-xsltOutput=" + wbexport_script + ';',
            ]
            with open(tmp_dir + '/h2_to_tsv.sql', "w") as file:
                file.write("\n".join(xsl))

            # TODO: Lag subprocess def som kalles to ganger her med forskjellige parametre
            cmd = 'java -jar sqlworkbench.jar -script=' + tmp_dir + '/h2_to_tsv.sql'
            returncode, stdout, stderr = run_shell_command(cmd, bin_dir)
            print(stdout)

            cmd = 'java -jar sqlworkbench.jar -script=' + tmp_dir + '/wbexport.sql'
            returncode, stdout, stderr = run_shell_command(cmd, bin_dir)
            print(stdout)

            open(h2_done_file, 'a').close()

        for data_file in glob.iglob(data_folder + "/*.data"):
            shutil.move(data_file, data_docs_folder)
        if len(os.listdir(data_folder)) == 0:
            os.rmdir(data_folder)

        if os.path.isdir(
                os.path.join(os.path.abspath(sub_systems_path),
                             folder)) and os.path.isfile(header_xml_file):
            tree = ET.parse(header_xml_file)
            tree_lookup = ET.parse(header_xml_file)
            illegal_columns_lower_case = pwb_lower_dict(illegal_columns) # TODO: Feil for kolonner som legges til illegal i etterkant?

            t_count = 0
            c_count = 0
            pk_dict = {}
            constraint_dict = {}
            fk_columns_dict = {}
            fk_ref_dict = {}
            unique_dict = {}
            table_defs = tree.findall("table-def")
            for table_def in table_defs:
                table_name = table_def.find("table-name")
                old_table_name = ET.Element("original-table-name")
                old_table_name.text = table_name.text

                # TODO: Menyvalg for dispose trenger bare fjerne tsv-fil

                # Add tables names too long for oracle to 'illegal_tables'
                if len(table_name.text) > 30:
                    t_count += 1
                    illegal_tables[table_name.text] = table_name.text[:26] + "_" + str(t_count) + "_"

                file_name = base_path + "/content/data/" + table_name.text.lower(
                ) + ".txt"
                new_file_name = os.path.splitext(file_name)[0] + '.tsv'

                tsv_process = False
                if not os.path.isfile(tsv_done_file):
                    tsv_process = True

                if os.path.isfile(file_name):
                    os.rename(file_name, new_file_name)

                if table_name.text in illegal_tables:
                    table_name.text = illegal_tables[table_name.text]

                    # TODO: Bare slette fil direkte her heller?
                    ill_new_file_name = os.path.splitext(file_name)[0] + '_.tsv'
                    if os.path.isfile(new_file_name):
                        os.rename(new_file_name, ill_new_file_name)
                    new_file_name = ill_new_file_name

                table_name.text = table_name.text.lower()
                table_def.insert(3, old_table_name)
                table_def.set('name', table_name.text)

                # unique_list = []
                index_defs = table_def.findall("index-def")
                for index_def in index_defs:
                    unique = index_def.find('unique')
                    primary_key = index_def.find('primary-key')
                    index_name = index_def.find('name')

                    unique_col_list = []
                    if unique.text == 'true' and primary_key.text == 'false':
                        index_column_names = index_def.findall("column-list/column")
                        for index_column_name in index_column_names:
                            unique_constraint_name = index_column_name.attrib['name'].lower()    
                            unique_col_list.append(unique_constraint_name)   
                        unique_dict[(table_name.text, index_name.text.lower())] = sorted(unique_col_list)                                                                 

                pk_list = []
                column_defs = table_def.findall("column-def")
                for column_def in column_defs:
                    column_name = column_def.find('column-name')
                    primary_key = column_def.find('primary-key')

                    if len(column_name.text) > 30:
                        c_count += 1
                        illegal_columns[column_name.text] = column_name.text[:26] + "_" + str(c_count)

                    if primary_key.text == 'true':
                        pk_list.append(normalize_name(column_name.text, illegal_columns).lower())

                pk_dict[table_name.text] = ', '.join(sorted(pk_list))          

                # Add row-count/disposed-info:
                disposed = ET.Element("disposed")
                disposed.text = "false"
                disposal_comment = ET.Element("disposal_comment")
                disposal_comment.text = " "
                rows = ET.Element("rows")

                # TODO: Legg inn sjekk så ikke leser rader på nytt hvis gjort før -> tull med row_count da?
                if os.path.exists(new_file_name):
                    row_count = tsv_fix(base_path, new_file_name, pk_list,
                                        illegal_columns_lower_case, tsv_process)

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

                constraint_set = set()
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
                        old_tab_ref_table_name = ET.Element("original-table-name")
                        old_tab_ref_table_name.text = tab_ref_table_name.text

                        if tab_ref_table_name.text.lower() in empty_tables:
                            tab_constraint_name.text = "_disabled_" + tab_constraint_name.text

                        tab_ref_table_name.text = normalize_name(tab_ref_table_name.text, illegal_tables).lower()                           
                        fk_reference.insert(3, old_tab_ref_table_name)

                        if not tab_constraint_name.text.startswith('_disabled_'):
                            constraint_set.add(tab_constraint_name.text + ':' + tab_ref_table_name.text)


                    # WAIT: Slå sammen de to under til en def

                    source_column_set = set()
                    source_columns = foreign_key.findall('source-columns')
                    for source_column in source_columns:
                        source_column_names = source_column.findall('column')

                        source_columns_string = ''
                        for source_column_name in source_column_names:
                            old_source_column_name = ET.Element("original-column")
                            old_source_column_name.text = source_column_name.text
                            source_column_name.text = normalize_name(source_column_name.text, illegal_columns).lower()   
                            source_column.insert(10, old_source_column_name)
                            source_column_set.add(source_column_name.text)

                    if not len(source_column_set) == 0:
                        fk_columns_dict.update({tab_constraint_name.text: source_column_set}) # TODO: Endre andre til å være på denne formen heller enn split på : mm?                           

                    referenced_columns = foreign_key.findall('referenced-columns')
                    for referenced_column in referenced_columns:
                        referenced_column_names = referenced_column.findall('column')

                        for referenced_column_name in referenced_column_names:
                            old_referenced_column_name = ET.Element("original-column")
                            old_referenced_column_name.text = referenced_column_name.text
                            referenced_column_name.text = normalize_name(referenced_column_name.text, illegal_columns).lower()    
                            referenced_column.insert(10, old_referenced_column_name)


                constraint_dict[table_name.text] =  ','.join(constraint_set).lower()     

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
                    column_name.text = normalize_name(column_name.text, illegal_columns).lower()   
                    column_def.insert(2, old_column_name)
                    column_def.set('name', column_name.text)

                    col_references = column_def.findall('references')
                    ref_col_ok  = False
                    for col_reference in col_references:
                        ref_col_ok  = True
                        ref_column_name = col_reference.find('column-name')
                        col_ref_table_name = col_reference.find('table-name')
                        col_constraint_name = col_reference.find('constraint-name')
                        old_col_constraint_name = ET.Element("original-constraint-name")
                        old_col_constraint_name.text = col_constraint_name.text
                        old_ref_column_name = ET.Element("original-column-name")
                        old_ref_column_name.text = ref_column_name.text
                        old_ref_table_name = ET.Element("original-table-name")
                        old_ref_table_name.text = col_ref_table_name.text

                        ref_column_name.text = normalize_name(ref_column_name.text, illegal_columns)    
                        column_def.insert(3, old_ref_column_name)

                        col_ref_table_name.text = normalize_name(col_ref_table_name.text, illegal_tables)    
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
  
                    if ref_col_ok:
                        fk_ref_dict[table_name.text + ':' + column_name.text] = ref_column_name.text.lower()                        
                 

                    if disposed.text != "true":
                        ora_ctl_type = jdbc_to_ora_ctl_data_type[java_sql_type.text]
                        if '()' in ora_ctl_type:
                            ora_ctl_type = ora_ctl_type.replace('()', '(' + dbms_data_size.text + ')')

                        ora_ctl_list.append(
                            column_name.text + ' ' + ora_ctl_type)

                        iso_data_type = jdbc_to_iso_data_type[java_sql_type.text]
                        if '()' in iso_data_type:
                            iso_data_type = iso_data_type.replace('()', '(' + dbms_data_size.text + ')')
                     
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
            if not os.path.isfile(tsv_done_file):
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

            open(tsv_done_file, 'a').close()         

            ddl = []
            for table in deps_list:
                pk_str  = ''
                if pk_dict[table]:
                    pk_str = ',\nPRIMARY KEY (' + pk_dict[table] + ')'

                unique_str = ''
                unique_constraints = {key: val for key, val in unique_dict.items() if key[0] == table} 
                if unique_constraints:
                    for key, value in unique_constraints.items():
                        unique_str = unique_str + ',\nCONSTRAINT ' + key[1] + ' UNIQUE (' + ', '.join(value) + ')'

                fk_str = ''
                if constraint_dict[table]:  
                    for s in [x for x in constraint_dict[table].split(',')]:
                        constr, ref_table = s.split(':')
                        
                        ref_column_list = []
                        source_column_list = fk_columns_dict[constr]
                        for col in source_column_list:
                            ref_column_list.append(fk_ref_dict[table + ':' + col] + ':' + col)

                        ref_column_list = sorted(ref_column_list)
                        ref_s = '' 
                        source_s = ''
                        for s in ref_column_list:
                            ref, source = s.split(':')
                            ref_s = ref_s + ', ' + ref 
                            source_s = source_s + ', ' + source
                        ref_s = ref_s[2:] 
                        source_s = source_s[2:]    

                        fk_str = fk_str + ',\nCONSTRAINT ' + constr + '\nFOREIGN KEY (' + source_s + ')\nREFERENCES ' + ref_table + ' (' + ref_s + ')'       

                ddl.append('\nCREATE TABLE ' + table + '\n(\n' + ddl_columns[table][:-1] + pk_str + unique_str + fk_str + '\n);')

            with open(ddl_file, "w") as file:
                file.write("\n".join(ddl))                                                                                                 

            # TODO: Denne syntaksen er støttet av alle             
            # create table newish_table (
            #     id   int not null,
            #     id_A int not null,
            #     id_B int not null,
            #     id_C int null,
            #     id_t int,
            #     constraint pk_newish_table primary key (id),
            #     constraint u_constrainte4 unique (id_t),
            #     constraint u_constrainte5 unique (id_A, id_B, id_C)
            # );

          





































