import numpy as np
import math
import pprint
from amsModel import SFac, ResLine, ResWC, ResultGraph

TimeFactors = (86400,1440,24)
EXACTNESS = 0.00000001
MAXITERATIONS = 10000
PROBARRAYLEN = 51
LOG_ZERO_POINT_ONE = -2.302585092994045
WIP_START_VALUE_TO_OAR = 0.1
DBL_MAX = 1.7976931348623158e+308
ARR_RATE_EXACTNESS  = 1e-10
ARR_RATE_ITERATIONS = 100
WEEKSPERYEAR = 52
TIMEYEAR = 6
TIMEMONTH = 5
TIMEWEEK = 4
TIMEDAY = 3
TIMEHOUR = 2
TIMEMIN = 1
TIMESEC = 0

CostIndices = { 
                    # Output related costs per WC
                   "CostOutOverall": 0,
                   "CostOpExpense": 1,
                   "CostMatAndSupp": 2,
                   "CostInventories": 3,
                   "CostLoss": 4,
                   "CostHandling": 5,
                   "CostInspection": 6,
                   "CostUnSchedMaint": 7,
                   "CostTransport": 8,
                    # Time related costs per WC
                   "CostTimeOverall": 9,
                   "CostDepreciation": 10,
                   "CostServAndMat": 11,
                   "CostSchedMaint": 12,
                   "CostFloorSpace": 13,
                   "CostSpecArea": 14,
                   # totals
                   "CostManFacPerPart": 15,     # CostOutOverall + CostTimeOverall 
                   "CostProfitPerPart": 16,     # income - CostManFac                    
                   "CostIncome": 17,            # average income per WC 
                   "CostManFacPerTU": 18,
                   "CostProfitPerTU": 19,
                   "CostProfitPerDay": 20,
                   "CostManFacPerDay": 21
                   }

Resources = {        
   # Time 
   "SchedMaintTime": 0.0,
   "UnschedMaintTime": 0.0,
   "HandlingTime": 0.0,
   "InspectionTime": 0.0,
   "TransportTime": 0.0,
   "OperatingTime": 0.0,
   "WCTime": 0.0,
   # Space
   "FloorSpace": 0.0,
   "SpecialArea": 0.0,
   "WaitingRoom": 0.0,
   # Number of Operators 
   "OpSchedMaint": 0.0,
   "OpUnschedMaint": 0.0,
   "OpHandling": 0.0,
   "OpInspection": 0.0,
   "OpTransport": 0.0,
   "OpTotal": 0.0,
   # Overall factor
   "OverallFactor": 0.0
}

def ConvertAR(model,input,oldIMode,newIMode,AdvancedMethod=False):
    if newIMode == "IMODE_AR":
        conversion = 1.0
    elif newIMode == "IMODE_DR":
        conversion = model.YieldTot2
    elif newIMode == "IMODE_SOB":
        conversion = model.hoursPerDay * TimeFactors[model.unitOfTime] / 24.0
    elif newIMode == "IMODE_SHIP":
        conversion = model.hoursPerDay * TimeFactors[model.unitOfTime] * model.YieldTot2 / 24.0

    if oldIMode == "IMODE_DR":
        conversion /= model.YieldTot2
    elif oldIMode == "IMODE_SOB":
        conversion *= 24.0 / model.hoursPerDay / TimeFactors[model.unitOfTime]
    elif oldIMode == "IMODE_SHIP":
        conversion *= 24.0 / model.hoursPerDay / TimeFactors[model.unitOfTime] / model.YieldTot2
    elif oldIMode == "IMODE_WIP":
        oar = CompArrivalRate(model,input,ARR_RATE_EXACTNESS,ARR_RATE_ITERATIONS,AdvancedMethod)
        return oar            
    return input * conversion


def initialComputations(model):
    CompSFactors(model)
    CompWCSFactorsAndSums(model)
    CompAuxValArraysAndOAR(model)
    CompTotalYield(model)
    model.bComputed = True

def CompSFactors(model):
    r = 0
    for p in model.prodtypes:
        # Initialize the probability matrix and the diagonal vectors
        n = len(p.operations)+1
        m = np.array([0.0,]*n*n).reshape(n,n)
        SFactorTab = np.array([0.0,]*n)
        SFactorTabNew = np.array([0.0,]*n)
        diagvec = np.array([1.0,]*n)
        # Get the (inversed) probability matrix (subtracted from E-Matrix) and the diagonal vectors
        GetTransProbMatrix(model, p, diagvec, m)
        # Calculate the S factors without split/join factors
        rc = SpezGaussSeidel(n, m, diagvec, p.startOp-1, SFactorTab)
        p.SFactorTab = SFactorTab
	    # Calculate the S-Factors with split/join factors
		# First change the prob. matrix and diagvev
        for c in range(len(diagvec)):
            myoper = p.getOp(c+1)
            if diagvec[c] != 1.0:
                diagvec[c] = (1.0 - diagvec[c]) * myoper.SJFactor
            for r in range(len(m)):
                mysucc = p.getOp(c+1)
                m[c,r] *= mysucc.SJFactor
        rc = SpezGaussSeidel(n, m, diagvec, p.startOp-1, SFactorTabNew)
        p.SFactorTabNew = SFactorTabNew

def GetTransProbMatrix(model, prodtype, diagvec, m):
    for i in range(len(prodtype.operations)):
        for s in prodtype.getSucc(i+1):
            if (i+1) == s.to:
                diagvec[s.to-1] = s.Prob * -1
            else:
                m[i][s.to-1] -= s.Prob

def SpezGaussSeidel(N, SMat, DiagVec, ConstPos, Solution, R=EXACTNESS, Maxit=MAXITERATIONS):
    for Iterations in range(Maxit):
        CurrRow = 0
        Norm = 0.0
        for row in range(N):
            STemp = 1.0 if row==ConstPos else 0.0
            for col in range(SMat.shape[0]):
                STemp -= SMat[col,row] * Solution[col]
            STemp /= DiagVec[row]
            Norm = max(abs(STemp-Solution[row]),Norm)
            Solution[row] = STemp
        if Norm < R:
            return 0
    return 1

