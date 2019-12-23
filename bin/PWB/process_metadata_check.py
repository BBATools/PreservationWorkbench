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

import subprocess, os, sys, pathlib, glob, shutil, fileinput
from functools import reduce
from configparser import SafeConfigParser

config = SafeConfigParser()
tmp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
conf_file = tmp_dir + "/pwb.ini"
config.read(conf_file)
data_dir = os.path.abspath(os.path.join(tmp_dir, '../../', '_DATA'))
filepath = config.get('ENV', 'wim_path')
sys_name = os.path.splitext(os.path.basename(filepath))[0]
mount_dir = data_dir + "/" + sys_name + "_mount"
sql_file = tmp_dir + "/meta_check.sql"
sql = ""

if not filepath:
    exit()

with open(sql_file, "w+") as file:  # Blank out between runs
    file.write(" ")  

sub_systems_path = mount_dir + "/content/sub_systems/"
subfolders = os.listdir(sub_systems_path)
for folder in subfolders:
    header_xml_file = sub_systems_path + folder + "/header/metadata.xml"
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)) \
    and os.path.isfile(header_xml_file) \
    and os.listdir(sub_systems_path + folder + '/content/data/'):
        documentation_folder = sub_systems_path + folder + "/documentation/"
        sub_data_folder = sub_systems_path + folder + "/content/data/"
        import_order_file = documentation_folder + 'import_order.txt'
        isosql_ddl = documentation_folder + "metadata.sql"
        oracle_ddl = documentation_folder + "metadata_oracle.sql"
        mysql_ddl = documentation_folder + "metadata_mysql.sql"
        mssql_ddl = documentation_folder + "metadata_mssql.sql"
        pg_done = documentation_folder + "pg_done"
        my_done = documentation_folder + "my_done"
        ora_done = documentation_folder + "ora_done"
        ms_done = documentation_folder + "ms_done"
        lite_done = documentation_folder + "lite_done"
        sqlite_db = "/tmp/" + folder + ".db"

        # TODO: Se her for datatyper: http://troels.arvin.dk/db/rdbms/#data_types
        mssql_repls = (
            (" timestamp", " datetime"),
            (" varchar(", " nvarchar("),
            ("  DEFERRABLE INITIALLY DEFERRED", "  ")            
            #    (" boolean", " varchar(5)"),
            #  (" bigint", " numeric"), #TODO: Ser ikke ut til at bigint kan ha desimaler i alle dbtyper
        )
        mssql_ddl_w = open(mssql_ddl, "w")
        # mssql_ddl_w.write(
        #     "SET ANSI_NULLS OFF; \n \n")
        with open(isosql_ddl, 'r') as file_r:
            for line in file_r:
                mssql_ddl_w.write(
                    reduce(lambda a, kv: a.replace(*kv), mssql_repls, line))

        oracle_repls = (
            (" text", " clob"),
            (" varchar(4000)", " clob"),
            (" varchar2(4000)", " clob"),
            (" varchar(", " varchar2("),
            # (" boolean", " varchar2(5)"),
        )
        oracle_ddl_w = open(oracle_ddl, "w")
        oracle_ddl_w.write(
            "ALTER SESSION SET NLS_LENGTH_SEMANTICS=CHAR; \n \n")
        with open(isosql_ddl, 'r') as file_r:
            for line in file_r:
                oracle_ddl_w.write(
                    reduce(lambda a, kv: a.replace(*kv), oracle_repls, line))

        # mysql_repls = (
        #     (" timestamp", " datetime"),
        #     (" varchar(4000)", " text"),            
        #     ("  DEFERRABLE INITIALLY DEFERRED", "  ")
        # )
        # mysql_ddl_w = open(mysql_ddl, "w")
        # with open(isosql_ddl, 'r') as file_r:
        #     for line in file_r:
        #         mysql_ddl_w.write(
        #             reduce(lambda a, kv: a.replace(*kv), mysql_repls, line))


        order_list = []
        with open(import_order_file) as file:
            for cnt, line in enumerate(file):
                order_list.append(line.rstrip())

        # db_list = ['postgresql','mysql','oracle','mssql','sqlite']   
        # db_dict = {}      
        # for db in db_list:
        #     db_dict.update({db: get_table_deps(table_name, table_def, deps_dict)})   
         
        # TODO: Flytt øverst når testet
        def generate_import(db_name, done_file, schema):
            import_list = []
            for table in order_list:
                import_str = 'WbImport -ifNotDefined=' + done_file + ' -schema=' + schema + ' -file=' + sub_data_folder + table + '.tsv' + ' -table=' + table + " -type=text -extension=tsv -mode=insert -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=true -trimValues=false -showProgress=10000;"
                import_list.append(import_str)
                # print(cmd)    
            return '\n'.join(import_list)     

        db_dict =   {
                    'postgresql': [
                        '-url="jdbc:postgresql://localhost:5432/" -username="postgres" -password="P@ssw0rd";',
                        'DROP SCHEMA IF EXISTS pwb CASCADE; COMMIT; CREATE SCHEMA pwb; COMMIT; SET search_path TO pwb;',
                        pg_done,
                        isosql_ddl,
                        'DROP SCHEMA pwb CASCADE; COMMIT;',
                        'pwb'
                        ],
                    # 'mysql': [
                    #     '-url="jdbc:mysql://localhost:3306?zeroDateTimeBehavior=CONVERT_TO_NULL&serverTimezone=UTC" -username="root" -password="P@ssw0rd";',
                    #     'DROP DATABASE IF EXISTS pwb; CREATE DATABASE pwb; ALTER DATABASE pwb CHARACTER SET = utf8mb4 COLLATE = utf8mb4_da_0900_as_cs; USE pwb; RESET MASTER;',
                    #     my_done,
                    #     mysql_ddl,
                    #     'DROP DATABASE pwb;',
                    #     'pwb'
                    #     ],   
                    'oracle': [
                        '-url="jdbc:oracle:thin:@127.0.1.1:1521/XE" -username="oracle" -password="pwb";',
                        'WbInclude -ifNotDefined=ora_done -file="../PWB/ora_schema_reset.sql" -displayResult=true -verbose=true -continueOnError=false;',
                        ora_done,
                        oracle_ddl,
                        'WbInclude -ifNotDefined=ora_done -file="../PWB/ora_schema_reset.sql" -displayResult=true -verbose=true -continueOnError=false; COMMIT;',
                        'oracle'
                        ],  
                    'mssql': [
                        '-url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true;',
                        'DROP DATABASE IF EXISTS pwb; CREATE DATABASE pwb; WbDisconnect; WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433;databaseName=pwb" -username="sa" -password="P@ssw0rd" -autocommit=false;',
                        ms_done,
                        mssql_ddl,
                        'WbDisconnect; WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true; DROP SCHEMA pwb CASCADE;',
                        'pwb'
                        ],                                           
                                         

                    # 'mssql': ['1','2'],
                    # 'sqlite': ['1','2']                                        
                    }    

        sql_list = []
        for db_name, db_list in db_dict.items():
            url = db_list[0]
            drop_before = db_list[1]
            done_file_path = db_list[2]
            done_file_name = os.path.basename(done_file_path)
            ddl = db_list[3]
            drop_after = db_list[4]
            schema = db_list[5]
            sql = [
                    '\n',
                    '--' + db_name,
                    'WbDisconnect;',
                    'WbConnect ' + url,
                    'WbSysExec touch ' + done_file_path + ';',
                    'WbVarDef -contentFile=' + done_file_path + ' -variable=' + done_file_name + ';',
                    drop_before,
                    'WbInclude -ifNotDefined=' + done_file_name + ' -file=' + ddl + ' -displayResult=true -verbose=true -continueOnError=false; COMMIT;', 
                     generate_import(db_name, done_file_name, schema),
                    drop_after,
                    'WbSysExec echo "done" > ' + done_file_path + ';',
                    'WbDisconnect;'  
                    '\n'
            ]
            sql_list.append('\n'.join(sql))
        print('\n'.join(sql_list))
                



                

        # sql = [
        #     "-- SQL Server 2019",
        #     "WbDisconnect;",
        #     'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true;',
        #     "DROP DATABASE IF EXISTS pwb; CREATE DATABASE pwb;",
        #     "WbDisconnect;",
        #     'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433;databaseName=pwb" -username="sa" -password="P@ssw0rd" -autocommit=false;',
        #     "WbSysExec touch '" + ms_done + "';",
        #     "WbVarDef -contentFile='" + ms_done + "' -variable=ms_done;",
        #     "WbInclude -ifNotDefined=ms_done -file='"
        #     + mssql_ddl
        #     + "' -displayResult=true -verbose=true -continueOnError=false;",
        #     "WbImport -ifNotDefined=ms_done -type=text -extension=tsv -mode=insert -sourceDir='"
        #     + sub_systems_path
        #     + folder
        #     + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema=dbo -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=true -trimValues=false -showProgress=10000;",
        #     "WbDisconnect;",
        #     'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true;',
        #     "DROP DATABASE IF EXISTS pwb;",
        #     "WbSysExec echo 'done' > '" + ms_done + "';",
        #     "WbDisconnect;",
        #     "\n",
        #     "-- SQLite 3.27",
        #     "WbDisconnect;",
        #     # 'WbConnect -url="jdbc:sqlite::memory:" -username="" -password="" -driverjar="../bin/sqlite-jdbc-3.27.2.1.jar" -driver=org.sqlite.JDBC;',
        #     "WbSysExec rm '" + sqlite_db + "' 2> /dev/null;",
        #     'WbConnect -url="jdbc:sqlite:' + sqlite_db + \
        #     '"  -username="" -password="" -driverjar="../bin/sqlite-jdbc-3.27.2.1.jar" -driver=org.sqlite.JDBC;',
        #     "WbSysExec touch '" + lite_done + "';",
        #     "WbVarDef -contentFile='" + lite_done + "' -variable=lite_done;",
        #     "WbInclude -ifNotDefined=lite_done -file='"
        #     + isosql_ddl
        #     + "' -displayResult=true -verbose=true -continueOnError=false;",
        #     "WbImport -ifNotDefined=lite_done -type=text -extension=tsv -mode=insert -sourceDir='"
        #     + sub_systems_path
        #     + folder
        #     + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema= -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=true -trimValues=false -showProgress=10000;",
        #     "WbSysExec echo 'done' > '" + lite_done + "';",
        #     "WbDisconnect;",
        # ]
        with open(sql_file, "a+") as file:
            file.write("\n".join(sql_list))
