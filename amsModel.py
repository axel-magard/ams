import sys
import copy
import re

from amsView import RenderModelData, RenderWorkcenterData, RenderProdTypeData, RenderOperationData, RenderPflowData, unitOfTime
from amsData import dataDict, getDataDictItem, getDataDictItems, getLabel

CSSStyle = """
<style>
	th, td {
	  text-align: right;
	  border-bottom: 1px solid #ddd;
      font-size: %spx;
	}
</style>
"""

class Model:
    def __init__(self, name, inParts, outParts):
        self.version = "0"
        self.name = name
        self.dirname = ""
        self.changed = False
        self.workcenter = []
        self.prodtypes = []
        self.inParts = inParts
        self.outParts = outParts
        self.hoursPerShift = 8.0
        self.hoursPerDay = 24.0
        self.daysPerWeek =  5.0
        self.unitOfTime = 0
        self.currency = "€"
        self.CVSource = 0.0
        self.FloorSpace = 0.0
        self.SpecialArea = 0.0
        self.HeadCount = 0.0
        self.Overhead = 0.0
        self.OperatorAV = 1.0
        self.OAR = 0.0
        self.MaxOAR = 999999
        self.prodTypeSelected = 0
        self.Bottleneck = -1
        self.m_Summ1 = None
        self.m_Summ2 = None
        self.m_Summ3 = None
        self.m_HSumm = None
        self.m_VCompl = None
        self.m_MeanCycleTimes = None
        self.m_SplitJoinWC = None
        self.YieldTot = 0.0
        self.YieldTot2 = 0.0
        self.bComputed = False
        self.ResTable = None
        self.ResGraph = []
        self.ResArray = []      # Matrix of computed resources by prod type and work center
        self.CostMatrixArray = None
    def change(self,changed=True,treeCtrl=None,treeItem=None):
        if treeCtrl:
            if changed:
                if not treeCtrl.GetItemText(treeItem).endswith("*"):
                    treeCtrl.SetItemText(treeItem,treeCtrl.GetItemText(treeItem)+" *")
            else:
                treeCtrl.SetItemText(treeItem,treeCtrl.GetItemText(treeItem).replace(" *",""))
        self.changed = changed
    def render(self,fontsize,what="All",prodType=None):
        self.htmlFile = "%s.html" % self.name
        html = "<html><head>%s<title>%s</title></head><body><h1>%s</h1>" % ((CSSStyle % fontsize),self.name,self.name)
        if what in ("All","Model"):
            html += RenderModelData(self)
        if what in ("All","Workcenter"):
            html += RenderWorkcenterData(self,self.Bottleneck)
        if what in ("All","Product Types","Product Mix") and not prodType:
            html += RenderProdTypeData(self)
        for p in self.prodtypes:
            if not prodType or p == prodType:
                if what in ("All","Product Types","Operations"):
                    html += RenderOperationData(p)
                if what in ("All","Product Types","Process Flow"):
                    html += RenderPflowData(p)
        html += "</body></html>"
        f = open(self.htmlFile,"w")
        f.write(html)
        f.close()
        return self.htmlFile
    def checkProperties(self, what, value):
        msg = ""
        if isinstance(value, str):
            return msg
        if value < 0.0:
            return f"Model {what} can not be negative !"
        return msg
    def updateWorkcenter(self,workcenter):
        for i in range(len(self.workcenter)):
            w = self.workcenter[i]
            if w.id == workcenter.id:
                self.workcenter[i] = workcenter
                self.bComputed = False
                return
    def updateOperation(self,operation):
        for i in range(len(self.prodtypes)):
            if self.prodtypes[i] == operation.ProdType:
                for j in range(len(self.prodtypes[i].operations)):
                    o = self.prodtypes[i].operations[j]
                    if o.id == operation.id:
                        self.prodtypes[i].operations[j] = operation
                        self.bComputed = False
                        self.findUsedWorkcenter()
                        return

    def findUsedWorkcenter(self):
        for i, w in enumerate(self.workcenter):
            w.Used = False
        for i, t in enumerate(self.prodtypes):
            for j, o in enumerate(t.operations):
                try:
                    self.workcenter[o.WCNumber-1].Used = True
                except IndexError: pass

        return
    def findWorkcenter(self, name):
        for i, w in enumerate(self.workcenter):
            if w.name == name:
                return w
        return None
    def findProdType(self, name):
        for i, p in enumerate(self.prodtypes):
            if p.name == name:
                return p
        return None
    def updateProdType(self,prodtype):
        for i in range(len(self.prodtypes)):
            t = self.prodtypes[i]
            if t.id == prodtype.id:
                self.prodtypes[i] = prodtype
                self.bComputed = False
                return
        return
    def addProdType(self,t=None,pt=None):
        if not t:
            try:
                t = self.prodtypes[-1]
            except IndexError: pass
        if not pt:
            pt = ProdType("New Product Type","Parts started","Parts finished", "New Product Type", self)
        if t:
            idx = self.prodtypes.index(t)+1
            self.prodtypes.insert(idx,pt)
        else:
            self.prodtypes.append(pt)
        if not pt.operations:
            pt.operations.append(Operation("New Operation",self))
            pt.operations[-1].ProdType = pt
            pt.startOp = 1
            pt.transitions.append(Transition(1,2,1.0,0.0,0.0,0.0,self,pt))
        self.bComputed = False
        return pt
    def getWCList(self):
        return [w.name for w in self.workcenter]
    def addWorkcenter(self,w=None,wc=None):
        if not w:
            try:
                w = self.workcenter[-1]
            except IndexError: pass
        if not wc:
            wc = Workcenter("New Workcenter")
        wc.name = genUniqueName(self.workcenter,wc.name)
        idx = 0
        if w:
            idx = self.workcenter.index(w)+1
            self.workcenter.insert(idx,wc)
        else:
            self.workcenter.append(wc)
        self.bComputed = False
        self.changed = True
        # Now update operation assignments ...
        for i, t in enumerate(self.prodtypes):
            for j, o in enumerate(t.operations):
                if o.WCNumber > idx:
                    o.WCNumber += 1
        return wc
    def deleteWorkcenter(self,w):
        idx = self.workcenter.index(w)+1
        self.workcenter.remove(w)
        self.bComputed = False
        # Now update operation assignments ...
        for i, t in enumerate(self.prodtypes):
            for j, o in enumerate(t.operations):
                if o.WCNumber > idx:
                    o.WCNumber -= 1
    def deleteProdType(self,t):
        self.prodtypes.remove(t)
        if len(self.prodtypes) == 1:
            self.prodtypes[0].percentage = 1.0
        self.bComputed = False
    def findOperations(self, workcenter, prodtype=None):
        operations = []
        for i, t in enumerate(self.prodtypes):
            for j, o in enumerate(t.operations):
                if o.WCNumber == self.workcenter.index(workcenter)+1:
                    if not prodtype or o.ProdType == prodtype:
                        operations.append(o)
        return operations
    def makeWorkcenterTable(self):
        table = {"Name": [] }
        dict = getDataDictItems("Workcenter",self)
        for d in dict:
            table[dict[d]["Label"]] = []
        for w in self.workcenter:
            table["Name"].append(w.name)
            for d in dict:
                table[dict[d]["Label"]].append(getattr(w,d))
        return table
    def makeProductTypeTable(self):
        table = {"Name": [] }
        dict = getDataDictItems("ProductType",self,"Basic")
        for d in dict:
            table[dict[d]["Label"]] = []
        for p in self.prodtypes:
            table["Name"].append(p.name)
            for d in dict:
                if d == "startOp":
                    table[dict[d]["Label"]].append(p.operations[p.startOp-1].name)
                elif d == "percentage":
                    table[dict[d]["Label"]].append(getattr(p,d)*100.0)
                else:
                    table[dict[d]["Label"]].append(getattr(p,d))
        return table
    def checkWorkcenterTable(self, table):
        row = 0
        for name in table["Name"]:
            w = Workcenter(name)
            msg = ""
            i = table["Name"].index(name)
            dataDict = getDataDictItems("Workcenter",self,unitOfTime)
            for d in dataDict:
                setattr(w,d,table[dataDict[d].get("Label")][i])
            for d in dataDict:
                msg = w.checkProperties(d, table[dataDict[d].get("Label")][i])
                if msg:
                    return f"Workcenter {w.name}: " + msg
        return ""
    def loadWorkcenterTable(self, table):
        newWC = []
        row = 0
        found = []
        for name in table["Name"]:
            w = self.findWorkcenter(name)
            if not w:
                w = self.addWorkcenter(None,Workcenter(name))
                newWC.append(w)
            else:
                found.append(w)
            i = table["Name"].index(name)
            w.NumWS = table["# Work Stations"][i]
            w.Batchsize = table["Batchsize"][i]
            w.COV = table["CoV"][i]
            w.Rel = table["Reliability"][i]
            w.MDT = table["Mean Down Time [%s]" % unitOfTime[self.unitOfTime]][i]
            w.COVofMDT = table["CoV of Mean Down Time"][i]
            w.Cost_Depr = table[getLabel("Cost_Depr",self)][i]
            w.Cost_SM = table[getLabel("Cost_SM",self)][i]
            w.Cost_Op = table[getLabel("Cost_Op",self)][i]
            w.Res_Floor = table[getLabel("Res_Floor",self)][i]
            w.Res_Area = table[getLabel("Res_Area",self)][i]
            w.BufferIsFloorSpace = table["Buffer Is Floor Space"][i]
            w.Maint_S = table[getLabel("Maint_S",self)][i]
            w.Maint_U = table[getLabel("Maint_U",self)][i]
            row += 1
        # Delete workcenter not found ...
        for i, w in enumerate(self.workcenter):
            if w not in found:
                self.deleteWorkcenter(w)
        return newWC
    def loadProductTypeTable(self, table):
        newPT = []
        for name in table["Name"]:
            p = self.findProdType(name)
            if not p:
                p = self.addProdType(None,ProdType(name,"Parts started","Parts finished", "New Product Type",self))
                newPT.append(p)
            i = table["Name"].index(name)
            p.percentage = float(table["Percentage"][i])/100.0
            p.inParts = table["In Parts"][i]
            p.outParts = table["Out Parts"][i]
            p.description = table["Description"][i]
            try:
                p.startOp = p.operations.index(p.findOperation(table["Start Operation"][i]))+1
            except ValueError:
                p.startOp = 0
            p.Cost_Inventory = table[getLabel("Cost_Inventory",self)][i]
            p.Res_Space = table[getLabel("Res_Space",self)][i]
            p.Income = table[getLabel("Income",self)][i]
        return newPT
    def getWorkcenterListAsString(self):
        str = ""
        for w in self.workcenter:
            str += w.name+","
        return str[:-1]
    def getWorkcenterNameList(self):
        l = []
        for w in self.workcenter:
            l.append(w.name)
        return l
    def clone(self):
        return(copy.deepcopy(self))
    def changeUnitOfTime(self,old,new):
        timeConversion=((1,1/60.0,1/3600.0),(60,1,1/60.0),(3600.0,60.0,1))
        for i, w in enumerate(self.workcenter):
            w.MDT *= timeConversion[old][new]
        for i, t in enumerate(self.prodtypes):
            for j, o in enumerate(t.operations):
                o.CT *= timeConversion[old][new]
                o.Time_Handling *= timeConversion[old][new]
                o.Time_Inspection *= timeConversion[old][new]
            for j, tr in enumerate(t.transitions):
                tr.OperatorTime *= timeConversion[old][new]
                tr.TransitionTime *= timeConversion[old][new]
        self.change()


