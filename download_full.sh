#! /usr/bin/bash

set -e

for (( i=1; i<55; i++))
do
    echo "Downloading file $i of 109"
    f=`printf "%03d" $i`
    wget http://iesl.cs.umass.edu/downloads/wiki-link/full-content/part1/$f.gz --limit-rate=9m --directory-prefix=part1
done

echo "Downloaded all files, verifying MD5 checksums (might take some time)"
diff --brief <(wget -q -O - http://iesl.cs.umass.edu/downloads/wiki-link/full-content/part1/md5sum) <(md5sum part1/*.gz)

for (( i=55; i<110; i++))
do
    echo "Downloading file $i of 109"
    f=`printf "%03d" $i`
    wget http://iesl.cs.umass.edu/downloads/wiki-link/full-content/part2/part2/$f.gz --limit-rate=9m --directory-prefix=part2
done

if [ $? -eq 1 ]; then
    echo "ERROR: Download incorrect\!"
else
    echo "Download correct"
fi

echo "Downloaded all files, verifying MD5 checksums (might take some time)"
diff --brief <(wget -q -O - http://iesl.cs.umass.edu/downloads/wiki-link/full-content/part2/part2/md5sum) <(md5sum part2/*.gz)

# eof
