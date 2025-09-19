# DataShuttle

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=fff&labelColor=grey&color=yellowgreen)
![Platform](https://img.shields.io/badge/platform-desktop-blue)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/WoongyuChoi/DataShuttle)

> Lightweight, GUI-based table shuttle between two relational DBs (e.g., **Oracle → PostgreSQL**) with chunked inserts and error-skipping.
<figure align="center">
  <img src="https://github.com/user-attachments/assets/19000f1c-7254-4103-bf1c-2bcfc9f8dd76" alt="DataShuttle UI" width="80%" />
</figure>

## Overview

**DataShuttle** is a PyQt5 application that pulls rows from a **source (Origin)** database and inserts them into a **destination** database, assuming identical table structures. It focuses on practicality:
- Chunked migration (default **10,000** rows per batch)
- **Skip-on-error** per row when needed
- Non-blocking UI (**QThread**-based worker)
- Instant **Test Connection** in Settings
- **Preset Save/Load** to quickly reuse connection & query configs
- **CSV Export (Origin)** with UTF-8

## Key Features

- **Two Connections (Connection 1 / Connection 2)**  
  Oracle or PostgreSQL for each side. Auto-default ports by DB type.

- **Origin / Destination Mapping**  
  Separate inputs for Origin `SCHEMA, TABLES` and Destination `SCHEMA, TABLES`. If destination names are blank, origin names are used. WHERE applies to **Origin** only.

- **Chunked Inserts + Error Skips**  
  Streams SELECT from Origin and bulk-inserts to Destination (10,000 rows per chunk). If a chunk fails, it retries per row and **skips** rows that still fail, logging errors with row index.

- **Cross-DB Identifier Handling**  
  Oracle identifiers are handled without breaking (e.g., `UPDATED_AT` vs `"updated_at"`). The app selects with proper aliases to keep mapping stable.

- **Settings Dialog**  
  - DB Type (Oracle / PostgreSQL)  
  - Protocol (TCP / TCPS-SSL placeholder)  
  - Host / Port (auto default by DB type)  
  - Service/DB (Oracle: `SERVICE_NAME/SID`, PostgreSQL: database name)  
  - **Test Connection…** button

- **Preset Save/Load**  
  One-click export/import of JSON (saved as `.txt` or `.json`) including:  
  `connection_1/2` config, Origin schema/tables/where, Destination schema/tables.

- **CSV Export (Origin)**  
  Re-run the same Origin query and **stream** results to CSV (UTF-8 with BOM: `utf-8-sig`).  
  Multi-table export saves one file per table to the selected folder.

## Project Layout (suggested)

```
data_shuttle/
  ├─ gui.py                 # UI event handlers, QThread worker wiring
  ├─ ui_setup.py            # Pure UI layout (widgets only)
  ├─ utils.py               # DB engines, counting, streaming select→insert, CSV export
  └─ dialog/
      └─ settings_dialog.py # Settings modal with Test Connection
```

## Requirements

- Python **3.10+**
- Windows/macOS/Linux (desktop environment)
- Packages:
  - `PyQt5`
  - `SQLAlchemy>=2.0`
  - `oracledb` (for Oracle)
  - `psycopg[binary]` (for PostgreSQL)
  - `PyInstaller` (for packaging)
  - `pandas` (optional, CSV helpers)

## Setup

1. **Clone & Install**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run**
   ```bash
   python .\main.py
   ```

3. **Build Executable (Windows)**
   ```bash
   pyinstaller --onefile --windowed --icon favicon.ico --hidden-import sqlalchemy.dialects.oracle --hidden-import sqlalchemy.dialects.postgresql.psycopg main.py
   ```

## Usage

1. **Open Settings (⚙)** → Choose DB type (Oracle/PostgreSQL), fill Host/Port/Service/DB/ID/Password.
2. **Test Connection…** to verify credentials on each tab (Connection 1 / Connection 2).
3. **Fill Origin** (`SCHEMA`, `TABLES`) and **Destination** (`SCHEMA`, `TABLES`).  
   - Leave Destination fields empty to mirror Origin names.  
   - WHERE is **Origin-only** (write conditions without the `WHERE` keyword).
4. **Start Migration**  
   - Console shows logs; the **Result** table shows `Step/Detail` progress (chunk successes, per-row errors).
5. **CSV Export (Origin)** to save the Origin query results (UTF-8 with BOM).

## Preset Save/Load

- **Save Preset** (top-left): dumps a JSON like:
  ```json
  {
    "version": 1,
    "settings": { "connection_1": { "db_type": "Oracle", "host": "127.0.0.1", "port": 1521, "service_or_db": "ORCL", "user": "scott", "password": "tiger" },
                  "connection_2": { "db_type": "PostgreSQL", "host": "127.0.0.1", "port": 5432, "service_or_db": "devdb", "user": "dev", "password": "devpw" } },
    "origin": { "schema": "DATASHUTTLE", "tables": "T1,T2", "where": "status='A'" },
    "destination": { "schema": "DEV_DS", "tables": "T1_DST,T2_DST" }
  }
  ```
- **Load Preset**: restores both connections + Origin/Destination/WHERE.

> **Security Note:** Preset files contain credentials. Please keep them in a secure location.

## Troubleshooting

- **`ModuleNotFoundError: oracledb / psycopg`**  
  Install DB drivers: `pip install oracledb "psycopg[binary]"`

- **Oracle `ORA-00904 invalid identifier`**  
  The app handles identifier casing by selecting with aliases; ensure actual column names exist and table structures match.

- **Korean (한글) breaks in CSV**  
  Files are written as **UTF-8 with BOM (`utf-8-sig`)** for Excel compatibility. If your environment still breaks, try `cp949`.

- **PyInstaller missing dialects**  
  Add hidden imports:  
  `--hidden-import sqlalchemy.dialects.oracle --hidden-import sqlalchemy.dialects.postgresql.psycopg`

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
