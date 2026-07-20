# =========================================================

#  Installation locale du MCP Pennylane pour Claude Desktop

#  Cabinet AS ONE AUDIT - Fork derfoj/pennylane-mcp-server

#  Mode MONO-DOSSIER : un token Pennylane different par poste/collaborateur

# =========================================================

#

# Usage (executer sur le poste du collaborateur) :

#   .\install_pennylane_mcp.ps1 -PennylaneApiToken "TOKEN_DU_COLLABORATEUR"

#

# -> Genere un token different par collaborateur dans Pennylane

#    (Parametres > Connectivite > Developpeurs > Company API Token)

#    et passe-le en parametre a chaque execution.

#

# Ce script :

#   1. Verifie Python (>= 3.11) et Git, et les installe via winget si absents

#   2. Clone (ou met a jour) le fork derfoj/pennylane-mcp-server

#   3. Cree un venv et installe le paquet (pip install -e .)

#   4. Ecrit le fichier .env avec PENNYLANE_API_TOKEN

#   5. Ajoute l'entree MCP dans claude_desktop_config.json (sans ecraser le reste)

#

# A FAIRE APRES : quitter Claude Desktop depuis la barre des taches

# (systray, clic droit > Quit), pas juste fermer la fenetre, puis rouvrir.

#

# NOTE : l'installation automatique de Python/Git necessite winget

# (present par defaut sur Windows 10/11 a jour) et peut demander

# les droits administrateur (une fenetre UAC peut s'afficher).

 

param(

    [Parameter(Mandatory=$true)]

    [string]$PennylaneApiToken,

 

    [string]$InstallDir = "C:\AS-ONE-MCP\pennylane-mcp-server",

 

    [string]$RepoUrl = https://github.com/derfoj/pennylane-mcp-server.git

)

 

$ErrorActionPreference = "Stop"

 

function Test-Winget {

    return [bool](Get-Command winget -ErrorAction SilentlyContinue)

}

 

function Install-Prerequisite {

    param(

        [string]$CommandName,

        [string]$WingetId,

        [string]$DisplayName

    )

 

    if (Get-Command $CommandName -ErrorAction SilentlyContinue) {

        Write-Host "OK : $DisplayName deja present." -ForegroundColor Green

        return

    }

 

    Write-Host "$DisplayName absent." -ForegroundColor Yellow

 

    if (-not (Test-Winget)) {

        Write-Host "ERREUR : winget n'est pas disponible sur ce poste, impossible d'installer $DisplayName automatiquement." -ForegroundColor Red

        Write-Host "-> Installe $DisplayName manuellement, puis relance ce script." -ForegroundColor Red

        exit 1

    }

 

    Write-Host "Installation de $DisplayName via winget (une fenetre UAC peut apparaitre)..." -ForegroundColor Cyan

    winget install --id $WingetId -e --source winget --accept-package-agreements --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {

        Write-Host "ERREUR : l'installation de $DisplayName via winget a echoue (code $LASTEXITCODE)." -ForegroundColor Red

        exit 1

    }

 

    # Rafraichir le PATH de la session courante avec les valeurs Machine + User

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

 

    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {

        Write-Host "$DisplayName vient d'etre installe mais n'est pas encore detecte dans cette fenetre PowerShell." -ForegroundColor Yellow

        Write-Host "-> Ferme cette fenetre PowerShell, rouvre-en une nouvelle, puis relance le script." -ForegroundColor Yellow

        exit 1

    }

 

    Write-Host "OK : $DisplayName installe avec succes." -ForegroundColor Green

}

 

function Resolve-PythonExe {

    # Sur beaucoup de PC, 'python' dans le PATH est en fait un raccourci

    # "App Execution Alias" de Microsoft Store (WindowsApps\python.exe) qui

    # ne fait qu'ouvrir le Store, meme si Python n'est pas installe.

    # On utilise donc en priorite le lanceur 'py' (installe par le vrai

    # installeur python.org / winget), qui n'est pas court-circuite par ce raccourci.

    if (Get-Command py -ErrorAction SilentlyContinue) {

        try {

            $exe = & py -3 -c "import sys; print(sys.executable)" 2>$null

            if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) {

                return $exe.Trim()

            }

        } catch {}

    }

 

    # Repli : 'python' direct, mais on ignore le raccourci WindowsApps

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue

    if ($pythonCmd -and $pythonCmd.Source -notmatch "WindowsApps") {

        try {

            $out = & python --version 2>&1

            if ($LASTEXITCODE -eq 0 -and $out -match "Python 3") {

                return $pythonCmd.Source

            }

        } catch {}

    }

 

    return $null

}

 

Write-Host "=== 1. Verification / installation des prerequis ===" -ForegroundColor Cyan

Install-Prerequisite -CommandName "git" -WingetId "Git.Git" -DisplayName "Git"

 

$pythonExe = Resolve-PythonExe

