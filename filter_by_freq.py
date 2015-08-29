#! /usr/bin/env python3

import os
import sys
import glob

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    # conditions
    parser.add_argument("--gt", type=int)

    return parser.parse_args()

def run(args):
    nleftover = 0
    out = open(args.output, 'w')
    for line in open(args.input):
        tokens = line.rstrip().split()
        t = tokens[0]
        f = int(tokens[1])

        # check reasons to exclude t
        if args.gt and f < args.gt:
            continue

        out.write(line)

if __name__ == "__main__":
    args = get_args()
    run(args)

# eof
