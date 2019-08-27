Preservation Workbench (PWB) implements the features we need to extract data from systems and generate a data package suitable for long time storage. 
PWB is implemented on top of SQL Workbench/J: https://www.sql-workbench.eu/

Some features are only available when installed as part of Arkimint: https://github.com/BBATools/Arkimint


### Install instructions (extract and verify features only):

##### Windows:
Download this repo as zip or git clone.
Run or click *PWB.vbs* which will download any missing dependencies on first run.
Run or click *PWB.vbs* again after install has finished to run the program.

Many database drivers are available as part of the install, but for licensing reasons Oracle drivers are not included. Download ojdbc10.jar from here https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html
and add to the PreservationWorkbench\bin directory.


##### Linux:
Installer under construction.



### Usage:
Start SQL Workbench/J with  *PWB.vbs* (Windows) or  *PWB.sh* (Linux).
PWB specific features are started via macros and are thus found under the *Macros* menu. 
#### Extract:
*Extract data from database and/or files.*
If database export, Use *File->Connect window* first to connect to database/schema.
Use *Export to Disk* once per database schema (and any files on disk that are connected to schema) *or* (if only files on disk) any files on disk that constitute a separate part of the system.
Use *Create System Data Package* when all parts of the system have been extracted to package the data as a singular data package and generate checksum. 
#### Verify:
*Verify checksum and make backup of raw SIP before processing.*
#### Dispose:
*Dispose/remove parts of the extracted data that has no archival value*
WIP
#### Process:
*Normalizes documents and metadata. Generates AIP.*
#### Other:
SQL Workbench/J standard features are described here: 
https://www.sql-workbench.eu/manual/workbench-manual.html
