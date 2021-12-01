import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import copy
import wx.grid as gridlib
import requests, io
from PIL import Image
from amsCfg import cfgGet, getColumns, getOutputItemByName, getCharts
from amsData import dataDict, getDataDictItem, getDataDictItems, getLabel

SLASH = "/"
unitOfTime = ("sec","min","hour")

CSSStyle = """
<style>
	th, td {
	  text-align: right;
	  border-bottom: 1px solid #ddd;
      font-size: %spx;
	}
    img { width: 100%%;
    }
    div.error {
        padding: 2px;
        color: red;
        border-style: inset;
        border-color: red;
    }
</style>
"""

# CSS Styling
th_props = [
  ['text-align', 'center'],
  ['font-weight', 'bold'],
  ['color', '#6d6d6d'],
  ['background-color', '#f7f7f9'],
  ['padding-left', '20px'],
  ['padding-right', '20px'],
  ['width', 'auto'],
  ['font-size', '%spx']
  ]

td_props = [
  ['text-align', 'right'],
  ['font-size', '%spx']
  ]

styles = [
  dict(selector="th", props=th_props),
  dict(selector="td", props=td_props)
  ]

xValues = ( "Arrival Rate", "Departure Rate", "Daily Starts (SOB)", "Daily Shipments (SHIP)")
xValueAttributes = ("XVal", "DR", "SOB", "SHIP")


class guiTree:
    def __init__(self):
        self.tree = []
    def add(self, obj_id, name, treeItem):
        self.tree.append({"obj_id": obj_id, "name": name, "treeItem": treeItem})
    def get(self, obj_id, name):
        for t in self.tree:
            if t["obj_id"] == obj_id and t["name"] == name:
                return t["treeItem"]
    def delete(self, id):
        for t in self.tree:
            if t["obj_id"] == id:
                del t

# from: https://stackoverflow.com/questions/49015957/how-to-get-python-graph-output-into-html-webpage-directly
def fig_to_base64(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png',
                bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue())

def highlight_bottleneck(s,bn):
    return ['background-color:  #fadbd8' if i == bn and bn >= 0 else '' for i in range(len(s))]

def highlight_notUsed(s,notUsedList):
    return ['color:  grey' if s["Name"] in notUsedList else '' for i in range(len(s))]

def styleTable(df,fontsize):
    props1 = copy.deepcopy(th_props)
    props2 = copy.deepcopy(td_props)
    props1[-1][-1] = props1[-1][-1] % fontsize
    props2[-1][-1] = props2[-1][-1] % fontsize
    styles = [
        dict(selector="th", props=props1),
        dict(selector="td", props=props2)
    ]
    return df.style.set_table_styles(styles).render()

def formatValue(val,k,model):
    renderer = ()
    if k == "Buffer Is Floor Space":
        renderer = (gridlib.GridCellBoolRenderer(),gridlib.GridCellBoolEditor())
        # See http://wxpython-users.1045709.n5.nabble.com/problem-with-check-box-in-a-grid-td4974843.html
        if val == "1":
            return "1", renderer
        else:
            return "", renderer
    if isinstance(val,int):
        str = "%d" % val
        renderer = (gridlib.GridCellNumberRenderer(),gridlib.GridCellNumberEditor())
    elif isinstance(val,float):
        str = "%f" % val
        # gridlib.GridCellFloatEditor is not usable; throws assertion as soon as non-float value is entered.
        renderer = (gridlib.GridCellFloatRenderer(),gridlib.GridCellTextEditor())
    else:
        str = "%s" % val
        renderer = (gridlib.GridCellStringRenderer(),gridlib.GridCellTextEditor())
    if k == "Workcenter":
        str = "%s" % val
        renderer = (gridlib.GridCellEnumRenderer(model.getWorkcenterListAsString()),gridlib.GridCellChoiceEditor(model.getWorkcenterNameList()))
    return str, renderer

