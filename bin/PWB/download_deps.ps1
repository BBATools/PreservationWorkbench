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

# Download SQL Workbench J
$url= "https://www.sql-workbench.eu/Workbench-Build125.zip"
$filename = [System.IO.Path]::GetFileName($url); 
Write-Host "Downloading $filename (approx. 6MB)"
Invoke-WebRequest -Uri $url -OutFile $filename
Write-Host "Extracting $filename  to $binPath"
Expand-Archive $filename -DestinationPath $binPath

# Download Python
$url= "https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip"
$pythonPath = [IO.Path]::Combine($binPath, 'python')
New-Item -ItemType Directory -Force -Path $pythonPath 
$filename = [System.IO.Path]::GetFileName($url); 
Write-Host "Downloading $filename (approx. 7MB)"
Invoke-WebRequest -Uri $url -OutFile $filename
Write-Host "Extracting $filename  to $binPath"
Expand-Archive $filename -DestinationPath $pythonPath

# Download wimlib
$url= "https://wimlib.net/downloads/wimlib-1.13.1-windows-x86_64-bin.zip"
$filename = [System.IO.Path]::GetFileName($url); 
Write-Host "Downloading $filename (approx. 1MB)"
Invoke-WebRequest -Uri $url -OutFile $filename
Write-Host "Extracting $filename  to $binPath"
Expand-Archive $filename -DestinationPath $PSScriptRoot

#Download JRE
$url= "https://api.adoptopenjdk.net/v2/binary/releases/openjdk11?openjdk_impl=hotspot&os=windows&arch=x64&release=latest&type=jre"
$fUrl = Get-RedirectedUrl $url
$filename = [System.IO.Path]::GetFileName($fUrl); 
Write-Host "Downloading $filename (approx. 40MB)"
Invoke-WebRequest -Uri $url -OutFile $filename
Write-Host "Extracting JDK to $PSScriptRoot"
Expand-Archive $filename -DestinationPath $binPath

#Cleanup
Get-ChildItem -Path $PSScriptRoot | ?{ $_.PSIsContainer } | foreach { Remove-Item -Path $_.FullName -Recurse -Force -Confirm:$false}
Get-ChildItem -Path $PSScriptRoot\* -include *.txt,*.cmd | foreach { Remove-Item -Path $_.FullName }
Get-ChildItem -Path $binPath\* -include *.ps1,*.cmd,*.sample,*.sh,*-sample.xml,*.vbs,*.exe,*.zip,*.pdf | foreach { Remove-Item -Path $_.FullName }
$pythonExe = [IO.Path]::Combine($pythonPath, 'python.exe')
Rename-Item -Path $pythonExe -NewName "python3.exe"
$jdkDir = Get-ChildItem $binPath | Where-Object {$_.name -like "jdk-*"} | Select-Object -First 1
Rename-Item $jdkDir jre
