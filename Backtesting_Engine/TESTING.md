Testing the backtesting-engine
=============================

This document explains how to run the loader manually and how to run an offline unit test that mocks Kite API.

Prerequisites
-------------
- Python 3.11+.
- This repository does NOT include a virtual environment. Create one locally (recommended) and activate it before installing dependencies.

Create and activate a venv (Windows cmd):

```bash
python -m venv .venv
.venv\Scripts\activate
```

PowerShell:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Manual (CLI) test
-----------------
1. Ensure there is a request file at the project root, e.g. [request.json](request.json).
Here is an example of the json file 
```bash
{
  "symbols": ["^NSEI"],
  "start": "2023-01-01",
  "end": "2023-06-01",
  "interval": "1d",
  "auto_adjust": true
}
```

Remember to use only Kite API symbols only (as Kite API is being used has its own internal symbols)


2. Run the loader CLI (writes Parquet by default to `app/storage/parquet`):

```bash
python -m app.main request.json
```

3. Verify output exists and inspect a file:

```bash
dir app\storage\parquet
python -c "import pandas as pd; print(pd.read_parquet('app/storage/parquet/RELIANCE.NS.parquet').head())"
```




Run the test suite with:

```bash
pip install pytest
pytest -q
```

Notes and tips
--------------
- If you use the repository `python` from `.venv`, replace `python` above with the full path: `./.venv/Scripts/python.exe` (Windows) or `./.venv/bin/python` (macOS/Linux).
- The loader writes one Parquet file per symbol by default. The Parquet files follow the schema `symbol,timestamp,open,high,low,close,volume`.
- If you want CI-safe tests, add the mocked test above to `tests/` and run `pytest` in CI.

If you want, I can create `tests/test_loader.py` for you now and run the tests locally.
