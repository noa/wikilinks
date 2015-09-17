#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import subprocess
import gzip
import redis
from urlparse import urlparse
import codecs
import sys
import string
import ftfy
import zlib

if sys.version.startswith("3"):
    import io
    io_method = io.BytesIO
else:
    import cStringIO
    io_method = cStringIO.StringIO

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
    parser.add_argument('input', help='compressed input')
    parser.add_argument('--n', default=5)
    return parser.parse_args()

def to_utf8(s):
        ret = ftfy.fix_text(unicode(s,'utf8'))
        ret = ret.replace(u' ', u' ')
        ret = ret.replace(u'\n',u' ')
        return ret

def process_item(item):
    print(item.url)
    if item.mentions:
        print(str(len(item.mentions)) + ' mentions')

    if not item.content.dom:
        print('no dom content!')
        return

    dom = item.content.dom
    #print(dom)

    # if not item.content.raw:
    #     print('no raw content!')
    #     return
    # if not item.content.fullText:
    #     print('no full text!')
    #     return
    # if not item.mentions:
    #     print('no mentions!')
    #     return
    for mention in item.mentions:
        offset = mention.raw_text_offset
        name = mention.anchor_text
        start = dom.find(name)

        if start < 0:
            print('cannot find name!')
            return

        print(mention.anchor_text)
        print(dom[start-20:start+20])

        #print(mention.raw_text_offset)
        #print(dom[offset:offset+10])
        #print(item.content.fullText[offset:offset+5])
    #print(item.url)
    #print(item.content.fullText)
    #print(item.content.articleText)
    #print(item.content.)

def show_progress(file_name, chunk_size=4096):
    fh = gzip.open(file_name, "r")
    total_size = os.path.getsize(file_name)
    total_read = 0
    while True:
        chunk = fh.read(chunk_size)
        if not chunk:
            fh.close()
            break
        total_read += len(chunk)
        print("Progress: %s percent" % (total_read/total_size))
        yield chunk

def run(args):
    # print('decompressing...')
    # decompressed_data = gzip.open(args.input).read()
    # print('loading memory buffer...')
    # transportIn = TTransport.TMemoryBuffer(decompressed_data)
    # transport = TTransport.TFileTransport(args.input)
    # transport = TTransport.TMemoryBuffer(gzip.open(args.input))

    #READ_BLOCK_SIZE = 1024*8
    #isGZipped = response.headers.get('content-encoding', '').find('gzip') >= 0
    #d = zlib.decompressobj(16 + zlib.MAX_WBITS)

    p = subprocess.Popen(["zcat", args.input], stdout = subprocess.PIPE)
    fh = io_method(p.communicate()[0])
    assert p.returncode == 0

    transport = TTransport.TBufferedTransport(fh)
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
