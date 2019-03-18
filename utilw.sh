#!/bin/bash
cur_dir=`dirname $0`
python ${cur_dir}/buildutil.py $*
BUILD_EXIT_CODE=$?
echo exitcode = $BUILD_EXIT_CODE
exit $BUILD_EXIT_CODE