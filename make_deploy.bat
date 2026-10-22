@echo off
rem Builds the deployable folder WebGPUPort\M6-Deploy\dist from the current engine build and content package.
rem Usage: make_deploy.bat [Project=WebThirdPerson]. See HOSTING.md.
where py >nul 2>&1
if %ERRORLEVEL%==0 (
	py -I "%~dp0make_deploy.py" %*
) else (
	python -I "%~dp0make_deploy.py" %*
)
exit /b %ERRORLEVEL%
