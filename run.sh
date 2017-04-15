#!/bin/sh

. python_env/bin/activate

ACTION=$1
if [ -z $ACTION ]; then
    ACTION="start"
fi

buildbot $ACTION master
