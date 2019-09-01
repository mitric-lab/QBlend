from ..container import RangeList

def read_indexgroups(fp, groups = None, indexoff=1):
    if groups is None:
        groups = {}
        
    if isinstance(fp, str):
        fp = open(fp, 'r')
        
    groupname = None
    for line in fp:
        line = line.strip()
        if len(line) == 0 or line[0] in (';','#'): pass
        elif line[0] == '[':
            groupname = line[1:line.index(']')].strip()
            groups[groupname] = []
        elif groupname is not None:
            items = line.split()
            for i in items:
                try:
                    groups[groupname].append(int(i)-indexoff)
                except:
                    print("Can not convert string %s to index" % i)
                    
    for name, ind in groups.items():
        groups[name] = RangeList(ind)
        
    return groups