def CompWCSFactorsAndSums(model):
    model.m_Summ1 = np.array([0.0,]*len(model.workcenter))
    model.m_Summ2 = np.array([0.0,]*len(model.workcenter))
    model.m_Summ3 = np.array([0.0,]*len(model.workcenter))
    for i_p in range(len(model.prodtypes)):
        p = model.prodtypes[i_p]
        p.WCSFactorTab = np.array([0.0,]*len(model.workcenter))
        p.WCSFactorTab2 = np.array([0.0,]*len(model.workcenter))
        SFNo=0
        SFNo2=0
        for i_o in range(len(p.operations)):
            o = p.operations[i_o]
            WCNo = o.WCNumber
            p.WCSFactorTab[WCNo-1] += p.SFactorTab[SFNo]
            SFNo += 1
            Temp = p.SFactorTabNew[SFNo2]
            p.WCSFactorTab2[WCNo-1] += Temp
            SFNo2 += 1
            Temp *= p.percentage
            model.m_Summ1[WCNo-1] += Temp
            Temp *= o.CT
            model.m_Summ2[WCNo-1] += Temp
            model.m_Summ3[WCNo-1] += Temp * o.CT

def CompAuxValArraysAndOAR(model):
    model.m_HSumm = np.array([0.0,]*len(model.workcenter))
    model.m_VCompl = np.array([0.0,]*len(model.workcenter))
    model.m_MeanCycleTimes = np.array([0.0,]*len(model.workcenter))
    model.MaxOAR = 999999
    model.Bottleneck = -1
    for w in range(len(model.workcenter)):
        if (model.m_Summ1[w] == 0 or model.m_Summ2[w] == 0):
             continue
        CurrWC = model.workcenter[w]
        model.m_HSumm[w] = 0.0
        for i_p in range(len(model.prodtypes)):
            p = model.prodtypes[i_p]
            model.m_HSumm[w] += p.percentage * p.WCSFactorTab[w]
            if CurrWC.NumWS > 0:
                Temp = CurrWC.Rel * CurrWC.NumWS * CurrWC.Batchsize / model.m_Summ2[w]
                if Temp < model.MaxOAR:
                    model.MaxOAR = Temp
                    model.Bottleneck = w
            model.m_MeanCycleTimes[w] = model.m_Summ2[w] / model.m_Summ1[w]
            model.m_VCompl[w] = (1 + (CurrWC.COV * CurrWC.COV)) * model.m_Summ3[w] / model.m_Summ2[w] / model.m_MeanCycleTimes[w] - 1.0
            model.m_VCompl[w] +=  1.0 + (CurrWC.COVofMDT * CurrWC.COVofMDT) * CurrWC.MDT * (1.0 - CurrWC.Rel) * CurrWC.Rel / model.m_MeanCycleTimes[w]    

def CompTotalYield(model):
    model.YieldTot = 0.0
    model.YieldTot2 = 0.0
    for i_p in range(len(model.prodtypes)):
        p = model.prodtypes[i_p]
        model.YieldTot  += p.SFactorTab[-1] * p.percentage
        model.YieldTot2 += p.SFactorTabNew[-1] * p.percentage

def ComputeWorkloadTable(model,idxType,DailyOut):
    if not model.bComputed:
        initialComputations(model)
    CompSplitJoinWC(model)
    DailyIn = CompSFTable(model,idxType,DailyOut)


def CompSplitJoinWC(model):
    model.m_SplitJoinWC = np.array([0.0,]*len(model.workcenter))
    for i_p in range(len(model.prodtypes)):
        p = model.prodtypes[i_p]
        for i_o in range(len(p.operations)):
            o = p.operations[i_o]
            model.m_SplitJoinWC[o.WCNumber-1] += o.SJFactor * p.percentage * p.SFactorTabNew[i_o]
    for i, w in enumerate(model.workcenter):            
        if w.Used:
            model.m_SplitJoinWC[i] /= model.m_Summ1[i]

def CompSFTable(model,idxType,DailyOut):
    # Computes a table with Startfactor-values
    CurrType = model.prodtypes[idxType]
    Yield = CurrType.SFactorTabNew[len(CurrType.operations)]
    for w in range(len(model.workcenter)):
        wc = model.workcenter[w]
        wc.SFTable = SFac()
        SOB = CurrType.WCSFactorTab2[w]
        wc.SFTable.SOB = SOB
        wc.SFTable.MFG = SOB
        wc.SFTable.MFG /= Yield
        wc.SFTable.Hour = wc.SFTable.MFG * DailyOut / model.hoursPerDay
        wc.SFTable.Shift = wc.SFTable.Hour * model.hoursPerShift
        wc.SFTable.Day = wc.SFTable.MFG * DailyOut * 24.0 / model.hoursPerDay
    for i_o in range(len(model.prodtypes[idxType].operations)):
        op = model.prodtypes[idxType].operations[i_o]
        op.SFTable = SFac()
        SOB = CurrType.SFactorTabNew[i_o]
        op.SFTable.SOB =  SOB
        op.SFTable.MFG = SOB
        op.SFTable.MFG /= Yield
        op.SFTable.Hour = op.SFTable.MFG * DailyOut / model.hoursPerDay
        op.SFTable.Shift = op.SFTable.Hour * model.hoursPerShift
        op.SFTable.Day = op.SFTable.MFG * DailyOut * 24.0 / model.hoursPerDay
    return DailyOut / Yield

def ComputeCapTable(model):
    if not model.bComputed:
        initialComputations(model)
    WIP, OAR = CompCapTable(model)    
    return WIP, OAR

def CompCapTable(model):    
    # Computes New Capacity-Requirements
    WaitingTime = OAR = WIP = 0.0
    for i, t in enumerate(model.prodtypes):
        t.DayOut = t.WeekOut / model.daysPerWeek
        t.OAR = t.DayOut / (t.SFactorTabNew[-1] * TimeFactors[model.unitOfTime]) * 24.0 / model.hoursPerDay
        OAR += t.OAR
    for i, t in enumerate(model.prodtypes):
        t.new_percentage = t.OAR / OAR
        t.DayIn = t.DayOut / t.SFactorTabNew[-1]
        t.WeekIn = t.DayIn * model.daysPerWeek
    # Computation of new work station number                         
    for i, w in enumerate(model.workcenter):    
        w.NWSNum = OAR * model.m_Summ2[i] / (w.Rel * w.Batchsize)
        w.NewWSNum = math.ceil(w.NWSNum)
        if w.NumWS > 0:
            w.Differ = w.NewWSNum - w.NumWS
        else:
            w.Differ = 0
    # Computation of new work in process  
    for i, w in enumerate(model.workcenter):    
        if not w.Used:
            continue
        OverallLoad =  OAR  * model.m_Summ1[i]
        MeanCycleTime =  model.m_Summ2[i] / model.m_Summ1[i]
        MeanCycleTime2 =  model.m_Summ3[i] / model.m_Summ1[i]
        if w.NewWSNum > 0:
            UtilTot = OverallLoad * MeanCycleTime / (w.NewWSNum * w.Batchsize * w.Rel)
            P = UtilTot ** (w.NewWSNum+1)/2.0
            QueueLength = UtilTot  / ( 1.0 - UtilTot) \
                * (( 1.0 + (w.Batchsize * model.m_VCompl[i])) / 2.0 ) * P + ((w.Batchsize -1) / 2.0)
            LeadTime = (QueueLength + (OverallLoad * model.m_MeanCycleTimes[i] / w.Rel)) /  OverallLoad
        else:
            LeadTime = model.m_MeanCycleTimes[i]
        WaitingTime += model.m_HSumm[i] * LeadTime
    WIP = WaitingTime * OAR * model.YieldTot2 / model.YieldTot
    return WIP, OAR

