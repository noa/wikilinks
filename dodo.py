import os

WIKI_TYPES='wiki_types'

def task_wiki_types():
    return {
        'name': "wiki_types",
        'actions': 'mvn exec:java',
        'targets': ['titles.rdb']
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
                'actions': ['python read.py --input %s --output %s --types %s'
                            % (file, out_file, wiki_types)],
                'targets': [out_file]
            }
