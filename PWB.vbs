Dim WshShell
set WshShell = WScript.CreateObject("WScript.Shell" )
set FSO = WScript.CreateObject("Scripting.FileSystemObject")

wbpath = Left(WScript.ScriptFullName, Len(WScript.ScriptFullName) - Len(WScript.ScriptName)) & "bin\"
WshShell.CurrentDirectory = wbpath
javaPath = wbpath & "jre\bin\javaw.exe"

If Not FSO.FolderExists(wbpath & "/tmp") Then
	Set objFolder = FSO.CreateFolder(wbpath & "/tmp")
End If 

configFile="tmp\pwb.ini"
Set objFile = FSO.OpenTextFile(configFile, 2, True)
objFile.WriteLine "[ENV]"
objFile.WriteLine "py_path=" & wbpath & "python" 
objFile.WriteLine "os="
objFile.WriteLine "pwb_path=" & wbpath & "PWB"
objFile.Close

set args = WScript.Arguments
jarpath = wbpath & "sqlworkbench.jar" 

javaCmd = chr(34) & javaPath & chr(34) & " -jar " & chr(34) & jarpath & chr(34) & " -url=jdbc:h2:mem:PWB -password=""" & chr(34) & " -configDir=" & chr(34) & wbpath
if (args.length > 0) then
	for each arg in args
    	javaCmd = javaCmd & " " & arg
  	next
end if

If FSO.FileExists(jarpath) And FSO.FileExists(javaPath) Then
	' WScript.Echo javaCmd
	retValue = WshShell.Run(javaCmd, 0, false)
	Set WshShell = Nothing
else
	Answer = _
 		Msgbox("Missing dependencies! Download now?", vbYesNo+vbCritical, "PWB Installer")
	If Answer = vbYes Then
		WshShell.run("powershell -executionpolicy bypass -noexit -file PWB/download_deps.ps1")
	End If
End If

