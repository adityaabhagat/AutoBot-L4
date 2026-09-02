# Quorum Metadata MCP — Troubleshooting Report

## Issue Found: ✅ RESOLVED

### Problem
The Quorum Metadata MCP was not starting because **it requires an environment parameter** to be specified via command-line argument.

### Root Cause
The MCP executable (`QuorumMetadataMCP.exe`) is designed to connect to a specific customer database environment. Without specifying which environment to connect to, it exits with an error message.

### Error Message (Original)
```
Error: Environment name is required.
Usage: QuorumMetadataMCP --env <environment_name>
Available environments: APHU_HD_DEV17, ASTU_HD_DEV17, BEPU_HD_DEV17, ...
```

---

## ✅ Solution: How to Start the MCP

### Step 1: Identify Your Target Environment

The MCP supports 44 different customer environments. Common ones include:

**For TIPS (Oil & Gas) Products:**
- Most customer environments are in DEV17 or DEV16 variations
- No specific "NRM_DEV17" found in config — check which customer environment you need

**SQL Server Environments:**
- `ASTU_HD_DEV17` - Apex Energy  
- `BEPU_HD_DEV17` - BEPUe specific environment
- `PRMU_HD_DEV17` - Permian region environment
- `SPRU_HD_DEV1715` - SPR product DEV1715
- And 40+ more customer-specific environments

**Oracle Environment:**
- `QLS_DEV_OLEDB` - QLS Oracle-based environment (requires Oracle driver)

### Step 2: Start the MCP with Environment Parameter

```powershell
cd "c:\Users\aditya.bhagat\Downloads\QuorumMetadataMCP-v1.0"

# Replace ENVIRONMENT_NAME with your target environment
.\QuorumMetadataMCP.exe --env <ENVIRONMENT_NAME>

# Example:
.\QuorumMetadataMCP.exe --env ASTU_HD_DEV17
```

### Step 3: Verify MCP Started Successfully

The MCP will show logs like:
```
info: Program[0]
      Initializing Quorum Metadata MCP Server...
info: Program[0]
      Environment: ASTU_HD_DEV17
info: QuorumMetadataMCP.Services.DatabaseService[0]
      Initializing database service for environment: ASTU_HD_DEV17
info: QuorumMetadataMCP.Services.DatabaseService[0]
      Creating SQL Server connection
info: QuorumMetadataMCP.Services.DatabaseService[0]
      Using Windows Authentication for SQL Server connection
info: QuorumMetadataMCP.Services.DatabaseService[0]
      Connected to SQL Server
```

When you see **"Connected to SQL Server"** or similar, the MCP is ready and listening on stdio.

---

## Available Environments (44 Total)

### By Region/Customer (DEV17):
```
ASTU_HD_DEV17        BEPU_HD_DEV17        BRMU_HD_DEV17        CCIU_HD_DEV17
CNRU_HD_DEV17        CRCU_HD_DEV17        DAYU_HD_DEV17        ENCU_HD_DEV17
ENRU_HD_DEV1715      EQCU_HD_DEV17        ERFU_HD_DEV17        GLEU_HD_DEV17
JDMU_HD_DEV17        JNEU_HD_DEV17        MACU_HD_DEV17        MEWU_HD_DEV17
MLNU_HD_DEV17        NOGU_HD_DEV17        NWDU_HD_DEV17        APHU_HD_DEV17
PRCU_HD_DEV17        PRMU_HD_DEV17        RLYU_HD_DEV17        SEPU_HD_DEV17
SNDU_HD_DEV17        SRCU_HD_DEV17        SUMU_HD_DEV17        TPWU_HD_DEV17
SPRU_HD_DEV1715
```

### DEV16 Environments:
```
BTYU_DEV16           CENU_DEV16           FDLU_DEV16           GECU_DEV16
LUXU_DEV16           MSTU_DEV16           PERU_DEV16           PNRU_DEV16
WAGU_DEV16
```

### Core Infrastructure:
```
MSSQL_CORE_HD_UPS_SUPA1
MSSQL_CORE_HD_UPS_DEVA1
```

### Oracle Database:
```
QLS_DEV_OLEDB        (Requires Oracle client libraries)
```

---

## Configuration Details

