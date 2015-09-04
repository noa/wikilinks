#! /usr/bin/env python

import codecs
import os
import argparse
import sys
import glob
import operator
from multiprocessing import Pool
from collections import defaultdict
from functools import partial

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lemmas', required=True)
    parser.add_argument('--glob')
    parser.add_argument('--path')
    parser.add_argument('--output', default="lemma_token_freq.txt")
    parser.add_argument('--max', default=1000)
    parser.add_argument('--n', default=12)
    return parser.parse_args()

def read_lemmas(path):
    ret = set()
    for line in open(path):
        tokens = line.rstrip().split('\t')
        ret.add(tokens[0].upper())
    return ret

def is_named_entity(tag):
    if len(tag) > 2 and tag[0:2] == "B-" or tag[0:2] == "I-":
        return True
    return False

def count(args, lemmas, path):
    print('counting: %s' % (path))
    stats = defaultdict(int)
    for line in codecs.open(path, 'r', 'utf-8'):
        tokens = line.rstrip().split()
        if len(tokens) == 2:
            tag = tokens[1]
            if not is_named_entity(tag):
                word = tokens[0].upper()
                if word in lemmas:
                    stats[word] += 1
    return stats

def merge_counts(stats):
    ret = defaultdict(int)
    for s in stats:
        for k, v in s.items():
            ret[k] += v
    return ret

def main():
    args = get_args()
    stats = []
    lemmas = read_lemmas(args.lemmas)
    print(str(len(lemmas)) + ' lemmas')
    p = Pool(args.n)
    count_with_args = partial(count, args, lemmas)

    if args.glob:
        for s in p.map(count_with_args, glob.glob(args.glob)):
            stats.append(s)

    if args.path:
        for s in p.map(count_with_args, args.path):
            stats.append(s)

    print('reducing stats...')
    s = merge_counts(stats)
    sorted_s = sorted(s.items(), key=operator.itemgetter(1))
    print('stats size: ' + str(len(s)))
    print('stats size: ' + str(len(sorted_s)))

    print('writing results...')
    ouf = codecs.open(args.output, 'w', 'utf-8')
    for t in sorted_s:
        ol = t[0] + u" " + str(t[1])
        if args.output:
            ouf.write(ol + u"\n")
        else:
            print(ol)


if __name__ == "__main__":
    main()

# eof