class Workcenter:
    cnt = -1
    def __init__(self, name):
        Workcenter.cnt += 1
        self.id = Workcenter.cnt
        self.name = name
        self.Used = False
        self.NumWS = 1          # Capacity
        self.Batchsize = 1
        self.COV = 0.0          # Coefficient Of Variation of Operation Service Times
        self.Rel = 1.0          # Reliability
        self.MDT = 0            # Mean Down Time
        self.COVofMDT = 0.0     # Coefficient Of Variation of Mean Down Time
        self.Cost_Depr = 0.0    # Depreciation Cost
        self.Cost_SM = 0.0      # Service & Maintenance Cost
        self.Cost_Op = 0.0      # Opertional Cost
        self.Res_Floor = 0.0    # Floor Space
        self.Res_Area = 0.0     # Special Area
        self.BufferIsFloorSpace = 0
        self.Maint_S = 0.0      # Scheduled Maintenance
        self.Maint_U = 0.0      # Un-scheduled Maintenance
        self.SFTable = None
        self.ResTable = None
        self.NWSNum = 0         # for Capacity calculation
        self.NewWSNum = 0       # for Capacity calculation
        self.Differ = 0         # for Capacity calculation
    def __repr__(self):
        return(f"Workcenter '{self.name}'")
    def checkProperties(self, what, value):
        msg = ""
        if value < 0.0:
            return f"Workcenter {what} can not be negative !"
        if what == "Rel":
            if value > 1.0:
                msg = "Workcenter Reliability can not exceed 1.0 !"
            elif value < 1.0 and self.MDT == 0.0:
                msg = "Mean Down Time must be specified when Workcenter Reliability is not 100 % !"
        return msg


