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

import subprocess, os, sys, glob, shutil, fileinput, pathlib
from functools import reduce
from configparser import SafeConfigParser

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
ora_reset_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'oracle_reset.sql'))
ms_reset_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mssql_reset.sql'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
filepath = config.get('ENV', 'wim_path')
sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = data_dir + "/" + sys_name + "_mount"
db_list = ['postgresql','oracle','mssql','sqlite']     
  

if not filepath:
    exit()  

# def gen_import_statements(db):
#     import_statements = []
#     import_str = "" 
#     for table in order_list:
#         if db == 'postgresql': 
#             import_str = '''psql "user='postgres' password='P@ssw0rd' host='localhost'" -v "ON_ERROR_STOP=1" -c "\copy pwb.''' +  table + ''' FROM ''' \
#                 + sub_data_folder + table + '''.tsv delimiter E'\\t' CSV HEADER QUOTE E'\\b' NULL AS ''"'''                
#         elif db == 'oracle':
#             sql_loader_log = tmp_dir + '/sqlldr_log.log'
#             sql_loader_bad = tmp_dir + '/sqlldr_bad.log'
#             sql_loader_ctl = documentation_folder + 'oracle_import/' + table + '.ctl'
#             import_str = oracle_bin + 'sqlldr oracle/pwb bad =' + sql_loader_bad + ' log=' + sql_loader_log + ' errors=0 skip=1 direct=true control=' + sql_loader_ctl
#         elif db == 'mssql':   
#             import_str = bcp_bin + ' ' + table + ' in ' + sub_data_folder + table + '.tsv -U sa -P P@ssw0rd -d pwb -S localhost -r "\\r\\n" -F 2 -c'
#         elif db == 'sqlite':   
#             # import_str = 'sqlite3  -separator "\\t" -cmd ".import ' sqlite_db  + sub_data_folder + table + '.tsv ' + + '"' 
#             import_str = '''dqt='"'; sqlite3  ''' + sqlite_db + ''' -bail -batch ".mode tabs" ".import ${dqt}| tail -n +2 ''' + sub_data_folder + table + '''.tsv${dqt}''' + table + '''"'''
#             # import_str = '''sqlite3  ''' + sqlite_db + ''' -bail -batch ".mode tabs" ".import \\"| tail -n +2 ''' + sub_data_folder + table + '''.tsv\\" ''' + table + '''"'''
#             # \x22

#         import_statements.append(import_str)
#     return '\n'.join(import_statements)         


# WAIT: Lag også vbs-versjon for windows
def gen_import_file(db):                 
    ln = [
            '#!/bin/bash \n',
            '# -- ' + str(db) + ' --',
            '# -- modify variables as needed before running import script -- \n',
            '# -- Variables --',
            'user=' + users[db],
            'password=' + passwords[db],
            'host=localhost',
            'schema=' + schemas[db],
            'db_name=' + db_names[db],
            'sql_bin=' + sql_bin[db],
            'import_bin=' + import_bins[db],
            'import_order_file=' + import_order_file,
            'data_path=' + data_path,            
            'reset_file=' + reset_files[db],
            'ddl_file=' + ddl_files[db] + '\n',
            '# -- Code --',
            reset_statements[db],
            create_schema_statements[db],
            'while IFS= read -r table',
            'do',
            import_statements[db],
            # '$import_bin $user/$password@$host errors=0 skip=1 direct=true control="$table".ctl data="$data_path""$table".tsv',            
            'done < "$import_order_file"'
            # # db_reset_statements[db], # TODO: Foreløpig fjernet for test
            # 'touch ' + db_done_files[db], # TODO: Bedre sjekker før denne gjøres
    ]

    with open(import_sql_files[db], "w") as file:
        file.write("\n".join(ln))          


# TODO: Se her for datatyper: http://troels.arvin.dk/db/rdbms/#data_types

