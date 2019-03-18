@echo off
@python %~dp0\buildutil.py %*
set BUILD_EXIT_CODE=%errorlevel%
echo exitcode = %BUILD_EXIT_CODE%
exit %BUILD_EXIT_CODE%