def RenderModelData(model):
    html = "<table><tr><td>Parts in:</td><td>%s</td><td>%s</td><tr>" % (model.inParts,"")
    html += "<tr><td>Parts out:</td><td>%s</td><td>%s</td><tr>" % (model.outParts,"")
    html += "<tr><td>Hours per shift:</td><td>%.2f</td><td>%s</td><tr>" % (model.hoursPerShift,"")
    html += "<tr><td>Hours per day:</td><td>%.2f</td><td>%s</td><tr>" % (model.hoursPerDay,"")
    html += "<tr><td>Days per week:</td><td>%.2f</td><td>%s</td><tr>" % (model.daysPerWeek,"")
    html += "<tr><td>Unit of time:</td><td>%s</td><td>%s</td><tr>" % (unitOfTime[model.unitOfTime],"")
    html += "<tr><td>Currency:</td><td>%s</td><td>%s</td><tr>" % (model.currency,"")
    html += "<tr><td>CoV of arrival:</td><td>%.2f</td><td>%s</td><tr>" % (model.CVSource,"")
    html += "<tr><td>Floor Space:</td><td>%.2f</td><td>[%s/(sqm*year)]</td><tr>" % (model.FloorSpace,model.currency)
    html += "<tr><td>Special Area:</td><td>%.2f</td><td>[%s/(sqm*year)]</td><tr>" % (model.SpecialArea,model.currency)
    html += "<tr><td>Head Count:</td><td>%.2f</td><td>[%s/hour]</td><tr>" % (model.HeadCount,model.currency)
    html += "<tr><td>Overhead:</td><td>%.2f</td><td>%s</td><tr>" % (model.Overhead,"")
    html += "<tr><td>Operator Availability:</td><td>%.2f</td><td>%s</td><tr>" % (model.OperatorAV*100,"%")
    html += "</table>"
    return html

def RenderWorkcenterData(model,bn):
    html = "<h1>Workcenter</h1>"
    notUsedList = []
    table = model.makeWorkcenterTable()
    for w in model.workcenter:
        if not w.Used:
            notUsedList.append(w.name)
    df = pd.DataFrame(table)
    html += df.style.set_table_styles(styles).apply(highlight_bottleneck, axis=0, args=(bn,)).apply(highlight_notUsed, axis=1, args=(notUsedList,)).render()
    return html

def RenderProdTypeData(model):
    html = "<h1>Product Types</h1>"
    table = model.makeProductTypeTable()
    df = pd.DataFrame(table)
    df = df.astype({"Percentage":'float64'})
    html += df.style.format({'Percentage': '{:.2f} %'}).set_table_styles(styles).render()
    return html

def RenderOperationData(prodtype):
    html = "<h1>Product Type '%s' Operations</h1><table>" % prodtype.name
    table = prodtype.makeOperationTable()
    df = pd.DataFrame(table)
    html += df.style.set_table_styles(styles).render()
    return html

def RenderPflowData(prodtype):
    html = "<h1>Product Types '%s' Process Flow</h1><table>" % prodtype.name
    html += "<tr><th>Predecessor</th><th>Successor</th><th>Probability</th>"
    html += "<th>Operation Time [%s]</th><th>Transition Cost</th><th>Transition Time [%s]</th></tr>" % \
                                    (unitOfTime[prodtype.model.unitOfTime],unitOfTime[prodtype.model.unitOfTime])
    op = -1
    for t in prodtype.transitions:
        rowspan = ""
        try:
            to = prodtype.operations[t.to-1].name
        except IndexError:
            to = "Sink"
        if t.noSucc > 1:
            rowspan = "rowspan=\"%d\"" % t.noSucc
        if t.op != op:
            html += "<tr><td %s>%s</td><td>%s</td><td>%.2f</td>" % (rowspan,prodtype.operations[t.op-1].name,to,t.Prob)
        else:
            html += "<tr><td>%s</td><td>%.2f</td>" % (to,t.Prob)
        html += "<td>%.2f</td><td>%.2f</td><td>%.2f</td></tr>" % (t.OperatorTime,t.TransitionCost,t.TransitionTime)
        op = t.op
    html += "</table>"
    return html

