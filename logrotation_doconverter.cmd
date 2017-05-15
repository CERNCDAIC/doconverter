@echo off
REM Script to rotate a file in a dayly or monthly basis
REM It expects three arguments:
REM   1. logfile: file to be rotated. Full path.
REM	  2. Interval: either DAY or MONTH
REM	  3. Number of processes to start doconverter
REM   4. EXE normally python.exe
REM   5. Location of the py file to be executed
REM   6. Virtual environment if any.
REM	  Example:
REM   %0 .\logrotation_doconverter.bat  c:\doconverter\logs\api.log DAY 2 python.exe G:\Services\conversion\production-test02\doconverterwww\project\doconverter\engines\converter_daemon.py converter3464
REM Author: Ruben Gaspar rgaspar@cern.ch

SETLOCAL ENABLEEXTENSIONS

set /A NOT_DEFINED_VAR=-1
set /A FILE_NOT_FOUND=-2

set LOGFILE=%~1
set INTERVAL=%~2
set PROCESSES=%~3
set EXE=%~4
set ARGUMENT=%~5
set CONTAINER=%~6
:: this is just the name of my script
set ME=%~n0
set LOGGING_DIR="%windir%\TEMP"
IF "M%LOGFILE%"=="M" (
	echo "No path to clean provided"
	EXIT /B %NOT_DEFINED_VAR%
)
IF "M%INTERVAL%"=="M" (
	echo "Using and older than default of 15 days"
	EXIT /B %NOT_DEFINED_VAR%
)
IF "M%PROCESSES%"=="M" (
	echo "Default we clean directories"
	EXIT /B %NOT_DEFINED_VAR%
)
IF NOT EXIST %LOGFILE% (
	echo "Path doesnt exist"
	EXIT /B %FILE_NOT_FOUND%)

IF "M%EXE%"=="M" (
	echo "No exe provided"
	EXIT /B %NOT_DEFINED_VAR%
)
IF "M%ARGUMENT%"=="M" (
	echo "No Arguments provided"
	EXIT /B %NOT_DEFINED_VAR%
)
IF NOT EXIST %ARGUMENT% (
	echo "%ARGUMENT% doesnt exist"
	EXIT /B %FILE_NOT_FOUND%
)
IF "M%CONTAINER%"=="M" (
	echo "%CONTAINER% not provided"
) ELSE set WITHCONTAINER=workon %CONTAINER%

:: create a log file named [script].YYYYMMDDHHMMSS.txt
:: Create the date and time elements. Locale independent
if "%INTERVAL%"=="DAY" (
		For /f "tokens=1-3 delims=/. " %%a in ('date/T') do set CDate=%%b%%c%
)
if "%INTERVAL%"=="MONTH" (
		For /f "tokens=1-3 delims=/. " %%a in ('date/T') do set CDate=%%b%
)

REM Let's see the result.
:: echo %dow% %yy%-%mm%-%dd% @ %hh%:%min%:%ss%
SET log=%LOGGING_DIR%\%me%.%CDate%_%CTime%.txt
echo Starting at %date% %time% >>%log%

For %%A in ("%LOGFILE%") do (
    set DIRECTORY=%%~dpA
    set FILE=%%~nxA
    set FILENAME=%%~nA
    set EXTFILE=%%~xA
)

For %%A in ("%ARGUMENT%") do (
    set FILEARGUMENT=%%~nxA
)

For %%A in ("%EXE%") do (
    set EXENOEXT=%%~nA
)


:: define new file log
set NEWFILE=%FILENAME%%CDATE%%EXTFILE%
set FULLNEWFILE=%DIRECTORY%%NEWFILE%
echo %LOGFILE% %DIRECTORY% %FILE% %FILENAME% %EXTFILE% %NEWFILE% %FULLNEWFILE%>>%log%
echo %FILEARGUMENT%>>%log%

echo "Checking for exe and argument">>%log%
set VAR=1
echo %SystemRoot%\system32\wbem\wmic.exe process where "name='%EXE%'" get ProcessID^, Commandline ^| %SystemRoot%\system32\findstr.exe /I /R /N /C:"%EXENOEXT% *%FILEARGUMENT%" ^| %SystemRoot%\system32\find.exe /i "%FILEARGUMENT%" /c >> %log%
for /f  %%i in ('%SystemRoot%\system32\wbem\wmic.exe process where "name='%EXE%'" get ProcessID^, Commandline ^| %SystemRoot%\system32\findstr.exe /I /R /N /C:"%EXENOEXT% *.*%FILEARGUMENT%" ^| %SystemRoot%\system32\find.exe /i "%FILEARGUMENT%" /c') do set VAR=%%i

echo Number of matchesA is: %VAR% >>%log%
IF /I "%VAR%" GEQ "1" (
	echo Already appA running>>%log%
	echo "Stopping converter">>%log%
	IF "M%CONTAINER%"=="M" (
			cmd /K "%EXE% %ARGUMENT% --s & timeout /t 30 & ren %LOGFILE% %NEWFILE% & %EXE% %ARGUMENT% --r & %EXE% %ARGUMENT% --n %PROCESSES%"
	) ELSE (
			cmd /K "%WITHCONTAINER% & %EXE% %ARGUMENT% --s & timeout /t 30 & ren %LOGFILE% %NEWFILE% & %EXE% %ARGUMENT% --r & %EXE% %ARGUMENT% --n %PROCESSES%"
	)

) ELSE EXIT /B 0

