Dim WshShell
set WshShell = WScript.CreateObject("WScript.Shell" )
set FSO = WScript.CreateObject("Scripting.FileSystemObject")

wbpath = Left(WScript.ScriptFullName, Len(WScript.ScriptFullName) - Len(WScript.ScriptName)) & "bin\"
WshShell.CurrentDirectory = wbpath
javaPath = wbpath & "jre\bin\javaw.exe"

If Not FSO.FolderExists(wbpath & "\tmp") Then
	Set objFolder = FSO.CreateFolder(wbpath & "\tmp")
End If

configFile="tmp\pwb.ini"
if (FSO.FileExists(configFile)) then
   FSO.DeleteFile(configFile)
end if

Set objFile = FSO.OpenTextFile(configFile, 2, True)
objFile.WriteLine "[ENV]"
objFile.WriteLine "py_path=" & wbpath & "python"
objFile.WriteLine "os="
objFile.WriteLine "pwb_path=" & wbpath & "PWB"
objFile.Close

set args = WScript.Arguments
jarpath = wbpath & "sqlworkbench.jar"

javaCmd = chr(34) & javaPath & chr(34) & " -Xmx6g -jar " & chr(34) & jarpath & chr(34) & " -url=jdbc:h2:mem:PWB -password=""" & chr(34) & " -configDir=" & chr(34) & wbpath
if (args.length > 0) then
	for each arg in args
    	javaCmd = javaCmd & " " & arg
  	next
end if

wkspPath = wbpath & "Default.wksp"
If Not FSO.FileExists(wkspPath) Then
	FSO.CopyFile wbpath & "PWB\sqlwb\Default.wksp" , wkspPath
End If

settingsPath = wbpath & "workbench.settings"
If Not FSO.FileExists(settingsPath) Then
	FSO.CopyFile wbpath & "PWB\sqlwb\workbench_win.settings" , settingsPath
End If

pythonPath = wbpath & "python\python3.exe"
wimPath = wbpath & "PWB\wimlib-imagex.exe"
If (FSO.FileExists(jarpath) And FSO.FileExists(javaPath) And FSO.FileExists(pythonPath) And FSO.FileExists(wimPath)) Then
	Set jreFolder = FSO.GetFolder(wbpath & "\jre")
	For Each Subfolder in jreFolder.SubFolders
		On Error Resume Next
		If instr(Subfolder.Name, "jdk-") = 1 Then
			Set folder = FSO.GetFolder(Subfolder.Path)
			folder.Delete [True]
			Exit For
		End If
	Next
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