class ProdType:
    cnt = -1
    def __init__(self, name, inParts, outParts, description, model):
        ProdType.cnt += 1
        self.id = ProdType.cnt
        self.name = name
        self.operations = []
        self.transitions = []
        self.inParts = inParts
        self.outParts = outParts
        self.startOp = 0
        self.description = description
        self.percentage = 0.0
        self.Cost_Inventory = 0.0
        self.Res_Space = 0.0
        self.Income = 0.0
        self.model = model
        self.SFactorTab = None
        self.SFactorTabNew = None
        self.WCSFactorTab = None
        self.WCSFactorTab2 = None
        self.OAR = 0.0                  # for Capacity calculation
        self.new_percentage = 0.0       # for Capacity calculation
        self.WeekOut = 0                # for Capacity calculation
        self.DayOut = 0                 # for Capacity calculation
        self.WeekIn = 0                 # for Capacity calculation
        self.DayIn = 0                  # for Capacity calculation
        self.ResWCTable = []
        self.ResTable = None
    def __repr__(self):
        return(f"Product Type '{self.name}'")
    def checkProperties(self, what, value):
        msg = ""
        try:
            if value < 0.0:
                return f"Product Type {what} can not be negative !"
        except TypeError:
            return f"Product Type {what} must be numeric !"
        if what == "percentage":
            if value > 100.0:
                msg = "Product Type Percentage must be <= 100 % !"
        return msg

    def getOp(self,opNum):
        if opNum < 1:
            return None
        try:
            return self.operations[opNum-1]
        except IndexError:
            sink = Operation("Sink",self.model)
            return sink
    def getOpIdx(self,opName):
        for i in range(len(self.operations)):
            if self.operations[i].name == opName:
                return i
        return len(self.operations)
    def addOperation(self,o=None,op=None):
        if not o:
            o = self.operations[-1]
        if not op:
            op = Operation("New Operation",o.model)
        op.ProdType = self
        op.id = self.operations[-1].id + 1
        idx = self.operations.index(o)+1
        self.operations.insert(idx,op)
        self.fixTransitions(idx)
        # Add transitions to successors of original operation
        for tr in o.ProdType.getSucc(o.ProdType.operations.index(o)+1):
            o.ProdType.addSucc(self.model,o.ProdType.operations.index(op)+1,tr.to,tr.Prob,tr.OperatorTime,tr.TransitionCost,tr.TransitionTime)
        # Split transitions to original and new operation fifty-fifty
        for pr in o.ProdType.getPred(o.ProdType.operations.index(o)+1):
            for tr in o.ProdType.findTransitions(from_op=pr):
                tr.Prob = tr.Prob / 2.0
                o.ProdType.transitions.append(Transition(tr.op,o.ProdType.operations.index(op)+1,tr.Prob,tr.OperatorTime,tr.TransitionCost,tr.TransitionTime,self.model,o.ProdType))
        self.model.bComputed = False
        return op
    def deleteOperation(self,o):
        idx = self.operations.index(o)+1
        self.operations.remove(o)
        self.deleteTransitions(idx)
        self.fixTransitions(idx,"del")
        self.model.bComputed = False
    def findOperation(self, name):
        for i, o in enumerate(self.operations):
            if o.name == name:
                return o
        return None
    def fixTransitions(self, idx, op="add"):
        for t in self.transitions:
            if op == "add":
                if t.op > idx:
                    t.op += 1
                if t.to > idx:
                    t.to += 1
            else:
                if t.op > idx:
                    t.op -= 1
                if t.to > idx:
                    t.to -= 1
        countSuccessors(self.model)
    def deleteTransitions(self, idx):
        for t in self.transitions:
            if t.op == idx:
                self.transitions.remove(t)
    def getSucc(self,op):
        succ = []
        for t in self.transitions:
            if t.op == op:
                succ.append(t)
        return succ
    def addSucc(self,model,from_op,to_op,prob=1.0,otime=0.0,tcost=0.0,ttime=0.0):
        idx = -1
        t = Transition(from_op,to_op,prob,otime,tcost,ttime,model,self)
        for i in range(len(self.transitions)):
            if self.transitions[i].op == from_op:
                idx = i
            elif idx > -1:
                self.transitions.insert(idx+1,t)
                countSuccessors(model)
                return
        self.transitions.append(t)
        countSuccessors(model)
    def delSucc(self,model,from_op,to_op):
        for i in range(len(self.transitions)):
            if self.transitions[i].op == from_op and self.transitions[i].to == to_op:
                t = self.transitions[i]
                self.transitions.remove(t)
                break
        countSuccessors(model)
    def getPred(self,op):
        pred = []
        for t in self.transitions:
            if t.to == op:
                pred.append(t.op)
        return pred
    def findTransitions(self,from_op=None,to_op=None):
        trans = []
        for t in self.transitions:
            if t.to == to_op or t.op == from_op:
                trans.append(t)
        return trans
    def getAssignedOperations(self,wcIdx):
        wcList = []
        for o in self.operations:
            i = 0
            if o.WCNumber > 0 and o.WCNumber <= len(self.model.workcenter):
                wcList.append(i)
            i += 1
        return wcList
    def makeOperationTable(self):
        table = {"Name": [], "Cycle Time [%s]" % unitOfTime[self.model.unitOfTime]: [], "Split/Join Factor": [], "Workcenter": [],
                "Material Cost": [], "Scrapping Cost": [], "Handling Time [%s]" % unitOfTime[self.model.unitOfTime]: [],
                "Inspections Time [%s]" % unitOfTime[self.model.unitOfTime]: []}
        for o in self.operations:
            table["Name"].append(o.name)
            table["Cycle Time [%s]" % unitOfTime[self.model.unitOfTime]].append(o.CT)
            table["Split/Join Factor"].append(o.SJFactor)
            try:
                table["Workcenter"].append(self.model.workcenter[o.WCNumber-1].name)
            except IndexError:
                table["Workcenter"].append("-")
            table["Material Cost"].append(o.Cost_Mat)
            table["Scrapping Cost"].append(o.Cost_Scrap)
            table["Handling Time [%s]" % unitOfTime[self.model.unitOfTime]].append(o.Time_Handling)
            table["Inspections Time [%s]" % unitOfTime[self.model.unitOfTime]].append(o.Time_Inspection)
        return table
    def loadOperationTable(self, table):
        newOp = []
        found = []
        for name in table["Name"]:
            o = self.findOperation(name)
            if not o:
                o = self.addOperation()
                o.name = name
                newOp.append(o)
            else:
                found.append(o)
            i = table["Name"].index(name)
            o.CT = table["Cycle Time [%s]" % unitOfTime[self.model.unitOfTime]][i]
            o.SJFactor = table["Split/Join Factor"][i]
            if isinstance(table["Workcenter"][i], int):
                o.WCNumber = table["Workcenter"][i]
            else:
                o.WCNumber = self.model.workcenter.index(self.model.findWorkcenter(table["Workcenter"][i]))+1
            o.Cost_Mat = table["Material Cost"][i]
            o.Cost_Scrap = table["Scrapping Cost"][i]
            o.Time_Handling = table["Handling Time [%s]" % unitOfTime[self.model.unitOfTime]][i]
            o.Time_Inspection = table["Inspections Time [%s]" % unitOfTime[self.model.unitOfTime]][i]
        # Delete operations not found ...
        for i, o in enumerate(self.operations):
            if o not in found:
                self.deleteOperation(o)
        return newOp


