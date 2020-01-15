DECLARE @DatabaseName nvarchar(50)
SET @DatabaseName = N'pwb'

DECLARE @SQL varchar(max)

SELECT @SQL = COALESCE(@SQL,'') + 'Kill ' + Convert(varchar, SPId) + ';'
FROM MASTER..SysProcesses
WHERE DBId = DB_ID(@DatabaseName) AND SPId <> @@SPId

EXEC(@SQL)

DROP DATABASE IF EXISTS pwb;
CREATE DATABASE pwb;