def CompTabOverall(model,OAR,AdvancedMethod=False):
    for p in model.prodtypes:
        p.weekOut = ConvertAR(model,OAR,"IMODE_AR","IMODE_SHIP") * p.percentage * model.daysPerWeek
    # Compute overall work center results
    CompResWC(model,OAR,AdvancedMethod)
    # Compute overall line results
    CompResOverall(model,OAR,AdvancedMethod)
    # Compute work center results for all prod. types
    CompResTypeWC(model,OAR,AdvancedMethod)
    # Compute line results for all prod. types
    CompResTypeLine(model,OAR,AdvancedMethod)

def CompResOverall(model,OAR,AdvancedMethod):
    model.ResTable = ResLine()
    model.ResTable.DaysPerWeek = model.daysPerWeek
    model.ResTable.HoursPerDay = model.hoursPerDay
    model.ResTable.MaxOAR = model.MaxOAR
    model.ResTable.MaxODR = ConvertAR(model,model.MaxOAR,"IMODE_AR","IMODE_DR")
    model.ResTable.OAR = OAR
    model.ResTable.ThroughputMax = model.MaxOAR * model.YieldTot2 * model.hoursPerDay * TimeFactors[model.unitOfTime] / 24.0
    model.ResTable.StartMax = ConvertAR(model,model.ResTable.ThroughputMax,"IMODE_SHIP","IMODE_SOB")
    model.ResTable.GoodPartsOut = OAR * model.YieldTot2
    model.ResTable.Yield = model.YieldTot
    model.ResTable.DGRStart = OAR * model.hoursPerDay / 24.0 * TimeFactors[model.unitOfTime]
    model.ResTable.DGRShip = model.ResTable.DGRStart * model.YieldTot2
    if model.ResTable.GoodPartsOut == 0:
        model.ResTable.TactTime = -1
    else:
        model.ResTable.TactTime = 1.0 / model.ResTable.GoodPartsOut
    UtilAverage = 0.0
    LeadTimeNet = 0.0
    RawCycleTime = 0.0
    for i, w in enumerate(model.workcenter):    
        if not w.Used:
            continue
        w = model.workcenter[i]
        UtilAverage += w.ResTable.UtilTot
        if w.ResTable.LeadTime > -1:
            LeadTimeNet += w.ResTable.LeadTime * model.m_HSumm[i]
        RawCycleTime += w.ResTable.RawCycleTime * model.m_HSumm[i]
    model.ResTable.UtilAverage = UtilAverage / len(model.workcenter)
    model.ResTable.LeadTimeNet = LeadTimeNet
    model.ResTable.RawCycleTime = RawCycleTime
    if model.YieldTot == 0:
        model.ResTable.WIP = -1
    else:
        model.ResTable.WIP = LeadTimeNet * OAR * model.YieldTot2  / model.YieldTot
    model.ResTable.LeadTimeTot = model.ResTable.LeadTimeNet * 24.0 / model.hoursPerDay *  7.0 / model.daysPerWeek
    if model.ResTable.LeadTimeNet == 0:
        model.ResTable.EfficiencyNet = -1
    else:
        model.ResTable.EfficiencyNet = model.ResTable.RawCycleTime / model.ResTable.LeadTimeNet
    if model.ResTable.LeadTimeTot == 0:
        model.ResTable.EfficiencyTot = -1
    else:
        model.ResTable.EfficiencyTot = model.ResTable.RawCycleTime / model.ResTable.LeadTimeTot

def CompResTypeLine(model,OAR,AdvancedMethod):
    for i_t in range(len(model.prodtypes)):
        t = model.prodtypes[i_t]
        t.ResTable = ResLine()
        t.ResTable.DaysPerWeek = model.daysPerWeek
        t.ResTable.HoursPerDay = model.hoursPerDay
        t.ResTable.MaxOAR = model.MaxOAR * t.percentage
        t.ResTable.OAR = OAR * t.percentage
        t.ResTable.Yield = t.SFactorTabNew[-1]
        t.ResTable.GoodPartsOut = t.ResTable.OAR * t.ResTable.Yield
        t.ResTable.ThroughputMax = t.ResTable.MaxOAR * t.ResTable.Yield * model.hoursPerDay / 24.0 * TimeFactors[model.unitOfTime]
        t.ResTable.DGRStart = t.ResTable.OAR * model.hoursPerDay / 24.0 * TimeFactors[model.unitOfTime]
        t.ResTable.DGRShip = t.ResTable.DGRStart * t.ResTable.Yield
        if t.ResTable.GoodPartsOut == 0:
            t.ResTable.TactTime = -1
        else:
            t.ResTable.TactTime = 1.0 / t.ResTable.GoodPartsOut
        t.ResTable.UtilAverage = 0.0
        t.ResTable.LeadTimeNet = 0.0
        t.ResTable.RawCycleTime = 0.0
        for i, w in enumerate(model.workcenter):    
            if not w.Used:
                continue
            w = model.workcenter[i]
            t.ResTable.UtilAverage += w.ResTable.UtilNet
            t.ResTable.LeadTimeNet += w.ResTable.LeadTime * t.WCSFactorTab[i]
        t.ResTable.UtilAverage /= len(model.workcenter)
        t.ResTable.LeadTimeTot = t.ResTable.LeadTimeNet * 24.0 / model.hoursPerDay *  7.0 / model.daysPerWeek
        if t.SFactorTab[len(t.operations)] == 0:
            t.ResTable.WIP = -1
        else:
            t.ResTable.WIP = t.ResTable.LeadTimeNet * t.ResTable.GoodPartsOut / t.SFactorTab[len(t.operations)]
        for i_o in range(len(t.operations)):
            o = t.operations[i_o]
            WCNo = o.WCNumber
            t.ResTable.RawCycleTime += t.SFactorTab[i_o] * o.CT / model.workcenter[WCNo-1].Rel
        if t.ResTable.LeadTimeNet == 0:
            t.ResTable.EfficiencyNet = -1
        else:
            t.ResTable.EfficiencyNet = t.ResTable.RawCycleTime / t.ResTable.LeadTimeNet
        if t.ResTable.LeadTimeTot == 0:
            t.ResTable.EfficiencyTot = -1
        else:
            t.ResTable.EfficiencyTot = t.ResTable.RawCycleTime / t.ResTable.LeadTimeTot