class Operation:
    cnt = -1
    def __init__(self, name, model):
        Operation.cnt += 1
        self.id = Operation.cnt
        self.name = name
        self.CT = 0.0               # Cycle time
        self.SJFactor = 1.0         # Split/Join Factor
        self.WCNumber = 0           # Assigned work center
        self.Cost_Mat = 0.0         # Material Cost
        self.Cost_Scrap = 0.0       # Scrap Cost
        self.Time_Handling = 0.0    # Handling Time
        self.Time_Inspection = 0.0  # Inspection Time
        self.model = model
        self.reachedFromStart = False
        self.reachToEnd = False
        self.SFTable = None
        self.ProdType = None        # Product Type

    def __repr__(self):
        return(f"Operation '{self.name}' ({self.id}) or product type {self.ProdType.name}")

    def getWCName(self):
        if self.WCNumber == 0 or self.WCNumber > len(self.model.workcenter):
            return "-"
        else:
            return self.model.workcenter[self.WCNumber-1].name

    def checkProperties(self, what, value):
        msg = ""
        if value < 0.0:
            return f"Operation {what} can not be negative !"
        if what == "CT":
            if value == 0.0:
                msg = "Operation Cycle Time can not be 0.0 !"
        return msg



class Transition:
    def __init__(self, from_op, to_op, prob, optime, tcost, ttime, model, prodtype):
        self.op = from_op
        self.to = to_op
        self.Prob = prob             # Probability
        self.OperatorTime = optime   # Operator Time
        self.TransitionCost = tcost  # Transition Cost
        self.TransitionTime = ttime  # Transition Time
        self.noSucc = 0
        self.model = model
        self.prodType = prodtype
        self.name = "->"             # Need for compatibility with cloneArtefact()
    def getOPName(self,op):
        try:
            return self.prodType.operations[op-1].name
        except IndexError:
            return "SINK"
    def __repr__(self):
        return f"{self.getOPName(self.op)} -> {self.getOPName(self.to)}"

