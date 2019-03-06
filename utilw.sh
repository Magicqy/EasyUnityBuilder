#!/bin/bash
cur_dir=`dirname $0`
python ${cur_dir}/buildutil.py $*
echo exitcode = $?