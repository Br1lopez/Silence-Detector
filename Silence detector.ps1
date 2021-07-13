cd $PSScriptRoot
Get-ChildItem *.lnk | ForEach {
$link = $_.Name
$sh = New-Object -COM WScript.Shell
$videopath = $sh.CreateShortcut($link).TargetPath

.\..\ffmpeg.exe -i $videopath -af silencedetect=noise=-26dB:d=3.5 -f null - 2>&1 | tee silences_raw.txt

python EDLcreator.py -p $videopath
Remove-Item silences_raw.txt
Remove-Item $_.Name
}
[console]::beep(1600,200)
[console]::beep(800,400)