def DrawPflowData(prodtype,withWC):
    graph = """
        graph LR;
    """
    wc = {}
    for i, w in enumerate(prodtype.model.workcenter):
        wc[w.name] = []
    for i, o in enumerate(prodtype.operations):
        wc[prodtype.model.workcenter[o.WCNumber-1].name].append(o.name)
        tr = prodtype.getSucc(i+1)
        for t in tr:
            g = f"{o.name}--> "
            if t.Prob == 1.0:
                g += f"{t.getOPName(t.to)}"
            else:
                g += f"|{t.Prob}| {t.getOPName(t.to)}"
            graph += g + ";\n"
    if withWC == "True":
        for w in wc:
            if wc[w]:
                graph += f"subgraph {w}\n{' & '.join(wc[w])}\nend\n"
    graphbytes = graph.encode("ascii")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    fn = f"{prodtype.name} Flow.jpg"
    with Image.open(io.BytesIO(requests.get('https://mermaid.ink/img/' + base64_string).content)) as im:
        im.save(fn, "JPEG")
    html = '<img src="{}">'.format(fn)
    return html


def RenderCapTable(window,model,WIP,OAR,fontsize):
    htmlFile = "CapacityTable.html"
    html = "<h1>Capacity Calculation %s</h1>" % model.name
    table = {"Product Type": [], "Weekly Production Demand": [], "Weekly Input": []}
    for t in model.prodtypes:
        table["Product Type"].append(t.name)
        table["Weekly Production Demand"].append(t.WeekOut)
        table["Weekly Input"].append("%.2f" % t.WeekIn)
    df = pd.DataFrame(table)
    html += styleTable(df,fontsize)
    html += "<p>Days / Week: %.2f</p>" % model.daysPerWeek
    html += "<p>Hours / Day: %.2f</p>" % model.hoursPerDay
    table = {"Product Type": [], "Daily Production Demand": [], "Daily Input": []}
    for t in model.prodtypes:
        table["Product Type"].append(t.name)
        table["Daily Production Demand"].append("%.2f" % t.DayOut)
        table["Daily Input"].append("%.2f" % t.DayIn)
    df = pd.DataFrame(table)
    html += styleTable(df,fontsize)
    html += "<p>Overall arrival rate: %.2f</p>" % OAR
    html += "<p>WIP: %.2f</p>" % WIP
    table = {"Workcenter": [], "New Capacity": [], "Computed Capacity": [], "Difference to current model": []}
    for w in model.workcenter:
        table["Workcenter"].append(w.name)
        table["New Capacity"].append(w.NewWSNum)
        table["Computed Capacity"].append(w.NWSNum)
        table["Difference to current model"].append(w.Differ)
    df = pd.DataFrame(table)
    html += styleTable(df,fontsize)
    f = open(htmlFile,"w")
    f.write("<html>"+html+"</html>")
    f.close()
    window.panel_2.wv.LoadURL("file://"+os.getcwd()+SLASH+htmlFile)


def RenderWorkLoadTable(window,model,idxType,DailyOut,outputItems,cfg,chart,col,what="All",dx=640,dy=480,dpi=96):
    cols = set()
    fontsize = cfg["gui"]["font-size"]
    htmlFile = "WorkLoadTable.html"
    html = (CSSStyle % fontsize)
    html += "<h1>Workload Table for Product Type %s %s</h1>" % (model.prodtypes[idxType].name,model.name)
    table = {"Workcenter": [], "Operation": [], "Relative Load SOB": [], "Relative Load Mfg": [],
            "Overall Load Per Hour": [], "Overall Load Per Shift": [], "Overall Load Per Day": []}
    for w in model.workcenter:
        table["Workcenter"].append(w.name)
        table["Operation"].append("")
        table["Relative Load SOB"].append(w.SFTable.SOB)
        table["Relative Load Mfg"].append(w.SFTable.MFG)
        table["Overall Load Per Hour"].append(w.SFTable.Hour)
        table["Overall Load Per Shift"].append(w.SFTable.Shift)
        table["Overall Load Per Day"].append(w.SFTable.Day)
        for o in model.findOperations(w,prodtype=model.prodtypes[idxType]):
            table["Workcenter"].append("")
            table["Operation"].append(o.name)
            table["Relative Load SOB"].append(o.SFTable.SOB)
            table["Relative Load Mfg"].append(o.SFTable.MFG)
            table["Overall Load Per Hour"].append(o.SFTable.Hour)
            table["Overall Load Per Shift"].append(o.SFTable.Shift)
            table["Overall Load Per Day"].append(o.SFTable.Day)
    df = pd.DataFrame(table)
    if what == "All":
        for w in outputItems:
            html, columns = addOutputItem(w,html,cfg,df,-1,col,model,idxType,cols=cols,dx=dx,dy=dy,dpi=dpi)
            for c in columns:
                cols.add(c)
    elif what in outputItems:
        html, columns = addOutputItem(what,html,cfg,df,-1,col,model,idxType,chart=chart,dx=dx,dy=dy,dpi=dpi)
        cols = columns
    f = open(htmlFile,"w")
    f.write("<html>"+html+"</html>")
    f.close()
    window.panel_2.wv.LoadURL("file://"+os.getcwd()+SLASH+htmlFile)
    return cols


