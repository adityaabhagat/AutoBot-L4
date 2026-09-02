# ═══════════════════════════════════════════════════════════════════════════
# Quorum Metadata MCP — Client Configuration Manager
# Automatically adds client environments to dbconfig.json and manages MCP startup
# ═══════════════════════════════════════════════════════════════════════════

param(
    [string]$Action = "help",
    [string]$ClientName,
    [string]$Environment,
    [string]$Server,
    [string]$Database,
    [string]$Type = "sqlserver",
    [string]$DbConfigPath = "$PSScriptRoot\dbconfig.json",
    [switch]$StartMCP,
    [switch]$Quiet
)

# Configuration state
$script:config = $null
$script:modified = $false

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Load-Config {
    if (-not (Test-Path $DbConfigPath)) {
        Write-Host "ERROR: dbconfig.json not found at: $DbConfigPath" -ForegroundColor Red
        exit 1
    }
    $raw = Get-Content $DbConfigPath -Raw
    $script:config = $raw | ConvertFrom-Json
}

function Save-Config {
    $json = $script:config | ConvertTo-Json -Depth 10
    Set-Content -Path $DbConfigPath -Value $json -Encoding UTF8
    Write-Status "✓ Configuration saved to dbconfig.json" "Green"
    $script:modified = $true
}

function Add-ClientEnvironment {
    param(
        [string]$Name,
        [string]$Server,
        [string]$Database,
        [string]$Type = "sqlserver"
    )
    
    # Check if already exists
    if ($script:config.environments.PSObject.Properties[$Name]) {
        Write-Status "⚠ Environment already exists: $Name" "Yellow"
        return $false
    }
    
    # Create new environment object
    $newEnv = @{
        "type" = $Type
    }
    
    if ($Type -eq "sqlserver") {
        $newEnv["server"] = $Server
        $newEnv["database"] = $Database
    } elseif ($Type -eq "oracle-oledb") {
        $newEnv["database"] = $Database
        $newEnv["auth"] = "credentials"
    }
    
    # Add to config
    $script:config.environments | Add-Member -MemberType NoteProperty -Name $Name -Value $newEnv
    Write-Status "✓ Added environment: $Name" "Green"
    return $true
}

function List-Environments {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Available Environments in dbconfig.json              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $count = 0
    $sqlCount = 0
    $oracleCount = 0
    
    $script:config.environments.PSObject.Properties | ForEach-Object {
        $count++
        $name = $_.Name
        $value = $_.Value
        $type = $value.type
        $database = $value.database
        
        if ($type -eq "sqlserver") { $sqlCount++ } else { $oracleCount++ }
        
        $color = if ($type -eq "sqlserver") { "Green" } else { "Magenta" }
        Write-Host "  [$count] $name" -ForegroundColor $color
        Write-Host "      Type: $type | Database: $database"
        if ($value.server) { Write-Host "      Server: $($value.server)" }
    }
    
    Write-Host ""
    Write-Host "Total Environments: $count (SQL: $sqlCount | Oracle: $oracleCount)" -ForegroundColor Cyan
    Write-Host ""
}

