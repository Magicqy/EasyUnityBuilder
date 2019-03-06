@echo off
@python %~dp0\buildutil.py %*
echo exitcode = %errorlevel%