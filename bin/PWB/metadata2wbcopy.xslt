<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:wb-name-util="workbench.sql.NameUtil"
                xmlns:wb-string-util="workbench.util.StringUtil"
                xmlns:wb-sql-util="workbench.util.SqlUtil">

<xsl:output
  encoding="iso-8859-15"
  method="text"
  indent="no"
  standalone="yes"
  omit-xml-declaration="yes"
/>

  <xsl:param name="makeLowerCase">false</xsl:param>

  <xsl:strip-space elements="*"/>
  <xsl:variable name="quote">
    <xsl:text>"</xsl:text>
  </xsl:variable>
  <xsl:variable name="newline">
    <xsl:text>&#10;</xsl:text>
  </xsl:variable>
  <xsl:variable name="backtick">
    <xsl:text>&#96;</xsl:text>
  </xsl:variable>

  <xsl:template match="/">

    <xsl:apply-templates select="/schema-report/table-def"/>

    <xsl:apply-templates select="/schema-report/sequence-def">
      <xsl:with-param name="definition-part" select="'owner'"/>
    </xsl:apply-templates>

    <xsl:value-of select="$newline"/>
  </xsl:template>

  <xsl:template match="table-def">

    <xsl:variable name="tablename">
      <xsl:call-template name="write-object-name">
        <xsl:with-param name="objectname" select="table-name"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:text>WbCopy -ifNotEmpty=db_args -targetConnection=$[TargetCon] -mode=INSERT -ignoreIdentityColumns=false -removeDefaults=true -continueOnError=false -showProgress=10000 -targetSchema=PUBLIC -createTarget=true -targetTable="</xsl:text>
    <xsl:value-of select="$tablename"/> 
    <xsl:text>" -sourceQuery='SELECT</xsl:text>     

    <xsl:for-each select="column-def">
      <xsl:sort select="dbms-position" data-type="number"/>
      <xsl:variable name="colname">
        <xsl:call-template name="write-object-name">
          <xsl:with-param name="objectname" select="column-name"/>
        </xsl:call-template>
      </xsl:variable>

      <xsl:variable name="dbms-typename">
        <xsl:value-of select="wb-name-util:toLowerCase(dbms-data-type)"/>
      </xsl:variable>

      <xsl:text> "</xsl:text>
      <xsl:copy-of select="$colname"/>
      <xsl:if test="position() &lt; last()">
        <xsl:text>",</xsl:text>
      </xsl:if> 
    </xsl:for-each> 

    <xsl:text>" FROM "</xsl:text>
    <xsl:value-of select="$tablename"/>  
    <xsl:text>"';</xsl:text>    

    <xsl:value-of select="$newline"/>
    <xsl:for-each select="column-def">
      <xsl:sort select="column-name" data-type="number"/>
      <xsl:variable name="colname">
        <xsl:call-template name="write-object-name">
          <xsl:with-param name="objectname" select="column-name"/>
        </xsl:call-template>
      </xsl:variable>
    </xsl:for-each>

  </xsl:template>

  <xsl:template name="_replace_text">
    <xsl:param name="text"/>
    <xsl:param name="replace"/>
    <xsl:param name="by"/>
    <xsl:choose>
      <xsl:when test="contains($text, $replace)">
        <xsl:value-of select="substring-before($text, $replace)"/>
        <xsl:copy-of select="$by"/>
        <xsl:call-template name="_replace_text">
          <xsl:with-param name="text" select="substring-after($text, $replace)"/>
          <xsl:with-param name="replace" select="$replace"/>
          <xsl:with-param name="by" select="$by"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="write-object-name">
    <xsl:param name="objectname"/>
    <xsl:call-template name="_simple_cleanup">
        <xsl:with-param name="objectname" select="$objectname"/>
    </xsl:call-template>
  </xsl:template>

  <!--

  Functions available in SQL Workbench:

  cleanupIdentifier() will remove any special characters from the name so that it doesn't require quoting

  <xsl:variable name="tablename" select="wb-name-util:cleanupIdentifier(table-name, 'true')"/>
  <xsl:variable name="tablename" select="wb-name-util:cleanupIdentifier(table-name, $makeLowerCase)"/>

  The utility functions camelCaseToSnakeLower() or camelCaseToSnakeUpper() can be used
  to convert names from a case-preserving DBMS (e.g. SQL Server). OrderEntry would be converted to order_entry
  <xsl:variable name="tablename" select="wb-name-util:camelCaseToSnakeLower(table-name)"/>
  -->

  <xsl:template name="_cleanup-camel-case">
    <xsl:param name="identifier"/>
    <!-- remove any invalid characters first -->
    <xsl:variable name="clean-name" select="wb-name-util:cleanupIdentifier($identifier, 'false')"/>
    <xsl:value-of select="wb-name-util:camelCaseToSnakeLower($clean-name)"/>
  </xsl:template>

  <xsl:template name="_quote_if_needed">
    <xsl:param name="identifier"/>
    <xsl:value-of select="wb-name-util:quoteIfNeeded($identifier)"/>
  </xsl:template>

  <xsl:template name="_cleanup_identifier">
    <xsl:param name="identifier"/>
    <xsl:value-of select="wb-name-util:cleanupIdentifier($identifier, $makeLowerCase)"/>
  </xsl:template>

  <xsl:template name="_quote_mixed_case">
    <xsl:param name="identifier"/>
    <xsl:value-of select="wb-name-util:preserveCase($identifier)"/>
  </xsl:template>

  <!--
     use _simple_cleanup if this XSLT is run without SQL Workbench

     the other templates need to be removed in that case, because the presence
     of the referenced functions is tested when parsing the XSLT, not when running it
  -->
  <xsl:template name="_simple_cleanup">
    <xsl:param name="objectname"/>

    <xsl:variable name="lcletters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
    <xsl:variable name="ucletters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>

    <xsl:variable name="name-to-use">
      <xsl:choose>
        <xsl:when test="$makeLowerCase = 'true'">
          <xsl:value-of select="translate($objectname,$ucletters,$lcletters)"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$objectname"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="clean-name">
      <xsl:call-template name="_replace_text">
        <xsl:with-param name="text">
          <xsl:value-of select="$name-to-use"/>
        </xsl:with-param>
        <xsl:with-param name="replace" select="$backtick"/>
        <xsl:with-param name="by" select="''"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:choose>
      <xsl:when test="substring($clean-name,1,1) = $quote and substring($clean-name,string-length($clean-name),1) = $quote">
        <xsl:value-of select="$clean-name"/>
      </xsl:when>
      <!-- <xsl:when test="$quoteAllNames = 'true'">
        <xsl:text>"</xsl:text><xsl:value-of select="$name-to-use"/><xsl:text>"</xsl:text>
      </xsl:when> -->
      <xsl:when test="contains($clean-name,' ')">
        <xsl:value-of select="concat($quote, $clean-name, $quote)"/>
      </xsl:when>
      <xsl:when test="$objectname != $name-to-use and $makeLowerCase = 'false'">
        <xsl:text>"</xsl:text><xsl:value-of select="$objectname"/><xsl:text>"</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$clean-name"/>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>

</xsl:stylesheet>
