import wx
import numpy
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

def plot_sample1(current_panel):
        scores = [89, 98, 70, 80, 60, 78, 85, 90]
        sum = 0
        for s in scores:
            sum += s
        average = sum / len(scores)
 
        t_score = numpy.arange(1, len(scores) + 1, 1)
        s_score = numpy.array(scores)
 
        figure_score = Figure()
        figure_score.set_figheight(3.6)
        figure_score.set_figwidth(7.8)
        axes_score = figure_score.add_subplot(111)
 
        axes_score.plot(t_score, s_score, 'ro', t_score, s_score, 'k')
        axes_score.axhline(y=average, color='r')
        axes_score.set_title(u'My Scores')
        axes_score.grid(True)
        axes_score.set_xlabel('T')
        axes_score.set_ylabel('score')
        FigureCanvas(current_panel, -1, figure_score)
    
def plot_sample2(current_panel):
        dc = wx.PaintDC(current_panel)

        brush = wx.Brush('white')
        dc.SetBackground(brush)
        dc.Clear()

        # Line
        pen = wx.Pen(wx.Colour(0, 0, 255), 1, wx.SOLID)
        dc.SetPen(pen)
        dc.DrawLine(10, 10, 390, 190)
 
        # Text
        font = wx.Font(18, wx.ROMAN, wx.ITALIC, wx.NORMAL)
        dc.SetFont(font)
        dc.DrawText("Hello wxPython", 200, 10)
 
        # Shape
        brush_rec = wx.Brush('red')
        dc.SetBrush(brush_rec)
        dc.DrawRectangle(100, 100, 140, 140)
        
        
def plot_sample3(current_panel):
        dc = dc = wx.PaintDC(current_panel)
        verticle_lines = [(i*6,0,i*6,600) for i in range(100)]
        horizontal_lines = [(0,i*6,600,i*6) for i in range(100)]
        dc.DrawLineList(horizontal_lines+verticle_lines)
