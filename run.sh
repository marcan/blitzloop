#!/bin/bash
cd `dirname $0`
while xdpyinfo ; do
	blitzloop -fs ../songs 1024 768 2>&1 | tee -a /tmp/blitzloop-log.txt
	sleep 1
done
