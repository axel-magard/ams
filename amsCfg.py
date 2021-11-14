from configparser import NoOptionError

def cfgGet(cfg, s, opt):
    try:
        r = cfg.get(s,opt).strip()
    except NoOptionError:            
        r = None
    return r    

def getOutputItems(cfg, what="Line and Workcenter Characteristics Table"):
    l = []
    appends = []
    for i in range(100):
        s = "output%d" % i
        if cfg.has_section(s):
            if cfg.get(s,"report") == what:
                n = cfg.get(s,"name")
                if s not in appends:
                    l.append(n)
                # See whether this item is child of another item
                try:
                    a = cfg.get(s,"append")
                    appends.append(a)
                except NoOptionError: pass
        else:
            return l    

def getColumns(cfg,tname):
    try:
        c = cfg.get(tname,"columns")
    except NoOptionError:
        return []    
    else:
        return [i.strip() for i in c.split(",")]

def getXValues(cfg,tname):
    try:
        c = cfg.get(tname,"x")
    except NoOptionError:
        return ["Workcenter",]    
    else:
        return [i.strip() for i in c.split(",")]

def getCharts(cfg,tname):
    def getChart(cfg,l,tname,i=None):
        try:
            name = "chart"
            xname = "x"
            if i != None:
                name = "chart%d" % i       
                xname = "x%d" % i       
            c = cfg.get(tname,name)
        except NoOptionError:
            return l    
        else:
            l.append({"chart": name, "cols": c})
            xvalue = cfgGet(cfg, tname, xname)
            if xvalue:
                l[-1]["x"] = xvalue
            return l
    
    l = []
    getChart(cfg,l,tname)
    for i in range(100):
        cnt = len(l)        
        getChart(cfg,l,tname,i)
        if len(l) == cnt:
            break
    return l    

def getOutputItemByName(cfg,name):
    for s in cfg.sections():
        if s.startswith("output"):
            if cfg.get(s,"name") == name:
                return s
    return None        