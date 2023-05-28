#!/bin/bash
while [[ 1 ]]; do
	"${3:-dot}" -Tsvg $1 -o $2
	inotifywait -e modify $1
	if [[ $? != 0 ]]; then
		break
	fi
done
