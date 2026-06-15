@echo off

:: Start the frontend (npm run dev)
start "Frontend" cmd /k "cd /d ""D:\studying\3eme info(DSI33)\PFE_Email_Analysis\frontend"" && npm run dev"

:: Start the backend (python backend_app.py)
start "Backend" cmd /k "cd /d ""D:\studying\3eme info(DSI33)\PFE_Email_Analysis\orange_part"" && python backend_app.py"

start "" "D:\studying\3eme info(DSI33)\PFE_Email_Analysis\OrangeAnalytics.lnk"

exit