Preservation Workbench (PWB) implements the features we need to extract data from systems and generate a data package suitable for long time storage. 
PWB is implemented on top of SQL Workbench/J (installed as dependency): https://www.sql-workbench.eu/

Some features are only available when installed as part of Arkimint: https://github.com/BBATools/Arkimint


### Install instructions (extract and verify features only):

##### Windows:
Download this repo as zip or git clone.
Run or click *PWB.vbs* which will download any missing dependencies on first run.
Run or click *PWB.vbs* again after install has finished to run the program.

Many database drivers are available as part of the install, but for licensing reasons Oracle drivers are not included. Download ojdbc10.jar from here https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html
and add to the PreservationWorkbench\bin directory.

The resulting *PreservationWorkbench* directory can be used as a portable app: 
https://en.wikipedia.org/wiki/Portable_application


##### Linux:
Portable generic Linux install will be made available after we switch to a custom SQL Workbench/J build with jlink:
https://docs.oracle.com/javase/9/tools/jlink.htm 



### Usage:
Start SQL Workbench/J with  *PWB.vbs* (Windows) or  *PWB.sh* (Linux).
PWB specific features are started via macros and are thus found under the *Macros* menu. 
##### Extract:
*Extract data from database and/or disk.*
If database export, Use *File->Connect window* first to connect to database/schema.
Use *Export to Disk* once per database schema (and any files on disk that are connected to schema) *or* (if no database) any collection of files on disk that constitute a separate part of the system.
Use *Create System Data Package* when all parts of the system have been extracted to package the data as one data package (packaged as a wim file to retain file metadata) and generate checksum. 

##### Verify:
*Verify checksum and make backup of raw SIP before processing.*
##### Dispose:
*Dispose/remove parts of the extracted data that has no archival value*
WIP

##### Process:
*Normalize documents and metadata. Generate AIP.*

##### Other:
SQL Workbench/J standard features are described here: 
https://www.sql-workbench.eu/manual/workbench-manual.html
