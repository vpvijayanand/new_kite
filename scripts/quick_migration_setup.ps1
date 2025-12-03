# Kite App Windows Migration Setup Script
# PowerShell script to help migrate kite_app to a new Windows environment

param(
    [string]$AppDir = "C:\apps\kite_app",
    [string]$ServiceName = "KiteApp",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Kite App Windows Migration Setup Script

Usage: .\quick_migration_setup.ps1 [-AppDir <path>] [-ServiceName <name>] [-Help]

Parameters:
  -AppDir       Application directory (default: C:\apps\kite_app)
  -ServiceName  Windows service name (default: KiteApp)
  -Help         Show this help message

Example:
  .\quick_migration_setup.ps1 -AppDir "D:\apps\kite_app" -ServiceName "MyKiteApp"
"@
    exit 0
}

# Colors for output
$Script:Colors = @{
    Red    = "Red"
    Green  = "Green"
    Yellow = "Yellow"
    Cyan   = "Cyan"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-RequiredSoftware {
    Write-Status "Checking required software installations..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Found: $pythonVersion"
    }
    catch {
        Write-Warning "Python not found. Please install Python 3.8+ from https://www.python.org/"
        Write-Host "Make sure to check 'Add Python to PATH' during installation"
        return $false
    }
    
    # Check Git (optional but recommended)
    try {
        $gitVersion = git --version 2>&1
        Write-Status "Found: $gitVersion"
    }
    catch {
        Write-Warning "Git not found. Install from https://git-scm.com/download/win (optional)"
    }
    
    # Check PostgreSQL
    try {
        $psqlVersion = psql --version 2>&1
        Write-Status "Found PostgreSQL: $psqlVersion"
    }
    catch {
        Write-Warning "PostgreSQL not found. Install from https://www.postgresql.org/download/windows/"
        return $false
    }
    
    return $true
}

function Create-AppDirectories {
    Write-Status "Creating application directories..."
    
    $directories = @(
        $AppDir,
        "$AppDir\logs",
        "$AppDir\backups",
        "$AppDir\scripts",
        "$AppDir\storage\tokens"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory -Force | Out-Null
            Write-Status "Created directory: $dir"
        }
        else {
            Write-Status "Directory exists: $dir"
        }
    }
}

function Setup-PythonEnvironment {
    Write-Status "Setting up Python virtual environment..."
    
    Push-Location $AppDir
    
    try {
        # Create virtual environment
        if (!(Test-Path "venv")) {
            python -m venv venv
            Write-Status "Created Python virtual environment"
        }
        
        # Activate and upgrade pip
        & ".\venv\Scripts\activate.ps1"
        python -m pip install --upgrade pip
        
        Write-Status "Python environment setup completed"
    }
    catch {
        Write-Error "Failed to setup Python environment: $_"
        return $false
    }
    finally {
        Pop-Location
    }
    
    return $true
}

function Install-Dependencies {
    Write-Status "Installing Python dependencies..."
    
    Push-Location $AppDir
    
    try {
        # Create basic requirements.txt if it doesn't exist
        if (!(Test-Path "requirements.txt")) {
            Write-Status "Creating basic requirements.txt..."
            
            $requirements = @"
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.7
python-dotenv==1.0.0
APScheduler==3.10.4
requests==2.31.0
pandas==2.1.1
numpy==1.25.2
pytz==2023.3
"@
            $requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
        }
        
        # Activate environment and install
        & ".\venv\Scripts\activate.ps1"
        pip install -r requirements.txt
        
        Write-Status "Dependencies installed successfully"
    }
    catch {
        Write-Error "Failed to install dependencies: $_"
        return $false
    }
    finally {
        Pop-Location
    }
    
    return $true
}

