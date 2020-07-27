import os

params = {}
fname = None

def init(filename='config.cfg'):
    global fname
    fname = filename
    if os.path.exists(fname):
        with open(fname, 'r') as f:
            for line in f:
                if (line.find('=') < 0) :
                    continue
                prm = line.split("=")
                paramName = prm[0].strip()
                paramVal = prm[1].strip()
                if (paramVal.find(',') >= 0):
                    paramVal = [s.strip() for s in paramVal.split(',')]
                    pass
                params[paramName] = paramVal

    return params

    pass


def get(paramname, default=None):
    return params.get(paramname, default)
    pass


def set(paramname, value):
    params[paramname] = value
    __saveAll()

    pass

def sets(paramlist):
    for i in paramlist:
        params[i] = paramlist[i]
    __saveAll()
    pass

def saveAll():
    __saveAll()
    pass

def __saveAll():
    with open(fname, 'w') as f:
        for i in params:
            if (isinstance(params[i], (list,tuple))):
                f.write("%s = %s,\n" % (i, ','.join(params[i]),))
            else:
                f.write("%s = %s\n" % (i, params[i],))
    pass