def CompResWC(model,OAR,AdvancedMethod):
    CVEntry = 1.0
    for i, w in enumerate(model.workcenter):    
        if not w.Used:
            continue
        w = model.workcenter[i]
        w.ResTable = ResWC()
        OverallLoad      = OAR * model.m_Summ1[i]
        w.ResTable.TotCycleTime = 0.0
        w.ResTable.OverallLoad  = OverallLoad
        if w.NumWS > 0:
            w.ResTable.UtilNet = OverallLoad * model.m_MeanCycleTimes[i] / w.NumWS / w.Batchsize
            w.ResTable.UtilTot = w.ResTable.UtilNet / w.Rel
            w.ResTable.QueueLength, P = CompQueueLengthWC(w,OverallLoad,model.m_MeanCycleTimes[i],model.m_VCompl[i],CVEntry)
            w.ResTable.RawCycleTime = model.m_MeanCycleTimes[i] / w.Rel
            w.ResTable.WIP = w.ResTable.QueueLength + OverallLoad * w.ResTable.RawCycleTime
            if OverallLoad == 0:
                w.ResTable.LeadTime = -1
            else:
                w.ResTable.LeadTime = w.ResTable.WIP / OverallLoad
        else:
            # If the work centre has infinite capacity
            w.ResTable.UtilNet     = 0.0
            w.ResTable.UtilTot     = 0.0
            w.ResTable.QueueLength = 0.0
            w.ResTable.WIP         = OverallLoad * model.m_MeanCycleTimes[i] / w.Rel
            w.ResTable.LeadTime    = model.m_MeanCycleTimes[i]
        # Now compute alpha quantil
        if w.ResTable.UtilTot > 0.0:
            Quantil = math.ceil ( ( ( LOG_ZERO_POINT_ONE - math.log(P) )                 \
                            / math.log(w.ResTable.UtilTot) - 1.0 )                        \
                        * ( 1.0 / w.Batchsize + model.m_VCompl[i] ) / 2.0 )     \
                        * w.Batchsize  + w.Batchsize

            if Quantil <= 1.0:
                w.ResTable.Quantil = 1.0
            else:
                w.ResTable.Quantil = math.ceil(Quantil)
        else:
        #  UtilTot <= 0.0
            w.ResTable.Quantil = 0.0

def CompResTypeWC(model,OAR,AdvancedMethod):
    CVEntry = 1.0
    for i_t in range(len(model.prodtypes)):
        t = model.prodtypes[i_t]
        t.ResWCTable = []
        ArrivalRate = OAR * t.percentage
        for i in range(len(model.workcenter)):
            t.ResWCTable.append(ResWC())
        for i_o in range(len(t.operations)):
            o = t.operations[i_o]
            WCNo = o.WCNumber
            t.ResWCTable[WCNo-1].TotCycleTime = t.SFactorTabNew[i_o] * o.CT
            t.ResWCTable[WCNo-1].WCUsed = True
        for i in range(len(model.workcenter)):
            w = model.workcenter[i]
            ResTable = t.ResWCTable[i]
            if ResTable.WCUsed:
                OverallLoad      = OAR * model.m_Summ1[i]
                ResTable.OverallLoad  = ArrivalRate * t.WCSFactorTab2[i]
                if w.NumWS > 0:
                    ResTable.UtilNet = ArrivalRate * ResTable.TotCycleTime / w.NumWS / w.Batchsize
                    if OverallLoad == 0:
                        ResTable.QueueLength = -1
                    else:
                        QL, P = CompQueueLengthWC(w,OverallLoad,model.m_MeanCycleTimes[i],model.m_VCompl[i],CVEntry)
                        ResTable.QueueLength = ResTable.OverallLoad / OverallLoad * QL
                else:
                    ResTable.UtilNet = 0.0
                    ResTable.QueueLength = 0.0
                ResTable.WIP = ResTable.QueueLength + ResTable.OverallLoad * ResTable.TotCycleTime / w.Rel
                if ResTable.OverallLoad == 0:
                    ResTable.LeadTime = -1
                else:
                    ResTable.LeadTime = ResTable.WIP / ResTable.OverallLoad
                ResTable.RawCycleTime = ResTable.TotCycleTime / w.Rel
            else:
                ResTable.LeadTime = 0.0
                ResTable.OverallLoad = 0.0
                ResTable.QueueLength = 0.0
                ResTable.RawCycleTime = 0.0
                ResTable.TotCycleTime = 0.0
                ResTable.UtilNet = 0.0
                ResTable.WIP = 0.0
            t.ResWCTable[i] = ResTable

def CompQueueLengthWC(w,OverallLoad,MCT,VC,CVEntry):
    if w.NumWS > 0:
        UtilTot = OverallLoad * MCT / w.NumWS  / w.Batchsize  / w.Rel
        if UtilTot > 0.0:
            dProb = CompOccupationProbability(w.NumWS, UtilTot)
            # compute queue length
            QueueLength = ( UtilTot / ( 1.0 - UtilTot ) * dProb \
                        * ( CVEntry + w.Batchsize * VC ) \
                        + ( w.Batchsize - 1.0) ) / 2.0
        else:
            dProb = 0.0
            QueueLength = 0.0
    else:
        dProb = 0.0
        QueueLength = 0.0
    return QueueLength, dProb



def CompOccupationProbability(N, UtilTot):
    PolyArrays = CompProbPolyArray( PROBARRAYLEN )
    if UtilTot != 0.0:
        if N < PROBARRAYLEN:
            Prob = 1.0 / CompPolyValue(PolyArrays, N, N, 1.0 / UtilTot )
        else:
            SpecialPolyArray = np.array([0.0,]*1*(N+1)).reshape(1,N+1)
            CompProbPoly(SpecialPolyArray, 1, N)
            # now compute the probability
            Prob = 1.0 / CompPolyValue(SpecialPolyArray, 1, N, 1.0 / UtilTot)
    else:
        Prob = 0.0
    return Prob

def CompPolyValue(Mat, index, N, X ):
    i = N
    Value = Mat[index][i]
    # Horner iteration
    for i in range(N-1,-1,-1):
        Value *= X
        Value += Mat[index][i]
    return Value

def CompProbPolyArray(ServNum):
    PolyArrays = np.array([0.0,]*(PROBARRAYLEN+1)*(PROBARRAYLEN+1)).reshape(PROBARRAYLEN+1,PROBARRAYLEN+1)
    for I in range(ServNum):
        PolyArrays = CompProbPoly(PolyArrays, I, I)
    return PolyArrays

