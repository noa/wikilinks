#! /usr/bin/env bash

LEMMA="en_closed_class_lemmas.txt"
OUTPUT="vocab.txt"
MAX=25000

python get_vocab_from_lemma_freq.py --lemmas $LEMMA \
       --glob "*.conll" \
       --output $OUTPUT \
       --max $MAX

# eof
