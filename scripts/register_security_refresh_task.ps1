$pythonPath = "C:\Python313\python.exe"
$scriptPath = "D:\gemini\scripts\refresh_security_sources.py"
$taskName = "SSP-SecurityRefresh"
$description = "Quantum Safety data refresh"

$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath
$trigger = New-ScheduledTaskTrigger -Daily -At 03:00
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description $description -Force

Write-Host "Registered $taskName to run $scriptPath daily at 03:00."
