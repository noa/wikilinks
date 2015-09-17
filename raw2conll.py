#! /usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from urlparse import urlparse
import urllib
import codecs
import sys
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
import string
import ftfy
import os
import argparse
import gzip
import zlib
import HTMLParser
import pprint
import ftfy
import subprocess
from timeit import default_timer as timer

import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

if sys.version.startswith("3"):
    import io
    io_method = io.BytesIO
else:
    import cStringIO
    io_method = cStringIO.StringIO

import sys
sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')

# import thrift types
from constants import *
from ttypes import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='compressed input')
    parser.add_argument('output', help='output')
    parser.add_argument('--max-item', default=sys.maxsize)
    parser.add_argument('--print-stats', action='store_true')
    parser.add_argument('--redis-port', type=int, default=6379)
    parser.add_argument('--redis-host', default="localhost")
    parser.add_argument('--redis-dump-file', default="wiki_types.rdb")
    parser.add_argument('--exclude')
    parser.add_argument('--include')
    return parser.parse_args()

def to_utf8(s):
    ret = ftfy.fix_text(unicode(s,'utf8'))
    ret = ret.replace(u' ', u' ')
    ret = ret.replace(u'\n',u' ')
    return ret

def text_from_html(dom):
    soup = BeautifulSoup(html)

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract() # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

def get_redis(host, port, dump_file):
    return redis.StrictRedis(host=host, port=port, db=0)

def types_from_title_with_redis(r, title):
    key = title.replace("_", " ")
    return r.smembers(key)

def types_from_title(wiki, title):
    if type(wiki) == redis.client.StrictRedis:
        return types_from_title_with_redis(wiki, title)

def process_item(item, stats):
    stats['total_item'] += 1

    if not item.content.dom:
        stats['no_dom'] += 1
        return

    print(item.url)

def print_stats(stats):
    print("Statistics:")
    for key in sorted(stats.keys()):
        print(key + " : " + str(stats[key]))

def run(args, r, include_set, exclude_set):
    p = subprocess.Popen(["zcat", args.input], stdout = subprocess.PIPE)
    fh = io_method(p.communicate()[0])
    assert p.returncode == 0
    transport = TTransport.TBufferedTransport(fh)
    protocolIn = TBinaryProtocol.TBinaryProtocol(transport)
    item = WikiLinkItem()

    stats = dict()
    stats['no dom'] = 0
    stats['no mention'] = 0
    stats['total_item'] = 0
    stats['total_mention'] = 0

    i = 0
    while not item == None and i < args.n:
        try:
            item.read(protocolIn)
        except EOFError:
            item = None
            break

        process_item(item, stats) # work done here
        i += 1

def main():
    args = get_args()

    include_set = set()
    if args.include:
        for line in open(args.include):
            tokens = line.rstrip().split()
            include_set.add(tokens[0])

    exclude_set = set()
    if args.exclude:
        for line in open(args.exclude):
            tokens = line.rstrip().split()
            exclude_set.add(tokens[0])

    r = get_redis(args.redis_host, args.redis_port, args.redis_dump_file)
    read_mentions(args.input, r, include_set, exclude_set)

if __name__ == "__main__":
    main()
