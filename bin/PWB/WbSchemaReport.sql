
WbSchemaReport 
-file=../../_DATA/$[sys_name]/content/sub_systems/$[subsys_name]/header/metadata.xml
-schemas=$[db_schema] 
-types=SYNONYM,TABLE,VIEW
-includeProcedures=true
-includeTriggers=true
-writeFullSource=true;