class SFac:
    def __init__(self):
        self.SOB = 0.0
        self.MFG = 0.0
        self.Hour = 0.0
        self.Shift = 0.0
        self.Day = 0.0

class ResLine:
    def __init__(self):
        self.DaysPerWeek = 0.0
        self.HoursPerDay = 0.0
        self.MaxOAR = 0.0
        self.MaxODR = 0.0
        self.OAR = 0.0
        self.ThroughputMax = 0.0
        self.StartMax = 0.0
        self.GoodPartsOut = 0.0
        self.Yield = 0.0
        self.DGRStart = 0.0
        self.DGRShip = 0.0
        self.TactTime = 0.0
        self.UtilAverage = 0.0
        self.LeadTimeNet = 0.0
        self.RawCycleTime = 0.0
        self.WIP = 0.0
        self.LeadTimeTot = 0.0
        self.EfficiencyNet = 0.0
        self.EfficiencyTot = 0.0

class ResWC:
    def __init__(self):
        self.TotCycleTime = 0.0
        self.OverallLoad = 0.0
        self.UtilNet = 0.0
        self.UtilTot = 0.0
        self.QueueLength = 0.0
        self.RawCycleTime = 0.0
        self.WIP = 0.0
        self.LeadTime = 0.0
        self.Quantil = 0.0
        self.WCUsed = False

