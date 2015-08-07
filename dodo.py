import os

def task_thrift2conll():
    for file in os.listdir("."):
        if file.endswith(".gz"):
            name = os.path.basename(file)
            base_name = os.path.splitext(name)[0]
            yield {
                'basename': 'thrift2conll',
                'name': base_name,
                'actions': ['python read.py --input %s --output %s' % (file, base_name+".conll")]
            }
