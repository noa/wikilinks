# Prerequisites #

* [Python thrift](https://pypi.python.org/pypi/thrift)
* [Maven](https://maven.apache.org/)
* [Redis server](http://redis.io/)
* [Python redis API](https://pypi.python.org/pypi/redis) 
* **(Optional)** [Python wikibot](https://github.com/wikimedia/pywikibot-core)
* **(Optional)** [Python doit](http://pydoit.org/)

Maven will take care of all dependencies for the Java code when

```
#!bash
mvn compile
```
is invoked.

# Running the tools #

## Download the Wikilinks data ##

```
#!bash
./download.sh
```

The result should be about 5.3G. You can check with
```
#!bash
du -hc *.gz
```

## Generate the Python Thrift API ##

Before running ```thrift2conll.py```, the Thrift API must be generated as follows: 
```
thrift -gen py wiki-link-v0.1.thrift
```

## Run the tools ##

If doit is installed, simply type 
```
doit
```
at the command line to (1) fetch Wikipedia types and store them in redis (2) process the compressed Thrift files into CoNLL format.

If not, see dodo.py for details on how to run each command.  