def addOutputItem(w,html,cfg,df,bn,col,model,typeSelected,chart="",cols=set(),dx=640,dy=480,dpi=96):
    leave = None
    s = getOutputItemByName(cfg,w)
    columns = getColumns(cfg,s)
    columns = [getLabel(c,model) for c in columns]
    suffix = ""
    if typeSelected > 0:
        suffix = " for product type %s" % model.prodtypes[typeSelected-1].name
    title = "%s %s" % (cfg.get(s,"name"),suffix)
    html += "<h1>%s %s</h1>" % (title,model.name)
    if not chart:
        try:
            html += df[["Workcenter",] + columns].style.set_table_styles(styles).apply(highlight_bottleneck, axis=0, args=(bn,)).render()
        except (KeyError,) as e:
            html += "<div class='error'>%s</div>" % e
    charts = getCharts(cfg,s)
    for ch in charts:
        if not chart or chart == ch["chart"]:
            x = "Workcenter"
            if ch.get("x"):
                x = "Operation"
            fig, ax = plt.subplots(figsize=(24,8),dpi=dpi)
            if col and getLabel(col,model) in columns:
                colList = [getLabel(col,model),]
            else:
                colList = [getLabel(c.strip(),model) for c in ch["cols"].split(",")]
            df[df[x] != ""].plot.bar(x=x, y=colList, rot=45, ax=ax, title=title+" chart")
            # fig.set_size_inches(dx/dpi,dy/dpi)
            encoded = fig_to_base64(fig)
            html += '<img src="data:image/png;base64, {}">'.format(encoded.decode('utf-8'))
            plt.close("all")
    for c in columns:
        cols.add(c)
    return html, cols

def prepTable(model,typeSelected,CostIndices,Resources):
    table = {"Workcenter": [] }
    dict = getDataDictItems("Workcenter Results",model)
    for d in dict:
        table[dict[d]["Label"]] = []
    dict_c = getDataDictItems("Workcenter Results Cost",model)
    for d in dict_c:
        table[dict_c[d]["Label"]] = []
    dict_r = getDataDictItems("Workcenter Results Resources",model)
    for d in dict_r:
        table[dict_r[d]["Label"]] = []
    for i, w in enumerate(model.workcenter):
        if typeSelected == 0:
            ResWCTable = w.ResTable
        else:
            ResWCTable = model.prodtypes[typeSelected-1].ResWCTable[i]
        table["Workcenter"].append(w.name)
        for d in dict:
            m = 1
            if dict[d].get("Multiply"):
                m = dict[d].get("Multiply")
            try:
                try:
                    table[dict[d]["Label"]].append(getattr(ResWCTable,d)*m)
                except AttributeError:
                    table[dict[d]["Label"]].append(getattr(w.SFTable,d)*m)
            except AttributeError:
                table[dict[d]["Label"]].append(0.0)
        for d in dict_c:
            table[dict_c[d]["Label"]].append(model.CostMatrixArray[typeSelected-1][i][CostIndices[d]])
        for d in dict_r:
            table[dict_r[d]["Label"]].append(model.ResArray[typeSelected-1][i][d])
    df = pd.DataFrame(table)
    return df