function Create-WindowsService {
    Write-Status "Creating Windows service configuration..."
    
    # Create service wrapper script
    $serviceScript = @"
import os
import sys
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil

# Add app directory to path
app_dir = r'$AppDir'
sys.path.insert(0, app_dir)
os.chdir(app_dir)

class KiteAppService(win32serviceutil.ServiceFramework):
    _svc_name_ = '$ServiceName'
    _svc_display_name_ = 'Kite Trading Application'
    _svc_description_ = 'Flask-based trading application for Kite Connect'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                             servicemanager.PYS_SERVICE_STARTED,
                             (self._svc_name_, ''))
        self.main()

    def main(self):
        # Import and run the Flask app
        try:
            from run import app
            app.run(host='0.0.0.0', port=5000)
        except Exception as e:
            servicemanager.LogErrorMsg(f'Service error: {str(e)}')

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(KiteAppService)
"@

    $serviceScript | Out-File -FilePath "$AppDir\kite_service.py" -Encoding UTF8
    
    Write-Status "Service script created at: $AppDir\kite_service.py"
    Write-Status "To install service: python $AppDir\kite_service.py install"
    Write-Status "To start service: python $AppDir\kite_service.py start"
}

function Create-EnvironmentTemplate {
    Write-Status "Creating environment configuration template..."
    
    $envTemplate = @"
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost/kite_db

# Kite Connect API Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret

# Optional: Redis for caching (if using)
# REDIS_URL=redis://localhost:6379/0

# Windows specific settings
PYTHONPATH=$AppDir
"@

    $envTemplate | Out-File -FilePath "$AppDir\.env.template" -Encoding UTF8
    Write-Status "Environment template created: $AppDir\.env.template"
    Write-Warning "Please copy .env.template to .env and update with your actual values"
}

function Create-HelperScripts {
    Write-Status "Creating helper scripts..."
    
    # Database backup script
    $backupScript = @"
# Database Backup Script for Kite App
param(
    [string]`$BackupDir = "$AppDir\backups"
)

`$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
`$backupFile = "`$BackupDir\kite_db_`$timestamp.sql"

Write-Host "Creating database backup..."
pg_dump -h localhost -U your_db_user kite_db > `$backupFile

if (`$LASTEXITCODE -eq 0) {
    Write-Host "Backup created: `$backupFile"
    
    # Clean old backups (keep last 7 days)
    Get-ChildItem `$BackupDir -Name "kite_db_*.sql" | 
        Where-Object { `$_.CreationTime -lt (Get-Date).AddDays(-7) } |
        Remove-Item -Force
} else {
    Write-Error "Backup failed"
}
"@

    $backupScript | Out-File -FilePath "$AppDir\scripts\backup_db.ps1" -Encoding UTF8
    
    # Health check script
    $healthScript = @"
# Health Check Script for Kite App
`$appUrl = "http://localhost:5000"
`$logFile = "$AppDir\logs\health_check.log"

`$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    `$response = Invoke-WebRequest -Uri `$appUrl -TimeoutSec 30
    if (`$response.StatusCode -eq 200) {
        "`$timestamp : Application is healthy" | Add-Content `$logFile
    }
} catch {
    "`$timestamp : Application is DOWN - attempting restart" | Add-Content `$logFile
    
    # Restart the service
    try {
        Restart-Service -Name '$ServiceName'
        "`$timestamp : Service restarted" | Add-Content `$logFile
    } catch {
        "`$timestamp : Failed to restart service: `$_" | Add-Content `$logFile
    }
}
"@

    $healthScript | Out-File -FilePath "$AppDir\scripts\health_check.ps1" -Encoding UTF8
    
    # Start app script
    $startScript = @"
# Start Kite App (Development)
Set-Location '$AppDir'
& '.\venv\Scripts\activate.ps1'
python run.py
"@

    $startScript | Out-File -FilePath "$AppDir\scripts\start_app.ps1" -Encoding UTF8
    
    Write-Status "Helper scripts created in: $AppDir\scripts\"
}