class ResultGraph:
    def __init__(self, numValues=25):
        self.m_NumValues = numValues
        self.m_WCNumber = 0                  # 0 means: overall
        self.FactorSOB = 0.0
        self.FactorShip = 0.0
        self.FactorGPO = 0.0
        self.XVal = []
        self.XVal2 = []
        self.DR = []
        self.SOB = []
        self.SHIP = []
        self.Utilization = []
        self.WIP = []
        self.Efficiency = []
        self.Throughput = []
        self.LeadTime = []
        self.QueueLength = []
        self.Quantil = []
        self.OutCosts = []
        self.TimeCosts = []
        self.ManFacCostsPerPart = []
        self.ProfitPerPart = []
        self.FloorSpace = []
        self.SpecialArea = []
        self.NumOperators = []
        self.ManFacCostsPerTU = []
        self.ManFacCostsPerDay = []
        self.ProfitPerTU = []
        self.ProfitPerDay = []
        self.IncomePerDay = []
        for n in range(numValues):
            self.XVal.append(0.0)
            self.XVal2.append(0.0)
            self.DR.append(0.0)
            self.SOB.append(0.0)
            self.SHIP.append(0.0)
            self.Utilization.append(0.0)
            self.WIP.append(0.0)
            self.Efficiency.append(0.0)
            self.Throughput.append(0.0)
            self.LeadTime.append(0.0)
            self.QueueLength.append(0.0)
            self.Quantil.append(0.0)
            self.OutCosts.append(0.0)
            self.TimeCosts.append(0.0)
            self.ManFacCostsPerPart.append(0.0)
            self.ProfitPerPart.append(0.0)
            self.FloorSpace.append(0.0)
            self.SpecialArea.append(0.0)
            self.NumOperators.append(0.0)
            self.ManFacCostsPerTU.append(0.0)
            self.ManFacCostsPerDay.append(0.0)
            self.ProfitPerTU.append(0.0)
            self.ProfitPerDay.append(0.0)
            self.IncomePerDay.append(0.0)
    def reduce(self, n):
        for i in range(n):
            self.XVal.pop(-1)
            self.XVal2.pop(-1)
            self.DR.pop(-1)
            self.SOB.pop(-1)
            self.SHIP.pop(-1)
            self.Utilization.pop(-1)
            self.WIP.pop(-1)
            self.Efficiency.pop(-1)
            self.Throughput.pop(-1)
            self.LeadTime.pop(-1)
            self.QueueLength.pop(-1)
            self.Quantil.pop(-1)
            self.OutCosts.pop(-1)
            self.TimeCosts.pop(-1)
            self.ManFacCostsPerPart.pop(-1)
            self.ProfitPerPart.pop(-1)
            self.FloorSpace.pop(-1)
            self.SpecialArea.pop(-1)
            self.NumOperators.pop(-1)
            self.ManFacCostsPerTU.pop(-1)
            self.ManFacCostsPerDay.pop(-1)
            self.ProfitPerTU.pop(-1)
            self.ProfitPerDay.pop(-1)
            self.IncomePerDay.pop(-1)

