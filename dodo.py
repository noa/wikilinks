import os

WIKI_TYPES='wiki_types.rdb'

def task_wiki_types():
    return {
#        'name': "wiki2redis",
        'actions': ['mvn exec:java'],
        'targets': [WIKI_TYPES]
    }

def task_thrift2conll():
    for file in sorted(os.listdir(".")):
        if file.endswith(".gz"):
            name = os.path.basename(file)
            base_name = os.path.splitext(name)[0]
            out_file = base_name+".conll"
            yield {
                'basename': 'thrift2conll',
                'name': base_name,
                'file_dep': [WIKI_TYPES],
                'actions': ['python thrift2conll.py --redis --input %s --output %s'
                            % (file, out_file)],
                'targets': [out_file]
            }