def CompProbPoly(Mat, index, NumWS):
    # compute the coefficients */
    # in case of a finite server */
    if NumWS > 0:
        # initialize variables
        NumWSInverse = 1.0 / NumWS
        Factor1      = 1.0
        Factor2      = 0.0
        Mat[index][0] = 0.0
        for Count in range(1,NumWS):
            Factor1	   *= 1. - Factor2
            Factor2    += NumWSInverse
            Mat[index][Count] = Factor1 * Factor2
        # set top order factor
        Mat[index][NumWS] = Factor1 * NumWSInverse
    else:
        Mat[index][0] = 0.0
    return Mat

def ComputeDeltaX(maxOAR,NumValues):
    DeltaX = maxOAR /  NumValues
    c = 0
    while (math.floor(DeltaX)==0):
        c += 1
        DeltaX *= 10
    DeltaX = math.floor(DeltaX)
    for i in range(c,0,-1):
        DeltaX /= 10
    return DeltaX

def ComputeMinX(maxOAR,NumValues,DeltaX):
    d = 1
    while True:
        c = 0
        MinX = maxOAR - (NumValues-d) * DeltaX
        while (math.floor(MinX)==0):
            c += 1
            MinX *= 10
        MinX = math.floor(MinX)
        for i in range(c,0,-1):
            MinX /= 10
        d -= 1
        if not (1.0000000000000000001*MinX) >= (maxOAR - (NumValues-1) * DeltaX):
            return MinX

def CompWIP(model,oar,AdvancedMethod=False):
    # Description  : Computes the WIP for overall arrival rate oar.
    CVEntry = 1.0
    WaitingTime = 0.0
    for i in range(len(model.workcenter)):
        w = model.workcenter[i]
        OverallLoad = oar * model.m_Summ1[i]
        if w.NumWS > 0:
            if OverallLoad != 0.0:
                QueueLength, P = CompQueueLengthWC(w,OverallLoad,model.m_MeanCycleTimes[i],model.m_VCompl[i],CVEntry)
                if QueueLength >= DBL_MAX:
                    return DBL_MAX
                WaitingTime += model.m_HSumm[i] * (QueueLength / OverallLoad
                                + model.m_MeanCycleTimes[i] / w.Rel)
            else:
                WaitingTime += model.m_HSumm[i] *  model.m_MeanCycleTimes[i] / w.Rel
        else:
            WaitingTime += model.m_HSumm[i] *  model.m_MeanCycleTimes[i] / w.Rel
    return WaitingTime * oar * model.YieldTot2 / model.YieldTot

def CompArrivalRate(model,WIP,Exact,MaxIt,AdvancedMethod):
    # Description  : Computes the arrival rate corresponding to the WIP. 
    OAR1 = 0.49 * model.MaxOAR
    OAR2 = 0.50 * model.MaxOAR
    WIP1 = CompWIP(model, OAR1, AdvancedMethod)
    if (WIP1 == DBL_MAX):
        return DBL_MAX
    else:
        WIP1 -= WIP
    WIP2 = CompWIP(model, OAR2, AdvancedMethod)
    if (WIP2 == DBL_MAX):
        return DBL_MAX
    else:
        WIP2 -= WIP
    for iterations in range(MaxIt):
        if WIP1 == WIP2:
            return DBL_MAX
        NextOAR = OAR2 - WIP2 * (OAR2 - OAR1) / (WIP2 - WIP1)
        while (NextOAR >= model.MaxOAR):
            NextOAR = (NextOAR + OAR2) / 2.0
        while (NextOAR <= 0.0):
            NextOAR = (NextOAR + OAR2) / 2.0
        NextWIP = CompWIP(model, NextOAR, AdvancedMethod)
        if (NextWIP == DBL_MAX):
            return  DBL_MAX
        else:
            NextWIP -= WIP
        if (abs(NextWIP) < Exact):
            return NextOAR
        else:
            OAR1 = OAR2
            WIP1 = WIP2
            OAR2 = NextOAR
            WIP2 = NextWIP
        if (    abs(OAR2) < Exact):
            return 0.0
    return DBL_MAX

def CompYValues(model,NumValues,AdvancedMethod):
    def getCostAndResources(i,I):
        model.ResGraph[i].OutCosts[I]= CostOverall[i][CostIndices["CostOutOverall"]]
        model.ResGraph[i].TimeCosts[I]= CostOverall[i][CostIndices["CostTimeOverall"]]
        model.ResGraph[i].ManFacCostsPerPart[I]= CostOverall[i][CostIndices["CostManFacPerPart"]]
        model.ResGraph[i].ProfitPerPart[I]= CostOverall[i][CostIndices["CostProfitPerPart"]]
        model.ResGraph[i].ManFacCostsPerTU[I]= CostOverall[i][CostIndices["CostManFacPerTU"]]
        model.ResGraph[i].ManFacCostsPerDay[I]= CostOverall[i][CostIndices["CostManFacPerDay"]]
        model.ResGraph[i].ProfitPerTU[I]= CostOverall[i][CostIndices["CostProfitPerTU"]]
        model.ResGraph[i].ProfitPerDay[I]= CostOverall[i][CostIndices["CostProfitPerDay"]]
        model.ResGraph[i].IncomePerDay[I]= CostOverall[i][CostIndices["CostIncome"]]
        resources = model.ResArray[-1][i]
        model.ResGraph[i].NumOperators[I]= resources["OpTotal"]
        model.ResGraph[i].FloorSpace[I]= resources["FloorSpace"]                                    
        model.ResGraph[i].SpecialArea[I]= resources["SpecialArea"]        

    for I in range(NumValues):
        CompTabOverall(model,model.ResGraph[0].XVal[I])
        model.ResArray = ComputeResource(model)
        model.CostMatrixArray = ComputeCostAll(model)        
        # Compute for workcenter
        for i, w in enumerate(model.workcenter):    
            if not w.Used:
                continue
            model.ResGraph[i].Utilization[I]= w.ResTable.UtilTot * 100.0
            model.ResGraph[i].LeadTime[I]= w.ResTable.LeadTime
            model.ResGraph[i].WIP[I]= w.ResTable.WIP
            model.ResGraph[i].QueueLength[I]= w.ResTable.QueueLength
            model.ResGraph[i].Quantil[I]= w.ResTable.Quantil
            CostOverall = model.CostMatrixArray[-1]
            getCostAndResources(i,I)                                    
            # Compute efficiency and throughput
            model.ResGraph[i].Throughput[I]= model.ResGraph[i].XVal[I] * model.m_Summ1[i]
            if (w.NumWS > 0):
                model.ResGraph[i].Efficiency[I] = model.ResGraph[i].XVal[I] * model.m_Summ2[i] / w.ResTable.WIP * 100.0
            else:
                model.ResGraph[i].Efficiency[I] = 100.0
        # Compute for overall model
        i += 1
        model.ResGraph[i].Utilization[I]= model.ResTable.UtilAverage * 100.0
        model.ResGraph[i].LeadTime[I]= model.ResTable.LeadTimeNet
        model.ResGraph[i].WIP[I]= model.ResTable.WIP
        model.ResGraph[i].Throughput[I]= model.ResGraph[i].XVal[I] * model.YieldTot2
        model.ResGraph[i].Efficiency[I] = model.ResTable.EfficiencyNet * 100.0
        getCostAndResources(i,I)

