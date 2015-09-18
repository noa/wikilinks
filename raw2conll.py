#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import redis
from bs4 import BeautifulSoup
import lxml
from lxml import etree, cssselect, html
#from urlparse import urlparse
from functools import partial
#import urllib
from urllib.parse import urlparse
import codecs
import sys
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)
import string
import ftfy
import re
import os
import argparse
import gzip
import zlib
#import HTMLParser
import pprint
import ftfy
import subprocess
from timeit import default_timer as timer
import sys

# import thrift
# from thrift import Thrift
# from thrift.transport import TSocket
# from thrift.transport import TTransport
# from thrift.protocol import TBinaryProtocol

# sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')
# from constants import *
# from ttypes import *

import io
import thriftpy
from thriftpy.transport import TTransportException, TTransportBase
#from thriftpy.transport.buffered import TCyBufferedTransportFactory
from thriftpy.transport.buffered import TCyBufferedTransport
from thriftpy.protocol import TBinaryProtocol
wikilinks_thrift = thriftpy.load("wiki-link-v0.1.thrift", module_name="wikilinks_thrift")
from wikilinks_thrift import *

from threading import Timer, Event

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='compressed input')
    parser.add_argument('output', help='output')
    parser.add_argument('--max-item', type=int, default=sys.maxsize)
    parser.add_argument('--max-snippet-length', type=int, default=sys.maxsize)
    parser.add_argument('--print-stats', action='store_true')
    parser.add_argument('--redis-port', type=int, default=6379)
    parser.add_argument('--redis-host', default="localhost")
    parser.add_argument('--redis-dump-file', default="wiki_types.rdb")
    parser.add_argument('--exclude')
    parser.add_argument('--include')
    return parser.parse_args()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def to_utf8(s):
    ret = ftfy.fix_text(unicode(s,'utf8'))
    ret = ret.replace(u' ', u' ')
    ret = ret.replace(u'\n',u' ')
    return ret

def keep_mention(m):
    anchor_text = m[0]

    if is_number(anchor_text):
        return False

    if len(anchor_text) < 5:
        return False

    return True

def text_from_html(html):
    soup = BeautifulSoup(html)

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract() # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    #lines = (line.strip() for line in text.splitlines())

    # break multi-headlines into a line each
    #chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # drop blank lines
    #text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

def get_redis(host, port, dump_file):
    return redis.StrictRedis(host=host, port=port, db=0)

def types_from_title_with_redis(r, title):
    key = title.replace("_", " ")
    return r.smembers(key)

def get_context_tokens(text):
    return [ (token, '?') for token in text.split() ]

def process_item(item, stats, r, args, output):

    stats['total_item'] += 1

    if not item.content.dom:
        stats['no_dom'] += 1
        return

    if not item.mentions:
        stats['no_mentions'] += 1
        return

    try:
        keep_els = set()
        parser = etree.XMLParser(ns_clean=True, recover=True)
        doc = lxml.etree.fromstring(item.content.dom)
        for element in doc.iter(tag=etree.Element):
            if element.tag == "a":
                href = element.get("href")
                if href:
                    if href.find("wikipedia") >= 0:
                        # mention_types = types_from_title_with_redis(r, title)
                        # if len(mention_types) < 1:
                        #     stats['mention_type_not_found'] += 1
                        #     continue
                        keep_els.add(element.getparent())

        for el in keep_els:
            tokens = get_context_tokens(el.text)
            if el.tail:
                tokens += get_context_tokens(el.tail)
            for child in el:
                # Handle text
                if child.tag == "a" and child.get("href") and child.text:
                    href = child.get("href")
                    if href.find("wikipedia") >= 0:
                        #mention_types = types_from_title_with_redis(r, title)
                        tokens += [ (child.text, href) ]
                    else:
                        tokens += get_context_tokens(child.text)
                else:
                    if child.text:
                        tokens += get_context_tokens(child.text)
                # Handle tail
                if child.tail:
                    tokens += get_context_tokens(child.tail)

            for t in tokens:
                output.write(t[0] + u'\t' + t[1] + u'\n')
            output.write('\n')

    except lxml.etree.XMLSyntaxError:
        stats['xml_syntax_error'] += 1

