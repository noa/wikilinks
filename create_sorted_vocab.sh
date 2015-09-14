#! /usr/bin/env bash

LEMMA="en_closed_class_lemmas.txt"
OUTPUT="sorted_vocab.txt"

python get_vocab_from_lemma_freq.py --lemmas $LEMMA \
       --glob "*.conll" \
       --output $OUTPUT \

# eof
