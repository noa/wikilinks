#! /usr/bin/env python3

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

with gzip.open('001.gz', 'rb') as f:
        file_content = f.read()
        transportIn = TTransport.TMemoryBuffer(file_content)
        protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
        msg.read(protocolIn)
        serialized = transportIn.getvalue()
