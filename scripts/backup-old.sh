#!/bin/bash

# Get the current date
date=$(date "+%Y-%m-%d_%H-%M")
db_path="/root/prod/world-prod/tables"
db_file="dump.rdb"
clear_date=$(date -d "3 days ago" "+%Y-%m-%d")
files=$(find "${db_path}/backup" -type f -name "dbbackup-${clear_date}*")
# Loop through the found files
count=0
echo "$files"
for file in $files; do
	(($count+=1))
	# Keep the first file, delete the rest
    	if [ $count -eq 1 ]; then
        	echo "Keeping file: $file"
    	else
        	echo "Deleting file: $file"
        	rm "$file"
    fi
done
