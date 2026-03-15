This folder contains convenience scripts to start the development environment for smartbin-ai.

Files:
- start.ps1  - PowerShell script that opens two PowerShell windows and runs the backend and frontend.
- start.sh   - Bash/WSL/Git-Bash script that starts backend and frontend in background and writes logs to /tmp.

Usage:
- Windows (PowerShell): .\scripts\start.ps1
- Unix/WSL/Git-Bash: ./scripts/start.sh

Notes:
- Both scripts assume the backend virtualenv exists at `backend/venv` and that `npm` is installed and available in PATH.
- If your frontend uses the `frontend` folder directly (not `frontend/smartbin-ai`), update the paths in the scripts accordingly.