sub_systems_path = mount_dir + "/content/sub_systems/"
subfolders = os.listdir(sub_systems_path)
for folder in subfolders:
    folder_path = sub_systems_path + folder 
    header_xml_file = folder_path + "/header/metadata.xml"
    data_path = folder_path  + "/content/data/"

    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)) \
    and os.path.isfile(header_xml_file) and os.listdir(data_path):
        
        documentation_folder = folder_path + "/documentation/"
        import_order_file = documentation_folder + 'import_order.txt'
        sqlite_db = "/tmp/" + folder + ".db"

        order_list = []
        with open(import_order_file) as file:
            for cnt, line in enumerate(file):
                order_list.append(line.rstrip())          

        users = {}
        sql_bin = {}
        import_bins = {}
        passwords = {}
        schemas = {}
        db_names = {}        
        done_files = {} # WAIT: Skriv til config fil heller
        import_sql_files = {} 
        reset_statements = {}     
        create_schema_statements = {}  
        ddl_files = {} 
        reset_files = {}
        import_statements = {}

        for db in db_list:
            pathlib.Path(documentation_folder + db + '_import').mkdir(parents=True, exist_ok=True)
            done_files[db]=documentation_folder + db + '_done'
            import_sql_files[db]=documentation_folder + db + '_import/import.sh'

            if db in ('postgresql','sqlite'): 
                ddl_files[db] = documentation_folder + 'metadata.sql'
                reset_files[db] = '#Not needed for ' + db
            else:                             
                ddl_files[db] = documentation_folder + db + '_import/metadata_' + db + '.sql' # WAIT: Endre så konsekvent navngiving
                reset_files[db] = documentation_folder + db + '_import/' + db + '_reset.sql'

            if db == 'postgresql':
                users[db] = 'postgres'
                passwords[db] = 'P@ssw0rd'
                schemas[db] = 'pwb #Any existing tables in schema will be deleted by first line in code'
                db_names[db] = '#Not needed for postgresql'
                sql_bin[db] = '/usr/bin/psql'
                import_bins[db] = '/usr/bin/psql'
                reset_statements[db] = 'PGOPTIONS="--client-min-messages=warning" $sql_bin "user=$user password=$password host=$host" -c "DROP SCHEMA IF EXISTS $schema CASCADE;"'
                create_schema_statements[db] = '$sql_bin "user=$user password=$password host=$host" -c "CREATE SCHEMA $schema; SET search_path TO $schema;" -f $ddl_file' 
                import_statements[db] = '''$import_bin "user=$user password=$password host=$host" -v "ON_ERROR_STOP=1" -c "\copy \"$schema\".\"$table\" FROM \"$data_path\"\"$table\".tsv delimiter E'\\t' CSV HEADER QUOTE E'\\b' NULL AS ''"'''

            if db == 'oracle': 
                if not os.path.isfile(documentation_folder + db + '_import/oracle_reset.sql'):
                    shutil.copyfile(ora_reset_script, documentation_folder + db + '_import/oracle_reset.sql') 

                users[db] = 'oracle'
                passwords[db] = 'pwb'
                schemas[db] = 'oracle #Any existing tables in schema will be deleted by first line in code'   
                db_names[db] = '#Not needed for oracle'
                sql_bin[db] = '/u01/app/oracle/product/11.2.0/xe/bin/sqlplus'
                import_bins[db] = '/u01/app/oracle/product/11.2.0/xe/bin/sqlldr'                   
                reset_statements[db] = '$sql_bin -S $user/$password@$host < $reset_file'
                create_schema_statements[db] = '$sql_bin  -S $user/$password@$host < $ddl_file'
                import_statements[db] = '$import_bin $user/$password@$host errors=0 skip=1 direct=true control="$table".ctl data="$data_path""$table".tsv'
                repls = (
                            (" text,", " clob,"),
                            (" text)", " clob)"),
                            (" varchar(4000)", " clob"),
                            (" varchar2(4000)", " clob"),
                            (" varchar(", " varchar2("),
                            # (" boolean", " varchar2(5)"),
                )

                with open(ddl_files[db], "w") as file:
                    with open(ddl_files['postgresql'], 'r') as file_r:
                        file.write("ALTER SESSION SET NLS_LENGTH_SEMANTICS=CHAR;\n\n")
                        for line in file_r:
                            file.write(
                                reduce(lambda a, kv: a.replace(*kv), repls, line))

            if db == 'mssql': 
                if not os.path.isfile(documentation_folder + db + '_import/mssql_reset.sql'):
                    shutil.copyfile(ms_reset_script, documentation_folder + db + '_import/mssql_reset.sql') 

                users[db] = 'sa'
                passwords[db] = 'P@ssw0rd'
                schemas[db] = '#Default schema of user on mssql'
                db_names[db] = 'pwb #Any existing tables in database will be deleted by first line in code'  
                sql_bin[db] = '/opt/mssql-tools/bin/sqlcmd'
                import_bins[db] = '/opt/mssql-tools/bin/bcp'   
 

                # TODO: db_navn som variabel til reset_file hvordan?
                reset_statements[db] = '$sql_bin -b -U $user -P $password -h $host -d master -i $reset_file'
                create_schema_statements[db] = '$sql_bin -b -U $user -P $password -h $host -d $db_name -i $ddl_file' 
                import_statements[db] = '$import_bin $user/$password@$host errors=0 skip=1 direct=true control="$table".ctl data="$data_path""$table".tsv'                
                repls = (
                            (" timestamp", " datetime"),
                            (" varchar(", " nvarchar("),       
                            #    (" boolean", " varchar(5)"),
                            #  (" bigint", " numeric"), #TODO: Ser ikke ut til at bigint kan ha desimaler i alle dbtyper
                )

                with open(ddl_files[db], "w") as file:
                    with open(ddl_files['postgresql'], 'r') as file_r:
                        for line in file_r:
                            file.write(
                                reduce(lambda a, kv: a.replace(*kv), repls, line))    

            if db == 'sqlite':
                reset_statements[db] = 'rm ' + sqlite_db + ' 2> /dev/null'
                create_schema_statements[db] = 'sqlite3 ' + sqlite_db + ' < ' + ddl_files[db]   
                                                                          
            if db in ('postgresql', 'oracle', 'mssql'): # TODO: Fjern når kode fikset for alle db
                gen_import_file(db)                                



        for db in db_list:
        #    for db in ('postgresql', 'oracle', 'mssql'): # TODO: Støtte H2, mysql eller siard heller? http://www.h2database.com/html/tutorial.html#csv
            if not os.path.isfile(done_files[db]):
                with open(import_sql_files[db], "r") as meta_check:
                    for line in meta_check:
                        line = str(line)
                        if not line.startswith(' --'):
                            print(line)                                                                
                            sys.stdout.flush()   
                            try:
                                subprocess.check_call(line, shell=True, cwd=data_path)            
                            except subprocess.CalledProcessError:
                                # pass # handle errors in the called executable
                                break
                            except OSError:
                                pass 

                sys.stdout.flush()                                     

                                    


