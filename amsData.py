unitOfTime = ("sec","min","hour")
dataDict = {
    "Operation": {"Label": "Operation", "Usage": "Workcenter Results"},
    # Workcenter Results
    "OverallLoad": {"Label": "Overall Load [Part/&TIMEUNIT&]", "Usage": "Workcenter Results"},
    "UtilNet": {"Label": "Net. Utilization", "Append": "Tot. Utilization", "Usage": "Workcenter Results", "Multiply": 100.0}, 
    "UtilTot": {"Label": "Tot. Utilization", "Append": "Net. Utilization", "Usage": "Workcenter Results", "Multiply": 100.0},
    "LeadTime": {"Label": "Leadtime [&TIMEUNIT&]", "Usage": "Workcenter Results", "Plot": True, "Unit": "&TIMEUNIT&", "Idx": 3 }, 
    "WIP": {"Label": "WIP", "Usage": "Workcenter Results", "Plot": True, "Idx": 4}, 
    "QueueLength": {"Label": "Queue Length Mean", "Append": "Queue Length 90% Quantil", "Usage": "Workcenter Results", "Plot": True, "Idx": 6}, 
    "Quantil": {"Label": "Queue Length 90% Quantil", "Append": "Queue Length Mean", "Usage": "Workcenter Results", "Plot": True, "Idx": 7},
    "SOB": {"Label": "Relative Load SOB", "Usage": "Workcenter Results"},  
    "MFG": {"Label": "Relative Load Mfg", "Usage": "Workcenter Results"},  
    "Hour": {"Label": "Overall Load Per Hour", "Usage": "Workcenter Results"},   
    "Shift": {"Label": "Overall Load Per Shift", "Usage": "Workcenter Results"},   
    "Day": {"Label": "Overall Load Per Day", "Usage": "Workcenter Results"},       
    # Workcenter Results - Cost
    "CostOutOverall": {"Label": "Overall Output Related Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostOpExpense": {"Label": "Operation Expense [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostMatAndSupp": {"Label": "Cost of Material and Supply [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostInventories": {"Label": "Inventory Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostLoss": {"Label": "Cost of Loss [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostHandling": {"Label": "Handling Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostInspection": {"Label": "Inspection Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostUnSchedMaint": {"Label": "Cost of Unscheduled Maintenance [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostTransport": {"Label": "Transport Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},   
    # time related costs  
    "CostTimeOverall": {"Label": "Overall Time Related Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostDepreciation": {"Label": "Depreciation [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostServAndMat": {"Label": "Cost of Service & Maintenance [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostSchedMaint": {"Label": "Cost of Scheduled Maintenance", "Usage": "Workcenter Results Cost"},
    "CostFloorSpace": {"Label": "Cost of Floor Space [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    "CostSpecArea": {"Label": "Cost of Special Area [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},
    # totals
    "CostManFacPerPart": {"Label": "Total Manufacturing Cost [&CURRENCY&/Part]", "Usage": "Workcenter Results Cost"},     # CostOutOverall + CostTimeOverall 
    "CostIncome": {"Label": "Income [&CURRENCY&/Day]", "Usage": "Workcenter Results Cost"},            # average income per WC 
    "CostProfitPerPart": {"Label": "Profit per Part", "Usage": "Workcenter Results Cost"},     # income - CostManFac 
    "CostManFacPerTU": {"Label": "Manufacturing Cost [&CURRENCY&/&TIMEUNIT&]", "Usage": "Workcenter Results Cost"},
    "CostProfitPerTU": {"Label": "Profit per &TIMEUNIT&", "Usage": "Workcenter Results Cost"},    
    # Workcenter Results - Resources
    "SchedMaintTime": {"Label": "Scheduled Maintenance Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "UnschedMaintTime": {"Label": "Un-scheduled Maintenance Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "HandlingTime": {"Label": "Handling Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "InspectionTime": {"Label": "Inspection Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "TransportTime": {"Label": "Transport Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "OperatingTime": {"Label": "Operating Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    "WCTime": {"Label": "Workcenter Time [&TIMEUNIT&/Part]", "Usage": "Workcenter Results Resources"},
    # Space
    "FloorSpace": {"Label": "Floor Space [sqm]", "Usage": "Workcenter Results Resources", "Plot": True, "Unit": "sqm", "Idx": 8},
    "SpecialArea": {"Label": "Special Area Space [sqm]", "Usage": "Workcenter Results Resources", "Plot": True, "Unit": "sqm", "Idx": 9},
    "WaitingRoom": {"Label": "Waiting Room [sqm]", "Usage": "Workcenter Results Resources"},
    # Number of Operators 
    "OpSchedMaint": {"Label": "# Operator for scheduled maintenance", "Usage": "Workcenter Results Resources"},
    "OpUnschedMaint": {"Label": "# Operator for un-scheduled maintenance", "Usage": "Workcenter Results Resources"},
    "OpHandling": {"Label": "# Operator for handling", "Usage": "Workcenter Results Resources"},
    "OpInspection": {"Label": "# Operator for inspection", "Usage": "Workcenter Results Resources"},
    "OpTransport": {"Label": "# Operator for transport", "Usage": "Workcenter Results Resources"},
    "OpTotal": {"Label": "Total # Operator", "Usage": "Workcenter Results Resources"},
    "OverallFactor": {"Label": "OverallFactor", "Usage": "Workcenter Results Resources"},           
    # Workcenter Properties
    "NumWS": {"Label": "# Work Stations", "Usage": "Workcenter", "Group": "Basic"},
    "Batchsize": {"Label": "Batchsize", "Usage": "Workcenter", "Group": "Basic"},
    "COV": {"Label": "CoV", "Usage": "Workcenter", "Group": "Basic"},
    "Rel": {"Label": "Reliability", "Usage": "Workcenter", "Group": "Basic"},
    "MDT": {"Label": "Mean Down Time [&TIMEUNIT&]", "Usage": "Workcenter", "Group": "Basic"},
    "COVofMDT": {"Label": "CoV of Mean Down Time", "Usage": "Workcenter", "Group": "Basic"},
    "Cost_Depr": {"Label": "Depreciation Cost [&CURRENCY&/Year]", "Usage": "Workcenter", "Group": "Cost"},
    "Cost_SM": {"Label": "Service & Maintenance Cost [&CURRENCY&/Year]", "Usage": "Workcenter", "Group": "Cost"},
    "Cost_Op": {"Label": "Operation Cost [&CURRENCY&/&TIMEUNIT&]", "Usage": "Workcenter", "Group": "Cost"},
    "Res_Floor": {"Label": "Floor Space [sqm]", "Usage": "Workcenter", "Group": "Resource"},
    "Res_Area": {"Label": "Special Area [sqm]", "Usage": "Workcenter", "Group": "Resource"},
    "BufferIsFloorSpace": {"Label": "Buffer Is Floor Space", "Usage": "Workcenter", "Group": "Resource"},
    "Maint_S": {"Label": "Scheduled Maintenance [hours/day]", "Usage": "Workcenter", "Group": "Resource"},
    "Maint_U": {"Label": "Un-scheduled Maintenance [&TIMEUNIT&]", "Usage": "Workcenter", "Group": "Resource"},
    # Product Type Properties
    "percentage": {"Label": "Percentage", "Usage": "ProductType", "Group": "Basic"},
    "inParts": {"Label": "In Parts", "Usage": "ProductType", "Group": "Basic"},
    "outParts": {"Label": "Out Parts", "Usage": "ProductType", "Group": "Basic"},
    "description": {"Label": "Description", "Usage": "ProductType", "Group": "Basic"},
    "startOp": {"Label": "Start Operation", "Usage": "ProductType", "Group": "Basic"},
    "Cost_Inventory": {"Label": "Inventory Cost [&CURRENCY&/&TIMEUNIT&]", "Usage": "ProductType", "Group": "Basic"},
    "Res_Space": {"Label": "Space [sqm]", "Usage": "ProductType", "Group": "Basic"},
    "Income": {"Label": "Income [&CURRENCY&/part]", "Usage": "ProductType", "Group": "Basic"},
    # Extra Plot Values
    "Throughput": {"Label": "Throughput", "Unit": "[part/&TIMEUNIT&]", "Plot": True, "Idx": 1},     
    "Utilization": {"Label": "Utilization", "Unit": "%", "Plot": True, "Idx": 2},     
    "Efficiency": {"Label": "Efficiency", "Unit": "%", "Plot": True, "Idx": 5},
    "NumOperators": {"Label": "Total # Operator", "Unit": "", "Plot": True, "Idx": 7},
    "OutCosts": {"Label": "Overall Output Related Cost", "Unit": "&CURRENCY&/Part", "Plot": True, "Idx": 10},
    "TimeCosts": {"Label": "Overall Time Related Cost", "Unit": "&CURRENCY&/Part", "Plot": True, "Idx": 11},
    "ManFacCostsPerPart": {"Label": "Total Manufacturing Cost", "Unit": "&CURRENCY&/Part", "Plot": True, "Idx": 12},
    "ManFacCostsPerTU": {"Label": "Manufacturing Cost per Unit Of Time", "Unit": "&CURRENCY&/&TIMEUNIT&", "Plot": True, "Idx": 13},  
    "IncomePerDay": {"Label": "Income", "Unit": "&CURRENCY&/Day", "Plot": True, "Idx": 14},
    "ProfitPerPart": {"Label": "Profit per Part", "Unit": "&CURRENCY&/Part", "Plot": True, "Idx": 15},
    "ProfitPerTU": {"Label": "Profit per Unit of Time", "Unit": "&CURRENCY&/&TIMEUNIT&", "Plot": True, "Idx": 16},
    "ProfitPerDay": {"Label": "Profit per Day", "Unit": "&CURRENCY&/Day", "Plot": True, "Idx": 17},
    "ManFacCostsPerDay": {"Label": "Manufacturing Cost per Day", "Unit": "&CURRENCY&/Day", "Plot": True, "Idx": 18}
}

def getDataDictItem(name):
    try:
        return dataDict[name]
    except KeyError:
        for d in dataDict:
            if dataDict[d].get("Label") == name:
                return dataDict[d]    
        return {}        

def getDataDictItems(what,model,group=""):
    dict = {}
    for d in dataDict:
        if dataDict[d].get("Usage") == what or (what=="Plot" and dataDict[d].get("Plot")):
            if not group or dataDict[d].get("Group") == group:
                dict[d] = dataDict[d].copy()
                dict[d]["Label"] =  resolveTags(dict[d]["Label"],model)
                try:
                    dict[d]["Unit"] =  resolveTags(dict[d]["Unit"],model)
                except KeyError: pass    
    return dict        

def getLabel(d,model):
    return resolveTags(dataDict[d]["Label"],model)

def resolveTags(s,model):
    return s.replace("&TIMEUNIT&",unitOfTime[model.unitOfTime]) \
                                                    .replace("&CURRENCY&",model.currency)     

def getPlotsAvailable():
    dict = {}
    for d in dataDict:
            if dataDict[d].get("Plot"):
                dict[d] = dataDict[d]
    # Now sort by "Idx" ...
    dictSorted = sorted(dict.items(), key=lambda x: x[1]["Idx"])                
    l = []
    for d in dictSorted:
        l.append(d[0])
    return l                                                                    