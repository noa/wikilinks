#! /usr/bin/env bash

for (( i=1; i<110; i++)) do echo "Downloading file $i of 109"; f=`printf "%03d" $i` ; wget http://iesl.cs.umass.edu/downloads/wiki-link/context-only/$f.gz ; done ; echo "Downloaded all files, verifying MD5 checksums (might take some time)" ; diff --brief <(wget -q -O - http://iesl.cs.umass.edu/downloads/wiki-link/context-only/md5sum) <(md5sum *.gz) ; if [ $? -eq 1 ] ; then echo "ERROR: Download incorrect\!" ; else echo "Download correct" ; fi

#eof