def RenderTabOverall(window,model,oar,bn,typeSelected,CostIndices,Resources,outputItems,cfg,what="All",chart="",col="",dx=640,dy=480,dpi=96):
    fontsize = cfg["gui"]["font-size"]
    htmlFile = "LineOverall.html"
    columns = []
    cols = set()
    model.OAR = oar
    html = (CSSStyle % fontsize)
    if typeSelected == 0:
        ResTable = model.ResTable
    else:
        ResTable = model.prodtypes[typeSelected-1].ResTable
    if what in ("All", "Line"):
        if typeSelected == 0:
            html += "<h1>Line Characteristics Overall %s</h1><table>" % model.name
            ResTable = model.ResTable
        else:
            html += "<h1>Line Characteristics for Product Type %s %s</h1><table>" % (model.prodtypes[typeSelected-1].name,model.name)
            ResTable = model.prodtypes[typeSelected-1].ResTable
        html += "<tr><td>Parts started:</td><td>%.8f</td><td>[Parts/%s]</td><td> Maximum is:</td><td>%.8f</td><td>[Parts/%s]</td></tr>" % \
            (ResTable.OAR,unitOfTime[model.unitOfTime],ResTable.MaxOAR,unitOfTime[model.unitOfTime])
        html += "<tr><td>Good parts out:</td><td>%.8f</td><td>[Parts/%s]</td><td> Maximum is:</td><td>%.8f</td><td>[Parts/%s]</td></tr>" % \
            (ResTable.GoodPartsOut,unitOfTime[model.unitOfTime],ResTable.MaxODR,unitOfTime[model.unitOfTime])
        html += "<tr><td>Yield:</td><td>%.2f</td><td>%%</td></tr>" % (ResTable.Yield*100)
        html += "<tr><td>Days/Week:</td><td>%d</td><td></td></tr>" % model.daysPerWeek
        html += "<tr><td>Hours/Day:</td><td>%d</td><td></td></tr>" % model.hoursPerDay
        html += "<tr><td>Daily going rate (start of build):</td><td>%.2f</td><td>[%s/day]</td><td> Maximum is:</td><td>%.2f</td><td>[%s/day]</td></tr>" % \
            (ResTable.DGRStart,model.inParts,ResTable.StartMax,model.inParts)
        html += "<tr><td>Daily going rate (shipment):</td><td>%.2f</td><td>[%s/day]</td><td> Maximum is:</td><td>%.2f</td><td>[%s/day]</td></tr>" % \
            (ResTable.DGRShip,model.outParts,ResTable.ThroughputMax,model.outParts)
        html += "<tr><td>Takt time:</td><td>%.2f</td><td>[%s]</td></tr>" % (ResTable.TactTime,unitOfTime[model.unitOfTime])
        html += "<tr><td>Utilization (average):</td><td>%.2f</td><td>%%</td></tr>" % (ResTable.UtilAverage*100,)
        html += "<tr><td>Raw cycle time (all parts):</td><td>%.2f</td><td>[%s]</td></tr>" % (ResTable.RawCycleTime,unitOfTime[model.unitOfTime])
        html += "<tr><td>Leadtime (all parts):</td><td>%.2f</td><td>[%s]</td>" % (ResTable.LeadTimeNet,unitOfTime[model.unitOfTime])
        if ResTable.LeadTimeTot == -1:
            txt = "-"
        else:
            txt = "%.2f" % ResTable.LeadTimeTot
        html += "<td> including idle periods:</td><td>%s</td><td>[%s]</td></tr>" % (txt,unitOfTime[model.unitOfTime])
        if ResTable.EfficiencyNet == -1:
            txt = "-"
        else:
            txt = "%.2f" % (ResTable.EfficiencyNet*100)
        html += "<tr><td>Line efficiency:</td><td>%s</td><td>%%</td>" % (txt,)
        if ResTable.EfficiencyTot == -1:
            txt = "-"
        else:
            txt = "%.2f" % (ResTable.EfficiencyTot*100)
        html += "<td> including idle periods:</td><td>%s</td><td>%%</td></tr>" % (txt,)
        if ResTable.WIP == -1:
            txt = "-"
        else:
            txt = "%.2f" % ResTable.WIP
        html += "<tr><td>WIP:</td><td>%s</td><td>%s</td></tr>" % (txt,model.outParts)
        # Cost results
        html += "<tr><td>Manufacturing cost:</td><td>%.2f</td><td>[%s/part]</td><td></td><td>%.2f</td><td>[%s/%s]</td><td></td><td>%.2f</td><td>[%s/Day]</td></tr>" % \
                (model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostManFacPerPart"]],model.currency, \
                    model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostManFacPerTU"]],model.currency,unitOfTime[model.unitOfTime], \
                    model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostManFacPerDay"]],model.currency)
        html += "<tr><td>Income:</td><td></td><td></td><td></td><td></td><td></td><td></td><td>%.2f</td><td>[%s/day]</td></tr>" % \
                (model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostIncome"]],model.currency)
        html += "<tr><td>Profit:</td><td>%.4f</td><td>[%s/part]</td><td></td><td>%.4f</td><td>[%s/%s]</td><td></td><td>%.4f</td><td>[%s/Day]</td></tr>" % \
                (model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostProfitPerPart"]],model.currency, \
                model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostProfitPerTU"]],model.currency,unitOfTime[model.unitOfTime], \
                model.CostMatrixArray[typeSelected-1][-1][CostIndices["CostProfitPerDay"]],model.currency)
        html += "</table>"
    if what == "All" or what in outputItems:
        df = prepTable(model,typeSelected,CostIndices,Resources)
    if what == "All":
        for w in outputItems:
            html, columns = addOutputItem(w,html,cfg,df,bn,col,model,typeSelected,cols=cols,dx=dx,dy=dy,dpi=dpi)
            for c in columns:
                cols.add(c)
    elif what in outputItems:
        html, columns = addOutputItem(what,html,cfg,df,bn,col,model,typeSelected,chart=chart,dx=dx,dy=dy,dpi=dpi)
        cols = columns
    f = open(htmlFile,"w")
    f.write("<html>"+html+"</html>")
    f.close()
    window.panel_2.wv.LoadURL("file://"+os.getcwd()+SLASH+htmlFile)
    return cols

