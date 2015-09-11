#! /usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from urlparse import urlparse
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
        parser.add_argument('--verbose', action='store_true', default=False)
        parser.add_argument('--redis-port', type=int, default=6379)
        parser.add_argument('--redis-host', default="localhost")
        parser.add_argument('--redis-dump-file', default="wiki_types.rdb")
        parser.add_argument('--lang', default='en')
        parser.add_argument('--site', default='wikipedia')
        parser.add_argument('--exclude')
        parser.add_argument('--include')
        return parser.parse_args()

def get_redis(host, port, dump_file):
        return redis.StrictRedis(host=host, port=port, db=0)

def get_site(lang, site):
        return pywikibot.Site(lang, site)

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

def write_context(f, context):
        for tup in tokenize(context, False):
                f.write(tup[0] + u' ?\n')

def to_utf8(s):
        ret = ftfy.fix_text(unicode(s,'utf8'))
        ret = ret.replace(u' ', u' ')
        ret = ret.replace(u'\n',u' ')
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

                                left_context = to_utf8(m.context.left)
                                right_context = to_utf8(m.context.right)
                                middle_context = to_utf8(m.context.middle)
                                anchor_text = to_utf8(m.anchor_text)

                                if verbose:
                                        #print(type(m.anchor_text))
                                        #print(m.anchor_text)
                                        print(anchor_text)
                                        print(left_context)
                                        print(middle_context)
                                        print(right_context)
                                        print('')

                                if types == None or len(types) < 1:
                                        continue

                                nitems_with_type += 1
                                anchor_tokens = tokenize(anchor_text, True)

                                if len(anchor_tokens) > 9:
                                        continue

                                t = types.pop()

                                # Keep this instance?
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

                                type_str = t.title()
                                bio_type = u"B-"+type_str
                                for token in anchor_tokens:
                                        #s = token
                                        #uni = unicode(s, 'utf-8')
                                        ouf.write(token + u' ' + bio_type + u'\n')
                                        bio_type = u"I-"+type_str

                                # Write right context
                                write_context(ouf, right_context)

                                # End this utterance
                                ouf.write('\n')

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

        if args.redis:
                r = get_redis(args.redis_host, args.redis_port, args.redis_dump_file)
                read_mentions(args.input, args.output, r, args.lang, args.verbose, include_set, exclude_set)
        else:
                print('unsupported!')
                sys.exit(1)
                site = get_site(args.lang, args.site)
                read_mentions(args.input, args.output, site, args.lang, args.verbose, include_set, exclude_set)

if __name__ == "__main__":
        main()
