#! /usr/bin/env bash

##
# This script will copy all of the specified files to the destination
# usage ./copy.sh file1 file2 ... fileN destination/
#

numberOfArgs=$#

if [ $numberOfArgs -le 0 ]; then
    echo "Usage: ./copy.sh file1 file2 ... fileN destination/" >&2
    exit 1
elif [ $numberOfArgs -le 1 ]; then
    echo "You must specify a destination" >&2
    exit 1
fi

destination=${@: -1}

for (( i=1; i<$numberOfArgs; i++ )); do
    echo "# ${1}"
    cp "${1}" "$destination"
    echo "$(( (i * 100) /numberOfArgs ))"
    sleep 0.5  #So that you can see the items being copied
    shift 1
done | zenity --progress --title="Copy files to $destination" --percentage=0

if [ "$?" -eq 1 ]; then
    zenity --error --text="Copy Aborted"
    exit 1
fi
