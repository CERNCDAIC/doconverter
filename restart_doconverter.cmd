@echo off
REM Script to restart blindly the doconverter. Due to problems with EOS file system.
REM It expects three arguments:
REM   1. Number of processes
REM	  2. Virtual environment if any.
REM	  Example:
REM   %0 .\restart_doconverter.cmd 2 doconverter

REM Author: Ruben Gaspar rgaspar@cern.ch

SETLOCAL ENABLEEXTENSIONS

set /A NOT_DEFINED_VAR=-1
set /A FILE_NOT_FOUND=-2

set EXE=python.exe
set ARGUMENT=c:\doconverter\doconverter\doconverter\engines\converter_daemon.py
set PROCESSES=%~1
set CONTAINER=%~2

IF "M%PROCESSES%"=="M" (
	echo "Default we clean directories"
	EXIT /B %NOT_DEFINED_VAR%
)

IF "M%CONTAINER%"=="M" (
	echo "%CONTAINER% not provided"
) ELSE set WITHCONTAINER=c:\doconverter\doconverter\venv\Scripts\activate

IF "M%CONTAINER%"=="M" (
	start cmd /C "%EXE% %ARGUMENT% --n %PROCESSES%"
) ELSE (
	start cmd /C "%WITHCONTAINER% & %EXE% %ARGUMENT% --n %PROCESSES%"
)