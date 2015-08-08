#! /usr/bin/env python

import redis
from urlparse import urlparse
import codecs
import os
import argparse
import gzip
import zlib
import pywikibot
import pprint
from pywikibot.data import api
from timeit import default_timer as timer

try:
        from StringIO import StringIO
except ImportError:
        from io import StringIO

import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

import sys
sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')

# import thrift types
from constants import *
from ttypes import *

def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('--input', help='compressed input', required=True)
        parser.add_argument('--output', help='output path', required=True)
        parser.add_argument('--redis', action='store_true')
        parser.add_argument('--redis-port', type=int, default=6379)
        parser.add_argument('--redis-host', default="localhost")
        parser.add_argument('--redis-dump-file', default="wiki_types.rdb")
        parser.add_argument('--lang', default='en')
        parser.add_argument('--site', default='wikipedia')
        return parser.parse_args()

def get_redis(host, port, dump_file):
        return redis.StrictRedis(host=host, port=port, db=0)

def get_site(lang, site):
        return pywikibot.Site(lang, site)

def tokenize(s):
        return s.split()

def types_from_title_with_redis(r, title):
        #print('fetching types for: ' + title)
        key = title.replace("_", " ")
        return r.smembers(key)

def types_from_title_with_pywikibot(site, title):
        try:
                page = pywikibot.Page(site, title)
                item = pywikibot.ItemPage.fromPage(page)
                dictionary = item.get()
                sitelinks = item.sitelinks
                aliases = item.aliases
                if item.claims:
                        if 'P31' in item.claims: # instance of
                                ret = []
                                for c in item.claims['P31']:
                                        ret.append(c.getTarget())
                                assert(len(ret) > 0)
                                return ret
        except pywikibot.exceptions.NoPage:
                return None
        except:
                return None
        return None

def types_from_title(wiki, title):
        if type(wiki) == pywikibot.site.APISite:
                return types_from_title_with_pywikibot(wiki, title)
        if type(wiki) == redis.client.StrictRedis:
                return types_from_title_with_redis(wiki, title)

def read_mentions(inpath, outpath, wiki, lang):
        ouf = codecs.open(outpath, 'w', 'utf-8')
        #ouf = open(outpath, 'w')
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
                        print(str(nitems)+' mentions ('+str(nitems_with_context)
                              +' w context, '+str(nitems_with_type)+' w type)')
                        start = timer()

                try:
                        item.read(protocolIn)
                except EOFError:
                        item = None
                        break

                for m in item.mentions:
                        nitems += 1
                        if m.context == None:
                                continue
                        nitems_with_context += 1
                        types = None
                        if not m.wiki_url == None:
                                title = os.path.split(urlparse(m.wiki_url).path)[-1]
                                types = types_from_title(wiki, title)
                                if types == None or len(types) < 1:
                                        continue
                                nitems_with_type += 1
                                #print(type(m.anchor_text))
                                anchor_tokens = tokenize(m.anchor_text)
                                #print(type(anchor_tokens))
                                if len(anchor_tokens) > 9:
                                        continue
                                #t = types[0]
                                t = types.pop()
                                #print(type(m.context.left))
                                for token in tokenize(m.context.left):
                                        s = token
                                        uni = unicode(s, 'utf-8')
                                        ouf.write(uni + u' O\n')
                                type_str = t.title()
                                #print(m.anchor_text + '\t' + type_str)
                                bio_type = u"B-"+type_str
                                for token in anchor_tokens:
                                        s = token
                                        uni = unicode(s, 'utf-8')
                                        ouf.write(uni + u' ' + bio_type + u'\n')
                                        bio_type = u"I-"+type_str
                                for token in tokenize(m.context.right):
                                        s = token
                                        uni = unicode(s, 'utf-8')
                                        ouf.write(uni + u' O\n')
                                ouf.write('\n')

def main():
        args = get_args()
        if args.redis:
                r = get_redis(args.redis_host, args.redis_port, args.redis_dump_file)
                read_mentions(args.input, args.output, r, args.lang)
        else:
                site = get_site(args.lang, args.site)
                read_mentions(args.input, args.output, site, args.lang)

if __name__ == "__main__":
        main()
