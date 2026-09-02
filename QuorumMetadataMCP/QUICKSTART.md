# QuickStart: Quorum Metadata MCP

## 🎯 The Issue (SOLVED)
**Problem:** MCP was not starting  
**Root Cause:** Missing `--env` parameter  
**Status:** ✅ FIXED

---

## 🚀 Quick Start

### One-Liner to Start MCP
```powershell
cd "c:\Users\aditya.bhagat\Downloads\QuorumMetadataMCP-v1.0"
.\QuorumMetadataMCP.exe --env ASTU_HD_DEV17
```

### Or Pick Your Environment
```powershell
# View this file for all 44 available environments:
cat dbconfig.json

# Then start with your chosen environment:
.\QuorumMetadataMCP.exe --env <YOUR_ENVIRONMENT>
```

---

## ✅ MCP Started Successfully When You See

```
info: QuorumMetadataMCP.Services.DatabaseService[0]
      Connected to SQL Server
```

The MCP is now running and listening on stdin/stdout.

---

## 🔧 Common Environments

| Purpose | Environment | Database |
|---------|-------------|----------|
| General Testing | `ASTU_HD_DEV17` | AST_DEV17UPS_QFC |
| TIPS Work | `APHU_HD_DEV17` | APH_DEV17UPS_QFC |
| Core Infrastructure | `MSSQL_CORE_HD_UPS_DEVA1` | CORE_DEVA1UPS_QFC |
| Oracle Database | `QLS_DEV_OLEDB` | QINT_CORE_DEV17QLS |

---

## 📋 All 44 Environments

**SQL Server DEV17 (29):**
ASTU, BEPU, BRMU, CCIU, CNRU, CRCU, DAYU, ENCU, EQCU, ERFU, GLEU, JDMU, JNEU, MACU, MEWU, MLNU, NOGU, NWDU, APHU, PRCU, PRMU, RLYU, SEPU, SNDU, SRCU, SUMU, TPWU

**SQL Server DEV16 (9):**
BTYU, CENU, FDLU, GECU, LUXU, MSTU, PERU, PNRU, WAGU

**Core (2):**
MSSQL_CORE_HD_UPS_SUPA1, MSSQL_CORE_HD_UPS_DEVA1

**Oracle (1):**
QLS_DEV_OLEDB

**Other:**
ENRU_HD_DEV1715, SPRU_HD_DEV1715

---

## 📍 NRM_DEV17 Not Found?

NRM_DEV17 is not in the default configuration.

**To add it:**
1. Edit `dbconfig.json`
2. Add this entry:
```json
"NRM_DEV17": {
  "type": "sqlserver",
  "server": "YOUR_SQL_SERVER\\INSTANCE",
  "database": "NRM_DEV17UPS_QFC"
}
```
3. Restart MCP: `.\QuorumMetadataMCP.exe --env NRM_DEV17`

---

## 📁 Files

| File | Purpose |
|------|---------|
| `QuorumMetadataMCP.exe` | Main executable |
| `dbconfig.json` | Environment configurations |
| `TROUBLESHOOTING.md` | Full troubleshooting guide |
| `Microsoft.Data.SqlClient.SNI.dll` | SQL Server library |
| `QuorumMetadataMCP.pdb` | Debug symbols |

---

## 💡 Usage in VS Code

When MCP is running with `--env ASTU_HD_DEV17`, VS Code can query:
- Database schemas
- Registered SQLs
- Configuration tables (QARCH_CTRL_PROCESS, etc.)
- Batch process metadata
- And more...

---

**Status:** ✅ Ready to Use  
**Location:** `c:\Users\aditya.bhagat\Downloads\QuorumMetadataMCP-v1.0`  
**Docs:** See `TROUBLESHOOTING.md` for full guide