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
tmp_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'tmp'))
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
    if os.path.isdir(os.path.join(os.path.abspath(sub_systems_path), folder)):
        documentation_folder = sub_systems_path + folder + "/documentation/"
        isosql_ddl = documentation_folder + "metadata.sql"
        oracle_ddl = documentation_folder + "metadata_oracle.sql"
        mysql_ddl = documentation_folder + "metadata_mysql.sql"
        mssql_ddl = documentation_folder + "metadata_mssql.sql"
        pg_done = documentation_folder + "pg_done"
        my_done = documentation_folder + "my_done"
        ora_done = documentation_folder + "ora_done"
        ms_done = documentation_folder + "ms_done"
        lite_done = documentation_folder + "lite_done"
        sqlite_db = "/tmp/sqlite_test.db"

        # TODO: Se her for datatyper: http://troels.arvin.dk/db/rdbms/#data_types
        mssql_repls = ((" timestamp", " datetime"),
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
        mssql_ddl_w.close()

        oracle_repls = ((" text", " clob"),
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
        oracle_ddl_w.close()

        mysql_repls = ((" timestamp", " datetime"),
                       )
        mysql_ddl_w = open(mysql_ddl, "w")
        with open(isosql_ddl, 'r') as file_r:
            for line in file_r:
                mysql_ddl_w.write(
                    reduce(lambda a, kv: a.replace(*kv), mysql_repls, line))
        mysql_ddl_w.close()

        sql = [
            "\n",
            "-- PostgreSQL 12",
            "WbDisconnect;",
            'WbConnect -url="jdbc:postgresql://localhost:5432/" -username="postgres" -password="bba";',
            "DROP SCHEMA IF EXISTS postgresql_test CASCADE; COMMIT; CREATE SCHEMA postgresql_test; COMMIT; SET search_path TO postgresql_test;",
            "WbSysExec touch '" + pg_done + "';",
            "WbVarDef -contentFile='" + pg_done + "' -variable=pg_done;",
            "WbInclude -ifNotDefined=pg_done -file='"
            + isosql_ddl
            + "' -displayResult=true -verbose=true -continueOnError=false;",
            "COMMIT;",
            "WbEcho 'Processing PostgreSQL...';",
            "WbImport -ifNotDefined=pg_done -type=text -extension=tsv -mode=insert -sourceDir='"
            + sub_systems_path
            + folder
            + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema=postgresql_test -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=false -trimValues=false -showProgress=10000;",
            "DROP SCHEMA postgresql_test CASCADE; COMMIT;",
            "WbSysExec echo 'done' > '" + pg_done + "';",
            "WbDisconnect;",
            "\n",
            "-- MySQL 8.0",
            "WbDisconnect;",
            'WbConnect -url="jdbc:mysql://localhost:3306?zeroDateTimeBehavior=CONVERT_TO_NULL&serverTimezone=UTC" -username="root" -password="root";',
            "DROP DATABASE IF EXISTS MySQL_test; CREATE DATABASE MySQL_test; ALTER DATABASE MySQL_test CHARACTER SET = utf8mb4 COLLATE = utf8mb4_da_0900_as_cs; USE MySQL_test;",
            "RESET MASTER;"
            "WbSysExec touch '" + my_done + "';",
            "WbVarDef -contentFile='" + my_done + "' -variable=my_done;",
            "WbInclude -ifNotDefined=my_done -file='"
            + mysql_ddl
            + "' -displayResult=true -verbose=true -continueOnError=false;",
            "WbEcho 'Processing MySQL...';",
            "WbImport -ifNotDefined=my_done -type=text -extension=tsv -mode=insert -sourceDir='"
            + sub_systems_path
            + folder
            + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema=MySQL_test -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=false -trimValues=false -showProgress=10000;",
            # "DROP DATABASE MySQL_test;", #TODO: Fjern utkommentering etter demo i Trondheim. Behold pg heller da
            "WbSysExec echo 'done' > '" + my_done + "';",
            "WbDisconnect;",
            "\n",
            "-- Oracle 11.2",
            "WbDisconnect;",
            'WbConnect -url="jdbc:oracle:thin:@127.0.1.1:1521/XE" -username="oracle_test" -password="oracle_test";',
            "WbSysExec touch '" + ora_done + "';",
            "WbVarDef -contentFile='" + ora_done + "' -variable=ora_done;",
            "WbInclude -ifNotDefined=ora_done -file='../PWB/ora_schema_reset.sql' -displayResult=true -verbose=true -continueOnError=false;",
            "WbInclude -ifNotDefined=ora_done -file='"
            + oracle_ddl
            + "' -displayResult=true -verbose=true -continueOnError=false;",
            "WbEcho 'Processing Oracle...';",
            "WbImport -ifNotDefined=ora_done -type=text -extension=tsv -mode=insert -sourceDir='"
            + sub_systems_path
            + folder
            + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema=oracle_test -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=false -trimValues=false -showProgress=10000;",
            "WbInclude -ifNotDefined=ora_done -file='../PWB/ora_schema_reset.sql' -displayResult=true -verbose=true -continueOnError=false;",
            "WbSysExec echo 'done' > '" + ora_done + "';",
            "WbDisconnect;",
            "\n",
            "-- SQL Server 2019",
            "WbDisconnect;",
            'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true;',
            "DROP DATABASE IF EXISTS MSSQLServer_test; CREATE DATABASE MSSQLServer_test;",
            "WbDisconnect;",
            'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433;databaseName=MSSQLServer_test" -username="sa" -password="Hp3tusen1" -autocommit=false;',
            "WbSysExec touch '" + ms_done + "';",
            "WbVarDef -contentFile='" + ms_done + "' -variable=ms_done;",
            "WbInclude -ifNotDefined=ms_done -file='"
            + mssql_ddl
            + "' -displayResult=true -verbose=true -continueOnError=false;",
            "WbEcho 'Processing SQL Server...';",
            "WbImport -ifNotDefined=ms_done -type=text -extension=tsv -mode=insert -sourceDir='"
            + sub_systems_path
            + folder
            + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema=dbo -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=false -trimValues=false -showProgress=10000;",
            "WbDisconnect;",
            'WbConnect -url="jdbc:sqlserver://localhost\\SQLEXPRESS:1433" -username="sa" -password="P@ssw0rd" -autocommit=true;',
            "DROP DATABASE IF EXISTS MSSQLServer_test;",
            "WbSysExec echo 'done' > '" + ms_done + "';",
            "WbDisconnect;",
            "\n",
            "-- SQLite 3.27",
            "WbDisconnect;",
            # jdbc:sqlite:/home/bba/SQLite_test.db
            # 'WbConnect -url="jdbc:sqlite::memory:" -username="" -password="" -driverjar="../bin/sqlite-jdbc-3.27.2.1.jar" -driver=org.sqlite.JDBC;',
            "WbSysExec rm '" + sqlite_db + "' 2> /dev/null;",
            'WbConnect -url="jdbc:sqlite:' + sqlite_db + \
            '"  -username="" -password="" -driverjar="../bin/sqlite-jdbc-3.27.2.1.jar" -driver=org.sqlite.JDBC;',
            "WbSysExec touch '" + lite_done + "';",
            "WbVarDef -contentFile='" + lite_done + "' -variable=lite_done;",
            "WbInclude -ifNotDefined=lite_done -file='"
            + isosql_ddl
            + "' -displayResult=true -verbose=true -continueOnError=false;",
            "WbEcho 'Processing SQLite...';",
            "WbImport -ifNotDefined=lite_done -type=text -extension=tsv -mode=insert -sourceDir='"
            + sub_systems_path
            + folder
            + "/content/data' -skipTargetCheck=true -checkDependencies=true -useSavepoint=false -continueOnError=false -ignoreIdentityColumns=false -schema= -delimiter=\\t -decimal='.' -encoding=UTF8 -header=true -deleteTarget=false -booleanToNumber=false -adjustSequences=false -createTarget=false -emptyStringIsNull=false -trimValues=false -showProgress=10000;",
            "WbSysExec echo 'done' > '" + lite_done + "';",
            "WbDisconnect;",
        ]
        with open(sql_file, "a+") as file:
            file.write("\n".join(sql))
