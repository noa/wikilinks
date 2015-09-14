#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import gzip
import redis
from urlparse import urlparse
import codecs
import sys
import string
import ftfy

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TZlibTransport
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

import sys
sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')

# import thrift types
from constants import *
from ttypes import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='compressed input')
    parser.add_argument('--n', default=1)
    return parser.parse_args()

def to_utf8(s):
        ret = ftfy.fix_text(unicode(s,'utf8'))
        ret = ret.replace(u' ', u' ')
        ret = ret.replace(u'\n',u' ')
        return ret

def process_item(item):
    print(item.url)
    print(item.content.fullText)
    print(item.content.articleText)

def run(args):
    # print('decompressing...')
    # decompressed_data = gzip.open(args.input).read()
    # print('loading memory buffer...')
    # transportIn = TTransport.TMemoryBuffer(decompressed_data)
    # transport = TTransport.TFileTransport(args.input)
    # transport = TTransport.TMemoryBuffer(gzip.open(args.input))

    transport = TTransport.TMemoryBuffer(open(args.input))
    # transport = TTransport.TBufferedTransport(transport)
    transport = TZlibTransport.TZlibTransport(transport)

    print('setting up binary protocol...')
    protocolIn = TBinaryProtocol.TBinaryProtocol(transport)
    item = WikiLinkItem()
    i = 0
    while not item == None and i < args.n:
        print('item ' + str(i) + '...')
        try:
            item.read(protocolIn)
        except EOFError:
            item = None
            break

        # process an item
        process_item(item)

        i += 1

def main():
    args = get_args()
    run(args)

if __name__ == "__main__":
    main()
