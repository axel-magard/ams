#!/usr/bin/env python

import random

import wx
import wx.grid as gridlib

#---------------------------------------------------------------------------


rendererDemoData = [
    ('GridCellStringRenderer\n(the default)', 'this is a text value', gridlib.GridCellStringRenderer, ()),
    ('GridCellNumberRenderer', '12345', gridlib.GridCellNumberRenderer, ()),
    ('GridCellFloatRenderer', '1234.5678', gridlib.GridCellFloatRenderer, (6,2)),
    ('GridCellBoolRenderer', '1', gridlib.GridCellBoolRenderer, ()),
    ]



class EditorsAndRenderersGrid(gridlib.Grid):
    def __init__(self, parent, id):
        gridlib.Grid.__init__(self, parent, id)

        # There is a bug in wxGTK for this method...
        self.AutoSizeColumns(True)
        self.AutoSizeRows(True)

        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGED, self.OnCellChanged)


    # I do this because I don't like the default behaviour of not starting the
    # cell editor on double clicks, but only a second click.
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()

    def OnCellChanged(self, evt):
        self.button_OK.Enable()
        renderer = self.GetCellRenderer(evt.GetRow(),evt.GetCol())
        input = self.GetCellValue(evt.GetRow(),evt.GetCol())
        # We need to handle invalid float values on our own, since gridlib.GridCellFloatEditor doesn't really work.
        val = input
        if renderer.__class__.__name__ == "GridCellFloatRenderer":            
            try: 
                val = float(input)            
            except ValueError:
                self.SetCellTextColour(evt.GetRow(),evt.GetCol(),wx.RED)    
                self.button_OK.Disable()
            else:
                if val < 0.0:    
                    self.SetCellTextColour(evt.GetRow(),evt.GetCol(),wx.RED)    
                    self.button_OK.Disable()
                else:                        
                    self.SetCellTextColour(evt.GetRow(),evt.GetCol(),wx.BLACK)                    
        elif renderer.__class__.__name__ == "GridCellNumberRenderer":                
            val = int(input)            
            if val < 0.0:    
                self.SetCellTextColour(evt.GetRow(),evt.GetCol(),wx.RED)    
                self.button_OK.Disable()
            else:            
                self.SetCellTextColour(evt.GetRow(),evt.GetCol(),wx.BLACK)                    
        else:
            val = input    
        self.table[self.GetColLabelValue(evt.GetCol())][int(evt.GetRow())] = val


#---------------------------------------------------------------------------

class TestFrame(wx.Frame):
    def __init__(self, parent, log):
        wx.Frame.__init__(self, parent, -1, "Editors and Renderers Demo", size=(640,480))
        grid = EditorsAndRenderersGrid(self, log)



#---------------------------------------------------------------------------

