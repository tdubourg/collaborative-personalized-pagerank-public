#!/bin/bash

kill -KILL `ps -efal | grep $1 | grep -vE '(grep|kill_multiproc_program)' | cut -d ' ' -f 7,8`
