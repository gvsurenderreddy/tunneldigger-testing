#!/bin/sh
# Alexander Couzens <lynxis@fe80.eu>
#
# travis script

export WORKSPACE=$PWD

exec $(dirname $0)/jenkins.sh
