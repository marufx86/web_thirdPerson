@echo off
rem Serves dist\ like a plain static web host, then open http://localhost:8080/ in Chrome. See HOSTING.md.
where py >nul 2>&1
if %ERRORLEVEL%==0 (
	py "%~dp0serve_dist.py" %*
) else (
	python "%~dp0serve_dist.py" %*
)
pause