def process_item_old_2(item, stats, r, args, output):
    stats['total_item'] += 1

    if not item.content.dom:
        stats['no_dom'] += 1
        return

    if not item.mentions:
        stats['no_mentions'] += 1
        return

    # Get the soup
    soup = BeautifulSoup(item.content.dom)

    # Find all Wikipedia links
    for a in soup.find_all("a"):
        print(a)

def process_item_old(item, stats, r, args, output):
    stats['total_item'] += 1

    if not item.content.dom:
        stats['no_dom'] += 1
        return

    if not item.mentions:
        stats['no_mentions'] += 1
        return

    nmentions = len(item.mentions)
    #print('num mentions: ' + str(nmentions))
    stats['total_mention'] += len(item.mentions)

    # 1. Get text
    text = text_from_html(item.content.dom)

    # 2. Find all the mentions
    idx = 0
    replaced = 0
    minfo = []
    for mention in item.mentions:
        wiki_url = mention.wiki_url
        title = os.path.split(urlparse(wiki_url).path)[-1]
        mention_types = types_from_title_with_redis(r, title)
        if len(mention_types) < 1:
            stats['mention_type_not_found'] += 1
            continue
        #mention_type = mention_types.pop()
        anchor_text = to_utf8(mention.anchor_text)
        m = (anchor_text, mention_types)
        if not keep_mention(m):
            stats['skipped_mentions'] += 1
            continue
        minfo += [m]
#        print(anchor_text)
        text = text.replace(anchor_text, ' __MEN:'+str(idx)+'__ ')
        replaced += 1
        idx += 1
        ##################################012345

    if replaced < 1:
        stats['none_replaced'] += 1
        return

    # 3. Write the results
    for token in text.split():
        stats['total_num_tokens'] += 1
        if token.startswith("__MEN:"):
            stats['actual_num_mentions'] += 1
            #print(token)
            idx = int(token[6:-2])
            m = item.mentions[idx]
            wiki_url = item.mentions[idx].wiki_url
            anchor_text = minfo[idx][0]
            wiki_types = minfo[idx][1]
            output.write(anchor_text+'\t'+' '.join(wiki_types)+'\n')
        else:
            output.write(token+'\t'+'?\n')
            stats['total_num_unknown_tokens'] += 1
    output.write('\n')

def print_stats(stats):
    print("Statistics:")
    for key in sorted(stats.keys()):
        print(key + " : " + str(stats[key]))

def run(args, r, include_set, exclude_set):
    p = subprocess.Popen(["zcat", args.input], stdout = subprocess.PIPE)
    #fh = io_method(p.communicate()[0])
    fh = io.BytesIO(p.communicate()[0])
    assert p.returncode == 0

    #transport = TTransport.TBufferedTransport(fh)
    #protocolIn = TBinaryProtocol.TBinaryProtocol(transport)

    transport = TCyBufferedTransport(fh)
    protocolIn = TBinaryProtocol(transport)

    item = WikiLinkItem()

    stats = dict()
    stats['total_num_unknown_tokens'] = 0
    stats['total_num_tokens'] = 0
    stats['no_dom'] = 0
    stats['xml_syntax_error'] = 0
    stats['no_mention'] = 0
    stats['total_item'] = 0
    stats['total_mention'] = 0
    stats['none_replaced'] = 0
    stats['mention_type_not_found'] = 0
    stats['actual_num_mentions'] = 0
    stats['skipped_mentions'] = 0

    start_time = time.time()
    output = codecs.open(args.output, 'w', 'utf-8')

    i = 0
    while not item == None and i < args.max_item:
        try:
            item.read(protocolIn)
        except EOFError:
            item = None
            break

        process_item(item, stats, r, args, output) # work done here

        curr_time = time.time()
        if curr_time > start_time+5:
            print_stats(stats)
            start_time = curr_time

        i += 1

        if i >= args.max_item:
            print('hit max item; stopping early')
            break

    print_stats(stats)

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
    run(args, r, include_set, exclude_set)

if __name__ == "__main__":
    main()
