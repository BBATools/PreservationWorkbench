function Get-RedirectedUrl
{
    Param (
        [Parameter(Mandatory=$true)]
        [String]$URL
    )

    $request = [System.Net.WebRequest]::Create($url)
    $request.AllowAutoRedirect=$false
    $response=$request.GetResponse()

    If ($response.StatusCode -eq "Found")
    {
        $response.GetResponseHeader("Location")
    }
}

[Net.ServicePointManager]::SecurityProtocol = "tls12, tls11, tls"
$binPath = (get-item $PSScriptRoot).parent.FullName
$pythonPath = [IO.Path]::Combine($binPath, 'python')

# Download SQL Workbench J
$wbTestPath = [IO.Path]::Combine($binPath, 'sqlworkbench.jar')
If (-Not (Test-Path $wbTestPath)) {
	$url= "https://www.sql-workbench.eu/Workbench-Build125.zip"
	$filename = [System.IO.Path]::GetFileName($url); 
	Write-Host "Downloading $filename (approx. 6MB)"
	Invoke-WebRequest -Uri $url -OutFile $filename
	Write-Host "Extracting $filename  to $binPath"
	Expand-Archive $filename -DestinationPath $binPath
}

# Download Python
$pythonTestPath = [IO.Path]::Combine($binPath, 'python','python.exe')
If (-Not (Test-Path $pythonTestPath)) {
	$url= "https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip"
	New-Item -ItemType Directory -Force -Path $pythonPath 
    $filename = [System.IO.Path]::GetFileName($url); 
    Write-Host "Downloading $filename (approx. 7MB)"
    Invoke-WebRequest -Uri $url -OutFile $filename
    Write-Host "Extracting $filename  to $binPath"
    Expand-Archive $filename -DestinationPath $pythonPath
    #Fix python path
    $pthFile = [IO.Path]::Combine($pythonPath, 'python36._pth')
    $text = [string]::Join("`n", (Get-Content $pthFile))
	[regex]::Replace($text, "\.`n", ".`n..\PWB`n", "Singleline") | Set-Content $pthFile
}

# Download wimlib
$wimlibTestPath = [IO.Path]::Combine($binPath, 'PWB','wimlib-imagex.exe')
If (-Not (Test-Path $wimlibTestPath)) {
    $url= "https://wimlib.net/downloads/wimlib-1.13.1-windows-x86_64-bin.zip"
    $filename = [System.IO.Path]::GetFileName($url); 
    Write-Host "Downloading $filename (approx. 1MB)"
    Invoke-WebRequest -Uri $url -OutFile $filename
    Write-Host "Extracting $filename  to $binPath"
    Expand-Archive $filename -DestinationPath $PSScriptRoot
}

#Download JRE
$url= "https://api.adoptopenjdk.net/v2/binary/releases/openjdk11?openjdk_impl=hotspot&os=windows&arch=x64&release=latest&type=jre"
$fUrl = Get-RedirectedUrl $url
$filename = [System.IO.Path]::GetFileName($fUrl); 
Write-Host "Downloading $filename (approx. 40MB)"
Invoke-WebRequest -Uri $url -OutFile $filename
Write-Host "Extracting JDK to $PSScriptRoot"
Expand-Archive $filename -DestinationPath $binPath

#Cleanup
Get-ChildItem -Path $PSScriptRoot -exclude appJar | ?{ $_.PSIsContainer } | foreach { Remove-Item -Path $_.FullName -Recurse -Force -Confirm:$false}
Get-ChildItem -Path $PSScriptRoot\* -include *.txt,*.cmd | foreach { Remove-Item -Path $_.FullName }
Get-ChildItem -Path $binPath\* -include *.ps1,*.cmd,*.sample,*.sh,*-sample.xml,*.vbs,*.exe,*.zip,*.pdf | foreach { Remove-Item -Path $_.FullName }
$pythonExe = [IO.Path]::Combine($pythonPath, 'python.exe')
If (Test-Path $pythonExe) {Rename-Item -Path $pythonExe -NewName "python3.exe"}