def countSuccessors(model):
    for p in model.prodtypes:
        ops = [0,]*len(p.operations)
        for t in p.transitions:
            ops[t.op-1] += 1
        for t in p.transitions:
            t.noSucc = ops[t.op-1]


def importModelLegacy(filename):
    f = open(filename)
    lines = f.readlines()
    f.close()
    sect = ""
    model = None
    for l in lines:
        arr = l.replace("\n","").split("\x1c")
        if sect == "process flow":
            if not arr[0].startswith("TYPE"):
                model.prodtypes[-1].transitions.append(Transition(int(arr[0]),int(arr[1]),float(arr[2]),float(arr[3]),float(arr[4].replace("\x1d","")),0.0,model,model.prodtypes[-1]))
            else:
                sect = "prod type"
        if arr[0].startswith("PROCESS FLOW"):
            sect = "process flow"
        if arr[0].startswith("OPERATION"):
            sect = "operation"
            model.prodtypes[-1].operations.append(Operation(arr[0].split(":")[-1].strip(),model))
        elif sect == "operation":
            model.prodtypes[-1].operations[-1].CT = float(arr[0])
            model.prodtypes[-1].operations[-1].SJFactor = float(arr[1])
            model.prodtypes[-1].operations[-1].WCNumber = int(arr[2])
            model.workcenter[int(arr[2])-1].Used = True
            model.prodtypes[-1].operations[-1].Cost_Mat = float(arr[3])
            model.prodtypes[-1].operations[-1].Cost_Scrap = float(arr[4])
            model.prodtypes[-1].operations[-1].Time_Handling = float(arr[5])
            model.prodtypes[-1].operations[-1].Time_Inspection = float(arr[6])
            model.prodtypes[-1].operations[-1].ProdType = model.prodtypes[-1]
        if arr[0].startswith("TYPE"):
            sect = "prod type"
            model.prodtypes.append(ProdType(arr[0].split(":")[-1],arr[1],arr[2],arr[3],model))
        elif sect == "prod type":
            model.prodtypes[-1].percentage = float(arr[1])
            model.prodtypes[-1].startOp = int(arr[2])
            model.prodtypes[-1].Cost_Inventory = float(arr[3])
            model.prodtypes[-1].Res_Space = float(arr[4])
            model.prodtypes[-1].Income = float(arr[5])
        if sect == "work center":
            if arr[0].startswith("WORK CENTER"):
                model.workcenter.append(Workcenter(arr[0].split(":")[-1]))
            else:
                model.workcenter[-1].NumWS = int(arr[0])
                model.workcenter[-1].Batchsize = int(arr[1])
                model.workcenter[-1].COV = float(arr[2])
                model.workcenter[-1].Rel = float(arr[3])
                model.workcenter[-1].MDT = float(arr[4])
                model.workcenter[-1].COVofMDT = float(arr[5])
                model.workcenter[-1].Cost_Depr = float(arr[6])
                model.workcenter[-1].Cost_SM = float(arr[7])
                model.workcenter[-1].Cost_Op = float(arr[8])
                model.workcenter[-1].Res_Floor = float(arr[9])
                model.workcenter[-1].Res_Area = float(arr[10])
                model.workcenter[-1].Maint_S = float(arr[11])
                model.workcenter[-1].Maint_U = float(arr[12])
        if sect == "model":
            model.hoursPerShift = float(arr[3])
            model.hoursPerDay = float(arr[4])
            model.daysPerWeek =  float(arr[5])
            model.unitOfTime = int(arr[7])
            model.currency = arr[8]
            model.CVSource = float(arr[9])
            model.FloorSpace = float(arr[10])
            model.SpecialArea = float(arr[11])
            model.HeadCount = float(arr[12])
            model.Overhead = float(arr[13])
            model.OperatorAV = float(arr[14])
            sect = "work center"
        if arr[0].startswith("MODEL:"):
            sect = "model"
            model = Model(arr[1],arr[3],arr[4])
    if not model:
        print("Error: no AMS model found.")
        sys.exit(1)
    countSuccessors(model)
    return model

