#!/bin/bash
cd `dirname $0`
export PYTHONPATH=src/build/lib.linux-x86_64-2.7/
while xdpyinfo ; do
	python -u src/main.py -fs ../songs 1024 768 2>&1 | tee -a /tmp/blitzloop-log.txt
	sleep 1
done
