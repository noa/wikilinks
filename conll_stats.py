#! /usr/bin/env python

import os
import sys
import glob
import argparse
import operator

from collections import defaultdict
from multiprocessing import Pool

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action='append')
    parser.add_argument("--glob", action='store')
    parser.add_argument("-n", action='store', type=int)
    return parser.parse_args()

def count(path):
    stats = defaultdict(int)
    for line in open(path):
        tokens = line.rstrip().split()
        if len(tokens) == 2:
            bio_tag = tokens[1]
            tag = bio_tag[2:]
            stats[tag] += 1
    return stats

def reduce(stats):
    ret = defaultdict(int)
    for s in stats:
        for k, v in s.items():
            ret[k] += v
    return ret

def main():
    args = get_args()
    stats = []

    p = Pool(args.n)

    if args.glob:
        for s in p.map(count, glob.glob(args.glob)):
            stats.append(s)

    if args.path:
        for s in p.map(count, args.path):
            stats.append(s)

    s = reduce(stats)
    sorted_s = sorted(s.items(), key=operator.itemgetter(1))
    for t in sorted_s:
        print("%s : %u" % (t[0], t[1]))

    return 0

if __name__ == "__main__":
    sys.exit(main())