function Start-MCPServer {
    param([string]$Environment)
    
    if (-not $Environment) {
        Write-Host "ERROR: Environment parameter is required" -ForegroundColor Red
        exit 1
    }
    
    # Verify environment exists
    if (-not $script:config.environments.PSObject.Properties[$Environment]) {
        Write-Host "ERROR: Environment not found: $Environment" -ForegroundColor Red
        List-Environments
        exit 1
    }
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Starting Quorum Metadata MCP Server                      ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Environment: $Environment" -ForegroundColor Yellow
    
    $envConfig = $script:config.environments.$Environment
    Write-Host "Type:        $($envConfig.type)" -ForegroundColor Gray
    Write-Host "Database:    $($envConfig.database)" -ForegroundColor Gray
    
    if ($envConfig.server) {
        Write-Host "Server:      $($envConfig.server)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Starting process..." -ForegroundColor Yellow
    Write-Host ""
    
    # Verify executable exists
    $mcpPath = Join-Path $PSScriptRoot "QuorumMetadataMCP.exe"
    if (-not (Test-Path $mcpPath)) {
        Write-Host "ERROR: QuorumMetadataMCP.exe not found at: $mcpPath" -ForegroundColor Red
        exit 1
    }
    
    # Start MCP with environment
    Write-Host "────────────────────────────────────────────────────────────" -ForegroundColor Gray
    & $mcpPath --env $Environment
}

function Show-Help {
    $help = @"
╔════════════════════════════════════════════════════════════════════════════╗
║  Quorum Metadata MCP — Client Configuration Manager                       ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
  .\MCP-ConfigManager.ps1 -Action <action> [options]

ACTIONS:

  list
    List all configured environments
    .\MCP-ConfigManager.ps1 -Action list

  add
    Add a new SQL Server client environment
    Required: -ClientName, -Server, -Database
    .\MCP-ConfigManager.ps1 -Action add `
      -ClientName "NRM_DEV17" `
      -Server "QDDDEVSQL05.QDEV.NET\SQL2019" `
      -Database "NRM_DEV17UPS_QFC"

  addoracle
    Add a new Oracle client environment
    Required: -ClientName, -Database
    .\MCP-ConfigManager.ps1 -Action addoracle `
      -ClientName "QLS_NEW" `
      -Database "QINT_NEW_DEV17QLS"

  start
    Start MCP server with specified environment
    Required: -Environment
    .\MCP-ConfigManager.ps1 -Action start -Environment NRM_DEV17

  verify
    Verify environment exists in configuration
    Required: -Environment
    .\MCP-ConfigManager.ps1 -Action verify -Environment NRM_DEV17

  addandstart
    Add client and immediately start MCP (Case Loader integration)
    Required: -ClientName, -Server, -Database
    .\MCP-ConfigManager.ps1 -Action addandstart `
      -ClientName "NEW_ENV" `
      -Server "QDDDEVSQL01.QDEV.NET\SQL2017" `
      -Database "NEW_DEV17UPS_QFC"

OPTIONS:

  -DbConfigPath <path>
    Path to dbconfig.json (default: current directory)

  -StartMCP
    Automatically start MCP after adding client

  -Quiet
    Suppress console output (for automation)

EXAMPLES:

  1. List all environments:
     .\MCP-ConfigManager.ps1 -Action list

  2. Add NRM_DEV17:
     .\MCP-ConfigManager.ps1 -Action add `
       -ClientName "NRM_DEV17" `
       -Server "QDDDEVSQL05.QDEV.NET\SQL2019" `
       -Database "NRM_DEV17UPS_QFC"

  3. Start MCP with NRM_DEV17:
     .\MCP-ConfigManager.ps1 -Action start -Environment NRM_DEV17

  4. Add and start immediately:
     .\MCP-ConfigManager.ps1 -Action addandstart `
       -ClientName "CUSTOM" `
       -Server "QDDDEVSQL01.QDEV.NET\SQL2017" `
       -Database "CUSTOM_DEV17UPS_QFC"

╔════════════════════════════════════════════════════════════════════════════╗
║  Integration with Case Loader                                              ║
╚════════════════════════════════════════════════════════════════════════════╝

Automatically triggered when a client is selected in the Case Loader UI:

  PowerShell.exe -NoProfile -Command `
    "& 'C:\...\MCP-ConfigManager.ps1' -Action addandstart `
      -ClientName 'NRM_DEV17' `
      -Server 'QDDDEVSQL05.QDEV.NET\SQL2019' `
      -Database 'NRM_DEV17UPS_QFC' -Quiet"

This will:
  1. Add the client to dbconfig.json if not already present
  2. Automatically start the MCP server with that environment
  3. Run in quiet mode to minimize output

"@
    Write-Host $help
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

try {
    Load-Config
    
    switch ($Action.ToLower()) {
        "list" {
            List-Environments
        }
        "add" {
            if (-not $ClientName -or -not $Server -or -not $Database) {
                Write-Host "ERROR: Missing required parameters" -ForegroundColor Red
                Write-Host "Required: -ClientName, -Server, -Database" -ForegroundColor Yellow
                exit 1
            }
            $added = Add-ClientEnvironment -Name $ClientName -Server $Server -Database $Database -Type $Type
            if ($added) {
                Save-Config
            }
            if ($StartMCP) {
                Start-MCPServer -Environment $ClientName
            }
        }
        "addoracle" {
            if (-not $ClientName -or -not $Database) {
                Write-Host "ERROR: Missing required parameters" -ForegroundColor Red
                Write-Host "Required: -ClientName, -Database" -ForegroundColor Yellow
                exit 1
            }
            $added = Add-ClientEnvironment -Name $ClientName -Database $Database -Type "oracle-oledb"
            if ($added) {
                Save-Config
            }
            if ($StartMCP) {
                Start-MCPServer -Environment $ClientName
            }
        }
        "addandstart" {
            if (-not $ClientName -or -not $Database) {
                Write-Host "ERROR: Missing required parameters" -ForegroundColor Red
                Write-Host "Required: -ClientName, -Database, and -Server for SQL Server" -ForegroundColor Yellow
                exit 1
            }
            
            # For SQL Server, require server parameter
            if ($Type -eq "sqlserver" -and -not $Server) {
                Write-Host "ERROR: -Server required for SQL Server environments" -ForegroundColor Red
                exit 1
            }
            
            Write-Status "Adding client: $ClientName"
            $added = Add-ClientEnvironment -Name $ClientName -Server $Server -Database $Database -Type $Type
            
            if ($added) {
                Save-Config
                Write-Status "✓ Configuration updated" "Green"
            }
            
            Write-Status "Starting MCP server..."
            Start-MCPServer -Environment $ClientName
        }
        "start" {
            if (-not $Environment) {
                Write-Host "ERROR: Environment parameter required" -ForegroundColor Red
                List-Environments
                exit 1
            }
            Start-MCPServer -Environment $Environment
        }
        "verify" {
            if (-not $Environment) {
                Write-Host "ERROR: Environment parameter required" -ForegroundColor Red
                exit 1
            }
            if ($script:config.environments.PSObject.Properties[$Environment]) {
                $env = $script:config.environments.$Environment
                Write-Host "✓ Environment exists: $Environment" -ForegroundColor Green
                Write-Host "  Type: $($env.type)"
                Write-Host "  Database: $($env.database)"
                if ($env.server) { Write-Host "  Server: $($env.server)" }
            } else {
                Write-Host "✗ Environment not found: $Environment" -ForegroundColor Red
                exit 1
            }
        }
        "help" {
            Show-Help
        }
        default {
            Write-Host "Unknown action: $Action" -ForegroundColor Red
            Write-Host "Use: .\MCP-ConfigManager.ps1 -Action help" -ForegroundColor Yellow
            exit 1
        }
    }
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