def checkModel(model, errors):
    def look4Sink(prodtype):
        sinkFound = False
        for t in prodtype.transitions:
            if t.to > len(prodtype.operations):
                sinkFound = True
                return sinkFound
        return sinkFound

    def checkWorkcenter(model,errors):
        if len(model.workcenter) == 0:
            errors.append("No workcenter defined.")

    def checkProdtypes(model,errors):
        if len(model.prodtypes) == 0:
            errors.append("No product types defined.")
        sum = 0
        for t in model.prodtypes:
            sum += t.percentage
        if round(sum,4) != 1.0:
            errors.append("Product mix does not sum up to 100 %.")


    def checkOperations(prodtype, errors):
        max_ct = 0
        if len(prodtype.operations) == 0:
            errors.append("No operations defined of product type '%s'." % (prodtype.name,))
        for o in prodtype.operations:
            max_ct = max(max_ct,o.CT)
            if o.WCNumber < 1 or o.WCNumber > len(model.workcenter):
                errors.append("No workcenter assigned for operation '%s' of product type '%s'." % (o.name,prodtype.name))
            if o.CT == 0.0:
                errors.append("Cycle time of product type %s operation %s is 0.0." % (prodtype.name,o.name))
        if max_ct == 0:
            errors.append("Max cycle time for product type '%s' is 0." % (prodtype.name,))

    def resetFlow(prodtype):
        for o in prodtype.operations:
            o.reachedFromStart = False
            o.reachToEnd = False

    def traverseFlow(prodtype,op,direction):
        if direction == "->":
            o = prodtype.getOp(op)
            if o:
                if not o.reachedFromStart:
                    o.reachedFromStart = True
                    for s in prodtype.getSucc(op):
                        traverseFlow(prodtype,s.to,direction)
            else:
                return
        else:
            o = prodtype.getOp(op)
            if o:
                o.reachToEnd = True
            if prodtype.startOp == op:
                return
            for pred in prodtype.getPred(op):
                if not prodtype.getOp(pred).reachToEnd:
                    traverseFlow(prodtype,pred,direction)

    def checkFlow(prodtype, errors):
            for o in prodtype.operations:
                if not o.reachedFromStart:
                    errors.append("Operation '%s' of product type '%s' can not be reached from start operation." % (o.name,prodtype.name))
                if not o.reachToEnd:
                    errors.append("Operation '%s' of product type '%s' can not reach process flow SINK." % (o.name,prodtype.name))

    checkWorkcenter(model,errors)
    checkProdtypes(model,errors)
    for p in model.prodtypes:
        checkOperations(p, errors)
        if not look4Sink(p):
            errors.append("No SINK found in process flow for product type '%s'" % p.name)
        else:
            resetFlow(p)
            traverseFlow(p,p.startOp,"->")
            traverseFlow(p,len(p.operations)+1,"<-")
            checkFlow(p,errors)


def storeAttr(o,p):
    val = p.GetValueAsString()
    msg = ""
    if p.GetName() == "unitOfTime":
        val = unitOfTime.index(val)
    if p.GetName() == "BufferIsFloorSpace":
        if val == "True":
            val = "1"
        else:
            val = "0"
    try:
        v = int(val)
        if v < 0:
            return "Value for %s must not be negative !" % p.GetName()
    except ValueError:
        try:
            v = float(val)
            if v < 0:
                return "Value for %s must not be negative !" % p.GetName()
        except ValueError:
            v = val
    if p.GetName() in ("percentage"):
        v /= 100.0
    msg = o.checkProperties(p.GetName(),v)
    if msg:
        return msg
    setattr(o, p.GetName(), v)
    return ""

def genName(name):
    m = re.match(r"([\w\s]+)(\d+)",name)
    if m:
        name = m.group(1) + str(int(m.group(2))+1)
    else:
        name = name + " 2"
    return name

def cloneArtefact(a,l=[],name=""):
    if not name:
        name = genName(a.name)
        if l:
            # Make name unique ...
            while name in [e.name for e in l]:
                name = genName(name)

    a_new = copy.deepcopy(a)
    a_new.name = name
    return(a_new)

def genUniqueName(l,name):
    while name in [e.name for e in l]:
        name = genName(name)
    return name