def CompGraphics(model,NumValues=25,AdvancedMethod=False,WipDriven=False):
    if not model.bComputed:
        initialComputations(model)
    model.ResGraph = []
    # For every work centre ...
    for i in range(len(model.workcenter)):
        w = model.workcenter[i]
        model.ResGraph.append(ResultGraph(NumValues))
    # ... plus overall ...
    model.ResGraph.append(ResultGraph(NumValues))
    if not WipDriven:
        minOAR = model.MaxOAR / 2.0
        deltaX = ComputeDeltaX(model.MaxOAR, NumValues)
        minX = ComputeMinX(model.MaxOAR, NumValues, deltaX)
        minX2   =  0.1  *  model.MaxOAR
        deltaX2 = (0.99 *  model.MaxOAR - minX2 ) / (NumValues - 1 )
    else:
        maxX   = CompWIP(model, model.MaxOAR, AdvancedMethod)
        minX   = CompWIP(model, WIP_START_VALUE_TO_OAR * model.MaxOAR, AdvancedMethod)
        DeltaX = (maxX - minX) / NumValues
    # Calculate x-values
    if not WipDriven:
        for i in range(len(model.workcenter)+1):
            X = minX
            X2 = minX2
            for v in range(NumValues): 
                model.ResGraph[i].XVal[v]=X
                model.ResGraph[i].XVal2[v]=X2
                model.ResGraph[i].DR[v] = ConvertAR(model,X,"IMODE_AR","IMODE_DR")
                model.ResGraph[i].SOB[v] = ConvertAR(model,X,"IMODE_AR","IMODE_SOB")
                model.ResGraph[i].SHIP[v] = ConvertAR(model,X,"IMODE_AR","IMODE_SHIP")
                X += deltaX
                X2 += deltaX2
    else:
        for i in range(len(model.workcenter)+1):
            X = minX
            for v in range(NumValues):
                model.ResGraph[i].XVal[v] = CompArrivalRate(model,X,ARR_RATE_EXACTNESS,ARR_RATE_ITERATIONS,AdvancedMethod)
                X += DeltaX
    # Calculate y-values
    CompYValues(model,NumValues,AdvancedMethod)
    if not WipDriven:
        for i in range(len(model.workcenter)):
            model.ResGraph[i].FactorSOB = model.hoursPerDay / 24.0 * TimeFactors[model.unitOfTime]
            model.ResGraph[i].FactorSHIP = model.ResGraph[i].FactorSOB * model.YieldTot2
            model.ResGraph[i].FactorGPO = model.YieldTot2
    else:
        for i in range(len(model.workcenter)):
            X     = minX
            X2    = minX2
            for v in range(NumValues):
                model.ResGraph[i].XVal[v]=X
                model.ResGraph[i].XVal2[v]=X2
                X += deltaX
                X2 += deltaX2

def TimeScale(OldTime, NewTime):
    #             sec, min,  h,   day   , week ,   month ,    year
    TimeScales = [1.0,60.0,3600.0,86400.0,604800.0,2592000.0,31449600.0]
    return TimeScales[OldTime] / TimeScales[NewTime]