def RenderGraphics(window,model,col="Utilization",col2=None,x="XVal",workcenterSelected=[],dx=640,dy=480,dpi=96):
    if not col:
        col="Utilization"
    htmlFile = "LinePlot.html"
    data = { "x":   getattr(model.ResGraph[-1],x), "x_":   getattr(model.ResGraph[-1],"XVal")}
    columns = []
    suffix = ""
    for i in workcenterSelected:
        if i == 0:
            c = "Line"
        else:
            c = model.workcenter[i-1].name
        if len(workcenterSelected) == 1:
            suffix = " (%s)" % c
            c = col
        columns.append(c)
        data[c] = getattr(model.ResGraph[i-1],col)
    dict = getDataDictItems("Plot",model)
    unit = ""
    unit2 = ""
    label = getLabel(col,model)
    try:
        d = dict[columns[0]]
        unit = d["Unit"]
        label = d["Label"]
    except KeyError: pass
    if col2:
        try:
            d = dict[col2]
            unit2 = d["Unit"]
            label += ", " + d["Label"]
        except KeyError: pass
    html = "<h1>Line Characteristics Plot - %s - %s" % (label,model.name)
    if col2 and len(workcenterSelected) == 1:
        data[col2] = getattr(model.ResGraph[-1],col2)
    html += "%s</h1>" % suffix
    df = pd.DataFrame(data)
    # Filter out entries with x >= maxOAR
    df = df.loc[lambda df: df['x_'] < model.MaxOAR, :]
    fig, ax = plt.subplots(figsize=(15,6),dpi=dpi)
    label = ("")
    if len(columns) == 1:
        label = [getLabel(columns[0],model),]
    df.plot('x', columns, kind="line", ax=ax, grid=True, label=label)
    if col2 and len(workcenterSelected) == 1:
        label = ""
        label = getLabel(col2,model)
        df.plot('x',col2,ax=ax, grid=True, secondary_y=True, color='r', label=label)
    if x == "DR":
        ax.set_xlabel("Departure Rate")
    elif x == "SOB":
        ax.set_xlabel("Daily Starts (SOB)")
    elif x == "SHIP":
        ax.set_xlabel("Daily Shipments (SHIP)")
    else:
        ax.set_xlabel("Arrival Rate")
    if unit:
        ax.set_ylabel(unit)
    if unit2:
        ax.right_ax.set_ylabel(unit2)
    fig.set_size_inches(dx/dpi,dy/dpi)
    encoded = fig_to_base64(fig)
    html += '<img src="data:image/png;base64, {}">'.format(encoded.decode('utf-8'))
    f = open(htmlFile,"w")
    f.write("<html>"+html+"</html>")
    f.close()
    window.panel_2.wv.LoadURL("file://"+os.getcwd()+SLASH+htmlFile)