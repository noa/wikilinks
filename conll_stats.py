#! /usr/bin/env python3

import os
import sys
import glob
import argparse
import operator
import pywikibot
import pprint
from functools import partial
from pywikibot.data import api
import codecs
from collections import defaultdict
from multiprocessing import Pool

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action='append')
    parser.add_argument("--titles", action='store_true')
    parser.add_argument("--vocab-mode", action='store_true')
    parser.add_argument("--no-lowercase", action='store_true')
    parser.add_argument("--glob", action='store')
    parser.add_argument("-n", action='store', type=int, default=8)
    parser.add_argument("--lang", default='en')
    parser.add_argument("--site", default='wikipedia')
    parser.add_argument("--output", action='store', type=str, default="statistics.txt")
    return parser.parse_args()

def count(args, path):
    print('counting: %s' % (path))
    stats = defaultdict(int)
    #for line in open(path):
    for line in codecs.open(path, 'r', 'utf-8'):
        tokens = line.rstrip().split()
        if len(tokens) == 2:
            bio_tag = tokens[1]

            if args.vocab_mode:
                if bio_tag == "O":
                    word = tokens[0]
                    if not args.no_lowercase:
                        word = word.lower()
                    stats[word] += 1
                else:
                    continue
            else:
                # don't count context tags
                if bio_tag == "O":
                    continue

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
            print('no label for {}'.format(t))
            return None
    except:
        return None

def main():
    args = get_args()
    stats = []

    p = Pool(args.n)
    count_with_args = partial(count, args)

    if args.glob:
        for s in p.map(count_with_args, glob.glob(args.glob)):
            stats.append(s)

    if args.path:
        for s in p.map(count_with_args, args.path):
            stats.append(s)

    print('reducing stats...')
    s = reduce(stats)
    sorted_s = sorted(s.items(), key=operator.itemgetter(1))

    site = None
    repo = None
    if args.titles:
        print('getting wiki {} in {}'.format(args.site, args.lang))
        site = get_wiki(args.lang, args.site)

        print('getting data repository...')
        repo = site.data_repository()

    print('writing results to {}'.format(args.output))
    ouf = codecs.open(args.output, 'w', 'utf-8')
    for t in sorted_s:
        l = None
        if args.titles:
            l = get_type_label(repo, t[0])
        if l == None:
            l = "UNK"
        #print(t[0], l, t[1])
        #print(t[0] + " " + l + " " + str(t[1]))
        #ol = "%10s %50s %10u" % (t[0],l,t[1])
        #ol = t[0] + " " + t[1]
        ouf.write("{} {}\n".format(str(t[0]), str(t[1])))

    return 0

if __name__ == "__main__":
    sys.exit(main())