def ComputeResource(model):
    def ComputeOperator(ResOverall,ResNetwork,NumOperatorsFactor):    
        ResOverall["OpHandling"] = ResOverall["HandlingTime"] * NumOperatorsFactor
        ResNetwork["OpHandling"] += ResOverall["OpHandling"]
        ResOverall["OpInspection"] = ResOverall["InspectionTime"] * NumOperatorsFactor
        ResNetwork["OpInspection"] += ResOverall["OpInspection"]       
        ResOverall["OpTransport"] = ResOverall["TransportTime"] * NumOperatorsFactor
        ResNetwork["OpTransport"] += ResOverall["OpTransport"]   
        ResOverall["OpSchedMaint"] = ResOverall["SchedMaintTime"] * NumOperatorsFactor
        ResNetwork["OpSchedMaint"] += ResOverall["OpSchedMaint"]   
        ResOverall["OpUnschedMaint"] = ResOverall["UnschedMaintTime"] * NumOperatorsFactor
        ResNetwork["OpUnschedMaint"] += ResOverall["OpUnschedMaint"]  
        ResOverall["OpTotal"] = ResOverall["OpHandling"] + ResOverall["OpInspection"] + ResOverall["OpTransport"] + ResOverall["OpSchedMaint"] + ResOverall["OpUnschedMaint"]
        ResNetwork["OpTotal"] += ResOverall["OpTotal"]

    # Computes per type and work centre all important resources  
    # (time, space, material) wich are used to compute costs and 
    # resource table     
    n = len(model.prodtypes)+1
    m = len(model.workcenter)+1
    ResArray = [[Resources.copy() for x in range(m)] for y in range(n)] 
    for i, t in enumerate(model.prodtypes):
        if t.percentage == 0.0:
            continue
        DR = t.ResTable.OAR * t.ResTable.Yield
        NumOperatorsFactor = DR / model.OperatorAV            
        OverallFactor = t.ResTable.DGRShip / model.ResTable.DGRShip
        Yield = t.ResTable.Yield
        ResNetwork = ResArray[i][-1]
        for j, o in enumerate(t.operations):
            WCNo = o.WCNumber
            Res = ResArray[i][WCNo-1]
            eim =  t.SFactorTabNew[j] / Yield        # compute relative frequency 
            TransTime = 0.0                          # compute transport time    
            for s in t.getSucc(j+1):     
                TransTime += s.Prob * s.TransitionTime
            Res["OperatingTime"] += eim * o.CT              # operating time      
            Res["HandlingTime"] += eim * o.Time_Handling    # handling time
            Res["InspectionTime"] += eim * o.Time_Inspection    # inspection time
            Res["TransportTime"] += eim * TransTime    # transport time
        for j, w in enumerate(model.workcenter):    
            if not w.Used:
                continue
            Res = ResArray[i][j]
            Res["OperatingTime"] /= w.Batchsize        # Scale OperatingTime to part
            # First add up operation related data ...
            ResNetwork["OperatingTime"] += Res["OperatingTime"]
            ResNetwork["HandlingTime"] += Res["HandlingTime"]
            ResNetwork["InspectionTime"] += Res["InspectionTime"]
            ResNetwork["TransportTime"] += Res["TransportTime"]
            # Workenter time
            # First compute something like UtilNet(i,k)/UtilNet(Overall,k)
            WCTypeRel = t.percentage * t.ResWCTable[j].TotCycleTime \
                    / model.m_Summ1[j] \
                    / model.m_MeanCycleTimes[j]
            if w.NumWS > 0:
                WCTypeRel *= w.NumWS                    # Server related
            WCT = WCTypeRel / DR
            Res["WCTime"] = WCT
            ResNetwork["WCTime"] += Res["WCTime"]
            # Unscheduled maintenance
            if w.MDT == 0.0:
                Res["UnschedMaintTime"] = 0.0
            else:    
                Res["UnschedMaintTime"] = Res["OperatingTime"] * (1.0/w.Rel - 1.0) \
                    / w.MDT / w.Batchsize * w.Maint_U
            ResNetwork["UnschedMaintTime"] += Res["UnschedMaintTime"]        
            # Scheduled maintenance
            Res["SchedMaintTime"] = w.Maint_S / model.hoursPerDay * WCT
            ResNetwork["SchedMaintTime"] += Res["SchedMaintTime"]
            # Waiting room
            if t.ResWCTable[j].QueueLength == 0.0:
                Res["WaitingRoom"] = 0.0
            else:    
                Res["WaitingRoom"] = t.ResWCTable[j].QueueLength / w.ResTable.QueueLength * t.Res_Space * w.ResTable.Quantil
            ResNetwork["WaitingRoom"] += Res["WaitingRoom"]    
            # Sum up by workcenter ...
            ResOverall = ResArray[-1][j]
            # Floor space
            if w.NumWS > 0:
                NumWS = w.NumWS
            else:     
                NumWS = 1
            if w.BufferIsFloorSpace:
                WaitingRoom = Res["WaitingRoom"]
            else:    
                WaitingRoom = 0.0    
            Res["FloorSpace"] = OverallFactor * (w.Res_Floor * NumWS + WaitingRoom)
            ResNetwork["FloorSpace"] += Res["FloorSpace"]
            # Special Area
            Res["SpecialArea"] = OverallFactor * (w.Res_Area * NumWS + WaitingRoom)
            ResNetwork["SpecialArea"] += Res["SpecialArea"]
            ComputeOperator(Res,ResNetwork,NumOperatorsFactor)
            ResOverall["OperatingTime"] += Res["OperatingTime"] * OverallFactor
            ResOverall["HandlingTime"] += Res["HandlingTime"] * OverallFactor
            ResOverall["InspectionTime"] += Res["InspectionTime"] * OverallFactor
            ResOverall["TransportTime"] += Res["TransportTime"] * OverallFactor
            ResOverall["UnschedMaintTime"] += Res["UnschedMaintTime"] * OverallFactor
            ResOverall["SchedMaintTime"] += Res["SchedMaintTime"] * OverallFactor
            ResOverall["WaitingRoom"] += Res["WaitingRoom"]
            ResOverall["FloorSpace"] += Res["FloorSpace"]        
            ResOverall["SpecialArea"] += Res["SpecialArea"]                 
            ResOverall["WCTime"] += Res["WCTime"] * OverallFactor               
        # Sum up for entire line ...    
        ResOverall = ResArray[-1][-1]
        ResOverall["OperatingTime"] += ResNetwork["OperatingTime"] * OverallFactor
        ResOverall["HandlingTime"] += ResNetwork["HandlingTime"] * OverallFactor
        ResOverall["InspectionTime"] += ResNetwork["InspectionTime"] * OverallFactor
        ResOverall["TransportTime"] += ResNetwork["TransportTime"] * OverallFactor
        ResOverall["UnschedMaintTime"] += ResNetwork["UnschedMaintTime"] * OverallFactor
        ResOverall["SchedMaintTime"] += ResNetwork["SchedMaintTime"] * OverallFactor
        ResOverall["WaitingRoom"] += ResNetwork["WaitingRoom"]        
        ResOverall["FloorSpace"] += ResNetwork["FloorSpace"]        
        ResOverall["SpecialArea"] += ResNetwork["SpecialArea"]        
        ResOverall["WCTime"] += ResNetwork["WCTime"] * OverallFactor        
        ResArray[i][0]["OverallFactor"] = OverallFactor
    # Compute Resources for entire line
    DR = model.ResTable.OAR * model.ResTable.Yield
    NumOperatorsFactor = DR / model.OperatorAV            
    ResNetwork = ResArray[-1][-1]
    for j, w in enumerate(model.workcenter):    
        if not w.Used:
            continue
        ResOverall = ResArray[-1][j]
        ComputeOperator(ResOverall,ResNetwork,NumOperatorsFactor)
    return ResArray

