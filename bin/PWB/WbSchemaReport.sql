
WbSchemaReport 
-file=../../_DATA/$[SystemName]/content/sub_systems/$[SubSystemName]/header/metadata.xml
-schemas=$[DatabaseSchema] 
-types=SYNONYM,TABLE,VIEW
-includeProcedures=true
-includeTriggers=true
-writeFullSource=true;
