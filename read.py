#! /usr/bin/env python

#from urllib.parse import urlparse
#import urllib
#from urllib.parse import urlparse
from urlparse import urlparse
import codecs
import os
import argparse
import gzip
import zlib
import pywikibot
import pprint
from pywikibot.data import api

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
        parser.add_argument('--lang', default='en')
        parser.add_argument('--site', default='wikipedia')
        return parser.parse_args()

def get_site(lang, site):
        return pywikibot.Site(lang, site)

def tokenize(s):
        return s.split()

def types_from_title(site, title):
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

def read_mentions(inpath, outpath, site, lang):
        ouf = codecs.open(outpath, 'w', 'utf-8')
        #ouf = open(outpath, 'w')
        decompressed_data = gzip.open(inpath).read()
        transportIn = TTransport.TMemoryBuffer(decompressed_data)
        protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
        item = WikiLinkItem()
        while not item == None:
                item.read(protocolIn)
                for m in item.mentions:
                        if m.context == None:
                                continue
                        types = None
                        if not m.wiki_url == None:
                                title = os.path.split(urlparse(m.wiki_url).path)[-1]
                                types = types_from_title(site, title)
                                if types == None:
                                        continue
                                #print(type(m.anchor_text))
                                anchor_tokens = tokenize(m.anchor_text)
                                #print(type(anchor_tokens))
                                if len(anchor_tokens) > 9:
                                        continue
                                t = types[0]
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
        site = get_site(args.lang, args.site)
        read_mentions(args.input, args.output, site, args.lang)

if __name__ == "__main__":
        main()
