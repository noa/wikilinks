#! /usr/bin/env python3

import os
import sys
import glob
import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")

    # conditions
    parser.add_argument("--gt", type=int)

    return parser.parse_args()

def run(args):
    nleftover = 0
    out = None
    if args.output:
        out = open(args.output, 'w')
    for line in open(args.input):
        tokens = line.rstrip().split()
        t = tokens[0]
        f = int(tokens[1])

        # check reasons to exclude t
        if args.gt and f < args.gt:
            continue

        nleftover += 1

        if out:
            out.write(line)
    print(str(nleftover) + " left over")

if __name__ == "__main__":
    args = get_args()
    run(args)

# eof
