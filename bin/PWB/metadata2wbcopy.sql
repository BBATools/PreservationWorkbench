WbXslt -ifNotEmpty=db_args
-inputfile=../_DATA/$[sys_name]/content/sub_systems/$[subsys_name]/header/metadata.xml
-stylesheet=PWB/metadata2wbcopy.xslt
-xsltOutput=tmp/wbcopy.sql;