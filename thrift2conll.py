#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import redis
import logging
#from urlparse import urlparse # python2
from urllib.parse import urlparse # python3
import codecs
import sys
#sys.stdout = codecs.getwriter('utf8')(sys.stdout)
import string
import ftfy
import os
import argparse
import gzip
import zlib
import html.parser #python3
#import HTMLParser #python2
import pprint
from timeit import default_timer as timer

try:
    from io import StringIO
except ImportError:
    from io import StringIO

import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# import thriftpy

# wikilink_thrift = thriftpy.load("wiki-link-v0.1.thrift", module_name="wikilink_thrift")

import sys
#sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')
sys.path.append('./gen-py')

#import thrift types
from wikilinks.constants import *
from wikilinks.ttypes import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='compressed input', required=True)
    parser.add_argument('--output', help='output path', required=True)
    parser.add_argument('--redis', action='store_true')
    parser.add_argument('--verbose', action='store_true', default=False)
    parser.add_argument('--redis-port', type=int, default=6379)
    parser.add_argument('--redis-host', default="localhost")
    parser.add_argument('--redis-dump-file', default="wiki_types.rdb")
    parser.add_argument('--lang', default='en')
    parser.add_argument('--site', default='wikipedia')
    parser.add_argument('--exclude')
    parser.add_argument('--include')
    parser.add_argument('--logfile', default='thrift2conll.log')
    return parser.parse_args()

def get_redis(host, port, dump_file):
    return redis.StrictRedis(host=host, port=port, db=0)

def get_lemma(token):
    if token.find('http') >= 0:
        return 'URL'

    if token.isdigit() or any(char.isdigit() for char in token):
        return 'NUMBER'

    ret = token.upper()
    return ret

# `test` -> [`, test, `]
# test. -> [test, .]
def subtok(token):
    ret = []
    tlen = len(token)

    if tlen == 1:
        return [token]

    if tlen < 4:
        return [token]

    lp = False
    rp = False
    lstrip = token.lstrip(string.punctuation)
    ldiff = tlen - len(lstrip)
    if ldiff > 0:
        lp = True
        ret += [ token[0:ldiff] ]
        token = token[ldiff:]
    rstrip = token.rstrip(string.punctuation)
    rdiff = tlen - len(rstrip)
    if not len(rstrip) == tlen:
        rp = True
        ret += [ token[0:-rdiff] ]
        ret += [ token[-rdiff:]  ]

    if not rp:
        ret += [ token ]

    return ret

def tokenize(s, ne):
    ret = []
    for token in s.split():
        if not ne: # not a named-entity
            subtokens = subtok(token)
            assert len(subtokens) > 0
            for tok in subtokens:
                ret.append(tok)
        else: # is a named-entity, gotta be careful about e.g. U.S.
            ret.append(token)
    if ne:
        return ret
    else:
        return [ (x, get_lemma(x)) for x in ret ]

def types_from_title_with_redis(r, title):
    #print('fetching types for: ' + title)
    key = title.replace("_", " ")
    return r.smembers(key)

def write_context(f, context):
    for tup in tokenize(context, False):
        f.write(tup[0] + ' ?\n')

def to_utf8(s):
    #ret = ftfy.fix_text(str(s,'utf8'))
    #s = unicode(s, "utf-8")
    ret = ftfy.fix_text(s)
    ret = ret.replace(' ', ' ')
    ret = ret.replace('\n',' ')
    return ret

def read_mentions(inpath, outpath, wiki, lang, verbose, include_set, exclude_set):
    ouf = codecs.open(outpath, 'w', 'utf-8')
    #ouf = open(outpath, 'w')
    #tok_regex = re.compile(r'[%s\s]+' % re.escape(string.punctuation))
    decompressed_data = gzip.open(inpath).read()
    transportIn = TTransport.TMemoryBuffer(decompressed_data)
    protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
    item = WikiLinkItem()
    nitems = 0
    nitems_with_context = 0
    nitems_with_type = 0
    start = timer()
    while not item == None:
        curr = timer()
        if curr - start > 5:
            line = "{} mentions ({} w context {} w type)".format(nitems, nitems_with_context, nitems_with_type)
            logging.info(line)
            start = timer()
        try:
            item.read(protocolIn)
        except EOFError:
            item = None
            break

        for m in item.mentions:
            nitems += 1
            if m.context == None:
                logging.warning("empty context; skipping")
                continue
            nitems_with_context += 1
            types = None
            if not m.wiki_url == None:
                title = os.path.split(urlparse(m.wiki_url).path)[-1]
                #types = types_from_title(wiki, title)
                types = types_from_title_with_redis(wiki, title)

                left_context = to_utf8(m.context.left)
                right_context = to_utf8(m.context.right)
                middle_context = to_utf8(m.context.middle)
                anchor_text = to_utf8(m.anchor_text)

                if types == None or len(types) < 1:
                    logging.warning("null types for {}".format(m.wiki_url))
                    continue

                nitems_with_type += 1
                anchor_tokens = tokenize(anchor_text, True)

                if len(anchor_tokens) > 9:
                    print('len(anchor_tokens) = {}; skipping'.format(len(anchor_tokens)))
                    continue

                t = types.pop()

                # Keep this instance?
                if (len(include_set) + len(exclude_set)) > 0:
                    if len(include_set) == 0:
                        if t in exclude_set:
                            continue
                    else:
                        if not t in include_set:
                            continue
                        if t in exclude_set:
                            continue

                # Write left context
                write_context(ouf, left_context)

                type_str = str(t.title())

                if verbose:
                    logging.info("INSTANCE:")
                    logging.info("type:" + type_str)
                    logging.info("anchor:" + anchor_text)
                    logging.info("left: " + left_context)
                    logging.info("middle: " + middle_context)
                    logging.info("right: " + right_context)

                bio_type = "B-"+type_str
                for token in anchor_tokens:
                    #s = token
                    #uni = unicode(s, 'utf-8')
                    ouf.write(token + ' ' + bio_type + '\n')
                    bio_type = "I-"+type_str

                # Write right context
                write_context(ouf, right_context)

                # End this utterance
                ouf.write('\n')

def main():
    args = get_args()

    # set up logging
    logging.basicConfig(filename=args.input+'.log', filemode='w')

    include_set = set()
    if args.include:
        for line in open(args.include):
            tokens = line.rstrip().split()
            include_set.add(tokens[0])

    logging.info("include set size = {}".format(len(include_set)))

    exclude_set = set()
    if args.exclude:
        for line in open(args.exclude):
            tokens = line.rstrip().split()
            exclude_set.add(tokens[0])

    logging.info("exclude set size = {}".format(len(exclude_set)))

    if args.redis:
        r = get_redis(args.redis_host, args.redis_port, args.redis_dump_file)
        sz = r.dbsize()
        logging.info("redis DB num keys = {}".format(sz))
        if sz < 0:
            raise ValueError('empty redis DB')
        read_mentions(args.input, args.output, r, args.lang, args.verbose, include_set, exclude_set)
    else:
        raise ValueError('unsupported! must use redis')

if __name__ == "__main__":
    main()
