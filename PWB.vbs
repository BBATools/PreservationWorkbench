Dim WshShell
set WshShell = WScript.CreateObject("WScript.Shell" )
set FSO = WScript.CreateObject("Scripting.FileSystemObject")

wbpath = Left(WScript.ScriptFullName, Len(WScript.ScriptFullName) - Len(WScript.ScriptName)) & "bin\"
WshShell.CurrentDirectory = wbpath
javaPath = wbpath & "jre\bin\javaw.exe"

pyPathFile="tmp\pypath"
pwbPathFile="tmp\pwbpath" 
Set objFile = FSO.CreateTextFile(pyPathFile,True)
' objFile.Write chr(34) & wbpath & "python\python3" & chr(34) & vbCrLf
objFile.Write wbpath & "python\" 
objFile.Close
Set objFile = FSO.CreateTextFile(pwbPathFile,True)
' objFile.Write chr(34) & wbpath & "PWB\" & chr(34) & vbCrLf
objFile.Write wbpath & "PWB\"
objFile.Close

set args = WScript.Arguments
jarpath = wbpath & "sqlworkbench.jar" 
javaCmd = chr(34) & javaPath & chr(34) & " -jar " & chr(34) & jarpath & chr(34) & " -url=jdbc:h2:mem:PWB -password=""" & chr(34) & " -configDir=" & chr(34) & wbpath

if (args.length > 0) then
  for each arg in args
    javaCmd = javaCmd & " " & arg
  next
end if

' WScript.Echo javaCmd
retValue = WshShell.Run(javaCmd, 0, false)
Set WshShell = Nothing

