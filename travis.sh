#!/bin/sh
# Alexander Couzens <lynxis@fe80.eu>
#
# travis script

cd ..
export WORKSPACE=$PWD
export PATH=/usr/bin/:/usr/sbin:/usr/local/bin:/usr/local/sbin:/bin:/sbin
unset VIRTUAL_ENV
exec $(dirname $0)/jenkins.sh