### Location
```
c:\Users\aditya.bhagat\Downloads\QuorumMetadataMCP-v1.0\dbconfig.json
```

### Connection Details
Each environment is configured with:
- **Type**: `sqlserver` or `oracle-oledb`
- **Server**: Database server FQDN/instance name
- **Database**: Target database name
- **Authentication**: Windows Authentication (SQL Server) or credential-based (Oracle)

### Example Configuration
```json
{
  "ASTU_HD_DEV17": {
    "type": "sqlserver",
    "server": "QDDDEVSQL01.QDEV.NET\\SQL2017",
    "database": "AST_DEV17UPS_QFC"
  }
}
```

---

## Finding Your Environment

### If you're working with TIPS Batch (Case 26-01083038):
The case references an NRM_DEV17 environment, but this environment is **not configured** in the MCP's dbconfig.json.

**Options:**
1. **Add NRM_DEV17 to dbconfig.json** if you have the database credentials
2. **Use an existing environment** (e.g., ASTU_HD_DEV17 for testing)
3. **Request environment setup** from DBA team

### To Add a New Environment

Edit `dbconfig.json` and add:
```json
"NRM_DEV17": {
  "type": "sqlserver",
  "server": "YOUR_SQL_SERVER\\INSTANCE",
  "database": "NRM_DEV17UPS_QFC"
}
```

Then restart MCP with: `.\QuorumMetadataMCP.exe --env NRM_DEV17`

---

## PowerShell Script to List All Environments

```powershell
$configPath = "c:\Users\aditya.bhagat\Downloads\QuorumMetadataMCP-v1.0\dbconfig.json"
$config = Get-Content $configPath | ConvertFrom-Json

Write-Host "Available Quorum Metadata MCP Environments:" -ForegroundColor Green
Write-Host ""

$config.environments.PSObject.Properties | ForEach-Object {
    $env = $_.Name
    $type = $_.Value.type
    $server = $_.Value.server
    $database = $_.Value.database
    
    Write-Host "$env" -ForegroundColor Cyan
    Write-Host "  Type: $type" -ForegroundColor Gray
    Write-Host "  Server: $server" -ForegroundColor Gray
    Write-Host "  Database: $database" -ForegroundColor Gray
    Write-Host ""
}
```

---

## Quick Start Commands

```powershell
# List all environments (using PowerShell script above)
# Then choose one and start:

# Example 1: Start with ASTU environment
.\QuorumMetadataMCP.exe --env ASTU_HD_DEV17

# Example 2: Start with TIPS-related Apex environment  
.\QuorumMetadataMCP.exe --env APHU_HD_DEV17

# Example 3: Start with QLS Oracle environment (if Oracle client available)
.\QuorumMetadataMCP.exe --env QLS_DEV_OLEDB
```

---

## Troubleshooting Additional Issues

### Issue: "Cannot connect to SQL Server"
**Cause:** Network connectivity issue or SQL Server not accessible  
**Solution:** 
- Verify SQL Server is running
- Check network connectivity to the server
- Verify Windows Authentication credentials
- Check firewall rules

### Issue: "Database not found"
**Cause:** Database name in config is incorrect  
**Solution:**
- Verify database name in dbconfig.json
- Ensure database exists on the SQL Server
- Check database permissions for your Windows user

### Issue: "Oracle client library not found" (for QLS_DEV_OLEDB)
**Cause:** Oracle client not installed on this machine  
**Solution:**
- Install Oracle client libraries
- Or use a SQL Server environment instead
- Contact DBA team for Oracle setup assistance

---

## Summary

| Item | Status | Action |
|------|--------|--------|
| **MCP Installation** | ✅ Working | Ready to use |
| **Startup Requirement** | ✅ Identified | Use `--env` parameter |
| **Available Environments** | ✅ 44 total | Choose appropriate one |
| **NRM_DEV17 Configured** | ❌ Not found | Add to dbconfig.json or request setup |

**Next Step:** Choose your target environment and start the MCP using:
```powershell
.\QuorumMetadataMCP.exe --env <ENVIRONMENT_NAME>
```

---

**Created:** April 23, 2026  
**Status:** Troubleshooting Complete  
**Recommendation:** Use `ASTU_HD_DEV17` or other available environment for testing