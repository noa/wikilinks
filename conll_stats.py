#! /usr/bin/env python

import os
import sys
import glob
import argparse
import operator
import pywikibot
import pprint
from pywikibot.data import api
import codecs
from collections import defaultdict
from multiprocessing import Pool

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action='append')
    parser.add_argument("--glob", action='store')
    parser.add_argument("-n", action='store', type=int)
    parser.add_argument("--lang", default='en')
    parser.add_argument("--site", default='wikipedia')
    parser.add_argument("--output", action='store', type=str)
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

def get_wiki(lang, site):
    return pywikibot.Site(lang, site)

def get_type_label(wiki, t):
    try:
        item = pywikibot.ItemPage(wiki, t)
        item.get()
        #sitelinks = item.sitelinks
        #aliases = item.aliases
        if 'en' in item.labels:
            #print('The label in English is: ' + item.labels['en'])
            return item.labels['en']
        else:
            return None
    except:
        return None

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
    site = get_wiki(args.lang, args.site)
    repo = site.data_repository()
    ouf = codecs.open(args.output, 'w', 'utf-8')
    for t in sorted_s:
        l = get_type_label(repo, t[0])
        if l == None:
            l = "UNK"
        #print(t[0], l, t[1])
        #print(t[0] + " " + l + " " + str(t[1]))
        ol = "%10s %50s %10u" % (t[0],l,t[1])
        if args.output:
            ouf.write(ol+"\n")
        else:
            print(ol)

    return 0

if __name__ == "__main__":
    sys.exit(main())
