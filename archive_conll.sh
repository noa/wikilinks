#! /usr/bin/env bash

tar cvf - *.conll | pigz > zipped/conll.tar.gz

# eof