def ComputeCostType(model,idxType,Results):
    t = model.prodtypes[idxType]
    DR = t.ResTable.OAR * t.ResTable.Yield
    Yield = t.SFactorTabNew[-1]
    HC = model.HeadCount * TimeScale(model.unitOfTime,TIMEHOUR) / model.OperatorAV
    # Hours per year
    TimeScaleYear = 1.0 / (WEEKSPERYEAR * model.daysPerWeek * 24  \
                 * TimeScale(TIMEHOUR,model.unitOfTime))
    for i, o in enumerate(t.operations):
        WCNo = o.WCNumber
        # Compute relative frequency
        eim =  t.SFactorTabNew[i] / Yield
        # Compute scrapping probability and Transport cost  
        # for every successor in the successor list 
        ScrapProb = 1.0
        TransCost = 0.0
        for s in t.getSucc(i+1):
            ScrapProb -= s.Prob
            TransCost += s.Prob * s.TransitionCost
        # Materials / Supplies
        Results[WCNo-1][CostIndices["CostMatAndSupp"]] += eim * o.Cost_Mat
        # Scrapping costs
        Results[WCNo-1][CostIndices["CostLoss"]] += eim * o.Cost_Scrap * ScrapProb
        # Transport costs
        Results[WCNo-1][CostIndices["CostTransport"]] += eim * TransCost

    CostNetWork = Results[-1]
    for i, w in enumerate(model.workcenter):    
        Resources = model.ResArray[idxType][i]
        # Operating expense
        Results[i][CostIndices["CostOpExpense"]] = Resources["OperatingTime"] * w.Cost_Op
        CostNetWork[CostIndices["CostOpExpense"]] += Results[i][CostIndices["CostOpExpense"]]
        # Inventories
        ResTable = t.ResWCTable[i]
        Results[i][CostIndices["CostInventories"]] = ResTable.LeadTime * t.Cost_Inventory
        CostNetWork[CostIndices["CostInventories"]] += Results[i][CostIndices["CostInventories"]]        
        # Handling cost
        Results[i][CostIndices["CostHandling"]] = Resources["HandlingTime"] * HC
        CostNetWork[CostIndices["CostHandling"]] += Results[i][CostIndices["CostHandling"]]                
        # Inspection cost
        Results[i][CostIndices["CostInspection"]] = Resources["InspectionTime"] * HC
        CostNetWork[CostIndices["CostInspection"]] += Results[i][CostIndices["CostInspection"]]                        
        # Unscheduled maintenance
        Results[i][CostIndices["CostUnSchedMaint"]] = Resources["UnschedMaintTime"] * HC
        CostNetWork[CostIndices["CostUnSchedMaint"]] += Results[i][CostIndices["CostUnSchedMaint"]]     
        # Transport / net
        # Results[i][CostIndices["CostTransport"]] = Resources["TransportTime"] * HC            # Already computed above, based on Transistion Cost !
        CostNetWork[CostIndices["CostTransport"]] += Results[i][CostIndices["CostTransport"]]     
        # Materials and Cost of loss
        CostNetWork[CostIndices["CostMatAndSupp"]] += Results[i][CostIndices["CostMatAndSupp"]]                                       
        CostNetWork[CostIndices["CostLoss"]] += Results[i][CostIndices["CostLoss"]]                                       
        # Scheduled maintenance
        Results[i][CostIndices["CostSchedMaint"]] = Resources["SchedMaintTime"] * HC
        CostNetWork[CostIndices["CostSchedMaint"]] += Results[i][CostIndices["CostSchedMaint"]]             
        # Depreciation
        Results[i][CostIndices["CostDepreciation"]] = Resources["WCTime"] * TimeScaleYear * w.Cost_Depr
        CostNetWork[CostIndices["CostDepreciation"]] += Results[i][CostIndices["CostDepreciation"]]   
        # Service / materials          
        Results[i][CostIndices["CostServAndMat"]] = Resources["WCTime"] * TimeScaleYear * w.Cost_SM
        CostNetWork[CostIndices["CostServAndMat"]] += Results[i][CostIndices["CostServAndMat"]]   
        # Constant floor space
        if w.BufferIsFloorSpace:
            WaitingRoom = Resources["WaitingRoom"]/DR
        else:    
            WaitingRoom = 0.0        
        Results[i][CostIndices["CostFloorSpace"]] = (w.Res_Floor * Resources["WCTime"] + WaitingRoom) * TimeScaleYear * model.FloorSpace
        CostNetWork[CostIndices["CostFloorSpace"]] += Results[i][CostIndices["CostFloorSpace"]]   
        # Constant special area
        Results[i][CostIndices["CostSpecArea"]] = (w.Res_Area * Resources["WCTime"] + WaitingRoom) * TimeScaleYear * model.SpecialArea
        CostNetWork[CostIndices["CostSpecArea"]] += Results[i][CostIndices["CostSpecArea"]]   
        # Income
        Results[i][CostIndices["CostIncome"]] = t.Income * ConvertAR(model,t.ResWCTable[i].OverallLoad,"IMODE_DR","IMODE_SHIP")
        CostNetWork[CostIndices["CostIncome"]] += Results[i][CostIndices["CostIncome"]]           
    # Now add totals
    for i, w in enumerate(model.workcenter):       
        # Total output related costs per WC
        for j in range(CostIndices["CostOpExpense"],CostIndices["CostTransport"]+1):
            Results[i][CostIndices["CostOutOverall"]] += Results[i][j]              
        CostNetWork[CostIndices["CostOutOverall"]] += Results[i][CostIndices["CostOutOverall"]]   
        # Total time related costs per WC
        for j in range(CostIndices["CostDepreciation"],CostIndices["CostSpecArea"]+1):
            Results[i][CostIndices["CostTimeOverall"]] += Results[i][j]
        CostNetWork[CostIndices["CostTimeOverall"]] += Results[i][CostIndices["CostTimeOverall"]]   
        # Total manufacturing cost
        Results[i][CostIndices["CostManFacPerPart"]] = Results[i][CostIndices["CostOutOverall"]] + Results[i][CostIndices["CostTimeOverall"]]
        CostNetWork[CostIndices["CostManFacPerPart"]] += Results[i][CostIndices["CostManFacPerPart"]]
        Results[i][CostIndices["CostManFacPerTU"]] = Results[i][CostIndices["CostManFacPerPart"]] * DR
        CostNetWork[CostIndices["CostManFacPerTU"]] += Results[i][CostIndices["CostManFacPerTU"]]
        CostNetWork[CostIndices["CostManFacPerDay"]] += Results[i][CostIndices["CostManFacPerTU"]] * TimeFactors[model.unitOfTime]
    CostNetWork[CostIndices["CostIncome"]] = t.Income * ConvertAR(model,DR,"IMODE_DR","IMODE_SHIP")
    Overhead = model.Overhead * t.percentage / DR * TimeScaleYear
    CostNetWork[CostIndices["CostProfitPerPart"]] = t.Income - CostNetWork[CostIndices["CostManFacPerPart"]] - Overhead
    CostNetWork[CostIndices["CostProfitPerTU"]] = CostNetWork[CostIndices["CostProfitPerPart"]] * DR
    CostNetWork[CostIndices["CostProfitPerDay"]] = CostNetWork[CostIndices["CostProfitPerTU"]] * TimeFactors[model.unitOfTime]

def ComputeCostAll(model):
    def addCosts(j,OverallFactor,CostOverall):
        for k in range(0,CostIndices["CostProfitPerPart"]+1):
            CostOverall[j][k] += OverallFactor * CostType[j][k]
        # Add totals    
        for k in range(CostIndices["CostIncome"],CostIndices["CostManFacPerDay"]+1):
            CostOverall[j][k] += CostType[j][k]


    if not model.bComputed:
        initialComputations(model)
    t = len(model.prodtypes)+1
    w = len(model.workcenter)+1
    c = len(CostIndices)   
    CostMatrixArray = np.zeros((t,w,c))
    CostOverall = CostMatrixArray[-1]
    for i, t in enumerate(model.prodtypes):
        if t.percentage == 0.0:
            continue
        CostType = CostMatrixArray[i]
        ComputeCostType(model,i,CostType)
        OverallFactor = model.ResArray[i][0]["OverallFactor"]
        for j, w in enumerate(model.workcenter):
            addCosts(j,OverallFactor,CostOverall)       
        j += 1    
        addCosts(j,OverallFactor,CostOverall)
    return CostMatrixArray         