if (-not $pythonExe) {

    Write-Host "Python absent (ou seul le raccourci Microsoft Store est present)." -ForegroundColor Yellow

 

    if (-not (Test-Winget)) {

        Write-Host "ERREUR : winget n'est pas disponible sur ce poste, impossible d'installer Python automatiquement." -ForegroundColor Red

        Write-Host "-> Installe Python >= 3.11 manuellement (python.org), puis relance ce script." -ForegroundColor Red

        exit 1

    }

 

    Write-Host "Installation de Python via winget (une fenetre UAC peut apparaitre)..." -ForegroundColor Cyan

    winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {

        Write-Host "ERREUR : l'installation de Python via winget a echoue (code $LASTEXITCODE)." -ForegroundColor Red

        exit 1

    }

 

    # Rafraichir le PATH de la session courante avec les valeurs Machine + User

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

 

    $pythonExe = Resolve-PythonExe

    if (-not $pythonExe) {

        Write-Host "Python vient d'etre installe mais n'est pas encore detecte dans cette fenetre PowerShell." -ForegroundColor Yellow

        Write-Host "-> Ferme cette fenetre PowerShell, rouvre-en une nouvelle, puis relance le script." -ForegroundColor Yellow

        exit 1

    }

 

    Write-Host "OK : Python installe avec succes." -ForegroundColor Green

}

 

$pyVersionOutput = & $pythonExe --version

Write-Host "OK : git et python operationnels ($pyVersionOutput)" -ForegroundColor Green

Write-Host "    Python utilise : $pythonExe" -ForegroundColor DarkGray

 

Write-Host "`n=== 2. Clonage / mise a jour du repo ===" -ForegroundColor Cyan

if (Test-Path $InstallDir) {

    Write-Host "Dossier existant, on met a jour (git pull)..."

    Push-Location $InstallDir

    git pull

    Pop-Location

} else {

    New-Item -ItemType Directory -Path (Split-Path $InstallDir) -Force | Out-Null

    git clone $RepoUrl $InstallDir

}

 

Write-Host "`n=== 3. Creation du venv et installation du paquet ===" -ForegroundColor Cyan

Push-Location $InstallDir

& $pythonExe -m venv venv

$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"

$venvExe    = Join-Path $InstallDir "venv\Scripts\pennylane-mcp-server.exe"

 

if (-not (Test-Path $venvPython)) {

    Write-Host "ERREUR : la creation du venv a echoue, $venvPython introuvable." -ForegroundColor Red

    Pop-Location

    exit 1

}

 

& $venvPython -m pip install --upgrade pip

& $venvPython -m pip install -e .

 

if (-not (Test-Path $venvExe)) {

    Write-Host "ATTENTION : la commande 'pennylane-mcp-server' n'a pas ete generee dans le venv." -ForegroundColor Yellow

    Write-Host "-> On utilisera 'python -m pennylane_mcp.server' a la place dans la config." -ForegroundColor Yellow

    $useModuleFallback = $true

} else {

    Write-Host "OK : commande pennylane-mcp-server disponible dans le venv." -ForegroundColor Green

    $useModuleFallback = $false

}

 

Write-Host "`n=== 4. Ecriture du fichier .env (mono-dossier) ===" -ForegroundColor Cyan

@"

PENNYLANE_API_TOKEN=$PennylaneApiToken

"@ | Set-Content -Path (Join-Path $InstallDir ".env") -Encoding UTF8

Write-Host "OK : .env cree dans $InstallDir" -ForegroundColor Green

 

Write-Host "`n=== 5. Mise a jour de claude_desktop_config.json ===" -ForegroundColor Cyan

$configPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"

 

if (-not (Test-Path $configPath)) {

    Write-Host "Fichier config introuvable, creation d'un nouveau." -ForegroundColor Yellow

    $config = [PSCustomObject]@{ mcpServers = [PSCustomObject]@{} }

} else {

    Copy-Item $configPath "$configPath.bak" -Force

    Write-Host "Backup cree : $configPath.bak"

    $config = Get-Content $configPath -Raw | ConvertFrom-Json

    if (-not $config.mcpServers) {

        $config | Add-Member -MemberType NoteProperty -Name mcpServers -Value ([PSCustomObject]@{})

    }

}

 

if ($useModuleFallback) {

    $pennylaneEntry = [PSCustomObject]@{

        command = $venvPython

        args    = @("-m", "pennylane_mcp.server")

        env     = [PSCustomObject]@{ PENNYLANE_API_TOKEN = $PennylaneApiToken }

    }

} else {

    $pennylaneEntry = [PSCustomObject]@{

        command = $venvExe

        env     = [PSCustomObject]@{ PENNYLANE_API_TOKEN = $PennylaneApiToken }

    }

}

 

if ($config.mcpServers.PSObject.Properties.Name -contains "pennylane") {

    $config.mcpServers.pennylane = $pennylaneEntry

} else {

    $config.mcpServers | Add-Member -MemberType NoteProperty -Name "pennylane" -Value $pennylaneEntry

}

 

$config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath -Encoding UTF8

Write-Host "OK : entree 'pennylane' ajoutee dans claude_desktop_config.json" -ForegroundColor Green

 

Pop-Location

 

Write-Host "`n=== TERMINE ===" -ForegroundColor Green

Write-Host "IMPORTANT : quitte completement Claude Desktop depuis le systray (pas juste la croix)" -ForegroundColor Yellow

Write-Host "puis relance Claude Desktop. Le serveur Pennylane devrait apparaitre dans les outils MCP." -ForegroundColor Yellow

Write-Host "Verifie ensuite avec l'outil 'pennylane_whoami' que le token correspond bien au bon collaborateur." -ForegroundColor Yellow

 