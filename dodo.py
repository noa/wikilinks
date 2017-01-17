import os

WIKIDATA_DUMP=''
WIKI_TYPES='wiki_types.rdb'
#TYPE_EXCLUDE='exclude_list.txt'
#TYPE_EXCLUDE='exclude_less_than_10000.txt'

def show_cmd(task):
    return "executing... %s" % task.name

def task_download_wiki_dump():
    return {
        'actions': ['mvn exec:java -Dexec.mainClass="jhu.wikilinks.DownloadDump"'],
        'targets': ['dumpfiles'],
        'uptodate': [False],
        'verbosity': 1
    }

# this task retrieves a bunch of wikipedia entity types
# from a wikidata dump and stores them in redis
def task_wiki_types():
    return {
#        'name': "wiki2redis",
#        'actions': ['mvn exec:java'],
        'actions': ['mvn exec:java -Dexec.mainClass="jhu.wikilinks.WikiTypeProcessor" -Dexec.args="enwiki localhost 6379 20000 {}"'.format(WIKI_TYPES)],
        'targets': [WIKI_TYPES],
        'uptodate': [True],
        'verbosity': 2
    }

def task_thrift2conll():
    for f in sorted(os.listdir(".")):
        if f.endswith(".gz"):
            name = os.path.basename(f)
            base_name = os.path.splitext(name)[0]
            out_file = base_name+".conll"
            yield {
                'basename': 'thrift2conll',
                'name': base_name,
                'file_dep': [WIKI_TYPES],
                #'actions': ['python thrift2conll.py --redis --input %s --output %s --exclude %s'
                #            % (f, out_file, TYPE_EXCLUDE)],
                'actions': ['python3 thrift2conll.py --redis --input %s --output %s'
                            % (f, out_file)],
                'targets': [out_file],
                'title': show_cmd
            }

def task_conll_stats():
    STATS_OUT="statistics.txt"
    return {
        'actions': ['python3 conll_stats.py --glob "*.conll" --output %s --titles' % (STATS_OUT)],
        'targets': [STATS_OUT],
        'verbosity': 2
    }
