#! /usr/bin/env python

import gzip
import zlib

import pywikibot
import pprint
from pywikibot.data import api

def getItems(site, itemtitle):
        params = { 'action' : 'wbsearchentities',
                   'format' : 'json',
                   'language' : 'en',
                   'type' : 'item',
                   'search': itemtitle}
        request = api.Request(site=site,**params)
        return request.submit()

def getItem(site, wdItem, token):
        request = api.Request(site=site,
                              action='wbgetentities',
                              format='json',
                              ids=wdItem)
        return request.submit()

def prettyPrint(variable):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(variable)

try:
        from StringIO import StringIO
except ImportError:
        from io import StringIO

import thrift
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Import thrift types
import sys
sys.path.append('./gen-py/edu/umass/cs/iesl/wikilink/expanded/data')

#import constants
#import ttypes

#print(dir(constants))
#print(dir(ttypes))

from constants import *
from ttypes import *

# Login to Wikipedia
wikipedia_site = pywikibot.Site("en", "wikipedia")
page1 = pywikibot.Page(wikipedia_site, u"Douglas Adams")
item = pywikibot.ItemPage.fromPage(page1)

#dictionary = item.get()
#print dictionary

item.get()  # you need to call it to access any data.
sitelinks = item.sitelinks
aliases = item.aliases
if 'en' in item.labels:
        print('The label in English is: ' + item.labels['en'])
if item.claims:
        if 'P31' in item.claims: # instance of
                print(item.claims['P31'])
                print(len(item.claims['P31']))
                for c in item.claims['P31']:
                        print(str(c))
                        print(dir(c))
                        print(c.getTarget())
                        print(c.target)
                print(item.claims['P31'][0].getTarget())
                print(item.claims['P31'][0].sources[0])  # let's just assume it has sources.

sys.exit(0)

# Login to Wikidata
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()
item = pywikibot.ItemPage(repo, 'Q42')
dictionary = item.get()
print dictionary
print dictionary.keys()
#print item

sys.exit(0)

#token = repo.token(pywikibot.Page(repo, 'Main Page'), 'edit')
#wikidataEntries = getItems(site, "Google")
# Print the different Wikidata entries to the screen
#prettyPrint(wikidataEntries)

# Print each wikidata entry as an object
#for wdEntry in wikidataEntries["search"]:
#   prettyPrint(getItem(site, wdEntry["id"], token))

decompressed_data = gzip.open('001.gz').read()
transportIn = TTransport.TMemoryBuffer(decompressed_data)
protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
item = WikiLinkItem()
while not item == None:
        item.read(protocolIn)
        #print(item)
        for m in item.mentions:
                if not m.context == None:
                        print('anchor text: ' + m.anchor_text)
                        print('left:' + m.context.left)
                        print('middle:' + m.context.middle)
                        print('right:' + m.context.right)
                        #print('freebase id: ' + m.freebase_id)
                        print('wiki_url: ' + m.wiki_url)
                        print('')
        #serialized = transportIn.getvalue()
        #print(type(serialized))

sys.exit(0)

with gzip.open('001.gz') as f:
        file_content = f.read()
        transportIn = TTransport.TMemoryBuffer(file_content)
        protocolIn = TBinaryProtocol.TBinaryProtocol(transportIn)
        item = WikiLinkItem()
        item.read(protocolIn)
        serialized = transportIn.getvalue()
        print(serialized)
