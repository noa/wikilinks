import os

WIKI_TYPES='wiki_types.rdb'

def task_wiki_types():
    return {
#        'name': "wiki2redis",
        'actions': ['mvn exec:java'],
        'targets': [WIKI_TYPES],
        'uptodate': [True]
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
                'actions': ['python thrift2conll.py --redis --input %s --output %s'
                            % (f, out_file)],
                'targets': [out_file]
            }
