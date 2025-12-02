
# Activer le venv
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvActivate = Join-Path $scriptPath ".venv\Scripts\Activate.ps1"
& $venvActivate

# Définir les paramètres
$pythonScript = Join-Path $scriptPath "scrap_last_week.py"
$logFile = Join-Path $scriptPath "execution_log.txt"
$recipient = "bcoulet@rtm.fr"
$from = "bcoulet@rtm.fr"
$smtpServer = "mail.rtm.fr"   # ou emt.rtm.fr
$subject = "Rapport d'exécution : scrap_last_week.py"

# Mesurer le temps
$startTime = Get-Date
$status = "Succès"

try {
    python $pythonScript
} catch {
    $status = "Échec"
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# Créer le log
$logContent = @"
Nom du script : $pythonScript
Début : $startTime
Fin : $endTime
Durée : $duration secondes
Statut : $status
"@
$logContent | Out-File -FilePath $logFile -Encoding UTF8

# Authentification SMTP
$securePassword = ConvertTo-SecureString "TON_MOT_DE_PASSE" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($from, $securePassword)

# Envoyer le mail avec pièce jointe
Send-MailMessage -To $recipient -From $from -Subject $subject -Body $logContent -Attachments $logFile -SmtpServer $smtpServer -Credential $credential -UseSsl

# Fermer PowerShell
exit