function Create-TaskScheduler {
    Write-Status "Creating scheduled task templates..."
    
    # Strategy 1 execution task
    $taskScript = @"
# Scheduled Task for Strategy 1 Execution
# Run this script to create the scheduled task

`$taskName = "KiteApp_Strategy1"
`$scriptPath = "$AppDir\strategy1_standalone.py"
`$pythonPath = "$AppDir\venv\Scripts\python.exe"

# Create the scheduled task
`$action = New-ScheduledTaskAction -Execute `$pythonPath -Argument `$scriptPath
`$trigger = New-ScheduledTaskTrigger -Daily -At "09:30AM"
`$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
`$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName `$taskName -Action `$action -Trigger `$trigger -Settings `$settings -Principal `$principal

Write-Host "Scheduled task '$taskName' created successfully"
Write-Host "Task will run Strategy 1 daily at 9:30 AM"
"@

    $taskScript | Out-File -FilePath "$AppDir\scripts\create_scheduled_task.ps1" -Encoding UTF8
    
    Write-Status "Scheduled task template created: $AppDir\scripts\create_scheduled_task.ps1"
}

function Print-FinalInstructions {
    Write-Host ""
    Write-Host "🎉 Windows setup completed!" -ForegroundColor Green
    Write-Host "=========================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps to complete the migration:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Transfer your application code:" -ForegroundColor Yellow
    Write-Host "   - Copy your kite_app files to: $AppDir"
    Write-Host "   - Or clone from git: git clone <your-repo> $AppDir"
    Write-Host ""
    Write-Host "2. Update configuration:" -ForegroundColor Yellow
    Write-Host "   - Copy .env.template to .env: Copy-Item '$AppDir\.env.template' '$AppDir\.env'"
    Write-Host "   - Edit .env with your actual values"
    Write-Host ""
    Write-Host "3. Setup PostgreSQL database:" -ForegroundColor Yellow
    Write-Host "   - Create database: createdb -U postgres kite_db"
    Write-Host "   - Restore data: psql -U postgres -d kite_db -f your_backup.sql"
    Write-Host ""
    Write-Host "4. Install Python dependencies:" -ForegroundColor Yellow
    Write-Host "   - cd '$AppDir'"
    Write-Host "   - .\venv\Scripts\activate.ps1"
    Write-Host "   - pip install -r requirements.txt"
    Write-Host ""
    Write-Host "5. Run database migrations:" -ForegroundColor Yellow
    Write-Host "   - `$env:FLASK_APP='run.py'"
    Write-Host "   - flask db upgrade"
    Write-Host ""
    Write-Host "6. Install and start Windows service:" -ForegroundColor Yellow
    Write-Host "   - pip install pywin32"
    Write-Host "   - python '$AppDir\kite_service.py' install"
    Write-Host "   - python '$AppDir\kite_service.py' start"
    Write-Host ""
    Write-Host "7. Create scheduled tasks:" -ForegroundColor Yellow
    Write-Host "   - Run: '$AppDir\scripts\create_scheduled_task.ps1'"
    Write-Host ""
    Write-Host "8. Test the application:" -ForegroundColor Yellow
    Write-Host "   - Visit: http://localhost:5000/"
    Write-Host "   - Check: http://localhost:5000/strategies/"
    Write-Host ""
    Write-Host "Helper scripts available:" -ForegroundColor Cyan
    Write-Host "- Start app (dev): $AppDir\scripts\start_app.ps1"
    Write-Host "- Database backup: $AppDir\scripts\backup_db.ps1"
    Write-Host "- Health check: $AppDir\scripts\health_check.ps1"
    Write-Host ""
    Write-Host "For detailed instructions, see: $AppDir\docs\MIGRATION_GUIDE.md" -ForegroundColor Green
}

# Main execution
function Main {
    Write-Host "🚀 Starting Kite App Windows Migration Setup..." -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Warning "This script should be run as Administrator for best results"
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            Write-Status "Setup cancelled by user"
            exit 0
        }
    }
    
    # Check required software
    if (-not (Install-RequiredSoftware)) {
        Write-Error "Required software not found. Please install missing components and try again."
        exit 1
    }
    
    # Run setup functions
    Create-AppDirectories
    
    if (-not (Setup-PythonEnvironment)) {
        Write-Error "Failed to setup Python environment"
        exit 1
    }
    
    if (-not (Install-Dependencies)) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
    
    Create-WindowsService
    Create-EnvironmentTemplate
    Create-HelperScripts
    Create-TaskScheduler
    
    Print-FinalInstructions
}

# Run main function
Main
