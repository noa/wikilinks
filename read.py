#! /usr/bin/env python3

import gzip
import zlib


import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Import thrift types
import sys
#sys.path.append('gen-py')
sys.path.append('/home/nick/Work/wikilinks/gen-py/edu/umass/cs/iesl/wikilink/expanded/data')
import constants
import ttypes

decompressed_data = gzip.open('001.gz').read()
transportIn = TTransport.TMemoryBuffer(decompressed_data)
protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
item = WikiLinkItem()
item.read(protocolIn)
serialized = transportIn.getvalue()
print(serialized)

sys.exit(0)

with gzip.open('001.gz') as f:
        file_content = f.read()
        transportIn = TTransport.TMemoryBuffer(file_content)
        protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
        item = WikiLinkItem()
        item.read(protocolIn)
        serialized = transportIn.getvalue()
        print(serialized)
