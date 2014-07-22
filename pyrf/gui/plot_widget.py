import platform

import pyqtgraph as pg
import numpy as np
from PySide import QtCore

from pyrf.gui import colors
from pyrf.gui import labels
from pyrf.gui.trace_controls import PLOT_TOP, PLOT_BOTTOM
from pyrf.gui.waterfall_widget import (WaterfallModel,
    ThreadedWaterfallPlotWidget)

USE_WATERFALL = True #platform.system() != 'Windows'

PLOT_YMIN = -160
PLOT_YMAX = 20

IQ_PLOT_YMIN = -1
IQ_PLOT_YMAX = 1

IQ_PLOT_XMIN = -1
IQ_PLOT_XMAX = 1

AXIS_OFFSET = 7
class Trace(object):
    """
    Class to represent a trace in the plot
    """
    
    def __init__(self,plot_area, trace_name, trace_color, blank = False, write = False):
        self.name = trace_name
        self.max_hold = False
        self.min_hold = False
        self.blank = blank
        self.write = write
        self.store = False
        self.data = None
        self.raw_packet = None
        self.freq_range = None
        self.color = trace_color
        self.edge_color = trace_color + (40,)
        self.alternate_color = (
            max(0, trace_color[0] - 60),
            max(0, trace_color[1] - 60),
            min(255, trace_color[2] + 60),)
        self.curves = []
        self.plot_area = plot_area

    def clear(self):
        for c in self.curves:
            self.plot_area.window.removeItem(c)
        self.curves = []

    def update_curve(self, xdata, ydata, usable_bins, sweep_segments):

        if self.store or self.blank:
            return

        self.freq_range = xdata

        if self.max_hold:
            if (self.data == None or len(self.data) != len(ydata)):
                self.data = ydata
            self.data = np.maximum(self.data,ydata)

        elif self.min_hold:
            if (self.data == None or len(self.data) != len(ydata)):
                self.data = ydata
            self.data = np.minimum(self.data,ydata)

        elif self.write:
            self.data = ydata

        self.clear()
        if usable_bins:
            # plot usable and unusable curves
            i = 0
            for start_bin, run_length in usable_bins:
                if start_bin > i:
                    c = self.plot_area.window.plot(x=xdata[i:start_bin+1],
                        y=self.data[i:start_bin+1], pen=self.edge_color)
                    self.curves.append(c)
                    i = start_bin
                if run_length:
                    c = self.plot_area.window.plot(x=xdata[i:i+run_length],
                        y=self.data[i:i+run_length], pen=self.color)
                    self.curves.append(c)
                    i = i + run_length - 1
            if i < len(xdata):
                c = self.plot_area.window.plot(x=xdata[i:], y=self.data[i:],
                    pen=self.edge_color)
                self.curves.append(c)
        else:
            odd = True
            i = 0
            for run in sweep_segments:
                c = self.plot_area.window.plot(x=xdata[i:i + run],
                    y=self.data[i:i + run],
                    pen=self.color if odd else self.alternate_color)
                self.curves.append(c)
                i = i + run
                odd = not odd

class Marker(object):
    """
    Class to represent a marker on the plot
    """
    def __init__(self,plot_area, marker_name):

        self.name = marker_name
        self.marker_plot = pg.ScatterPlotItem()
        self.enabled = False
        self.selected = False
        self.data_index = None
        
        # index of trace associated with marker
        self.trace_index = 0
        
    def enable(self, plot):
        
        self.enabled = True
        plot.window.addItem(self.marker_plot)     
    
    def disable(self, plot):
        
        self.enabled = False
        plot.window.removeItem(self.marker_plot)
        self.data_index = None
        self.trace_index = 0

    def update_pos(self, xdata, ydata):
    
        self.marker_plot.clear()
        if self.data_index  == None:
           self.data_index = len(ydata) / 2 
   
        if self.data_index < 0:
           self.data_index = 0
            
        elif self.data_index >= len(ydata):
            self.data_index = len(ydata) - 1

        xpos = xdata[self.data_index]
        
        ypos = ydata[self.data_index]
        if self.selected:
            color = 'y'
        else: 
            color = 'w'
            
        self.marker_plot.addPoints(x = [xpos], 
                                   y = [ypos], 
                                    symbol = '+', 
                                    size = 20, pen = color, 
                                    brush = color)
class Plot(QtCore.QObject):
    """
    Class to hold plot widget, as well as all the plot items (curves, marker_arrows,etc)
    """
    user_xrange_change = QtCore.Signal(float, float)

    def __init__(self, controller, layout):
        super(Plot, self).__init__()

        self.controller = controller
        controller.state_change.connect(self.state_changed)
        # initialize main fft window
        self.window = pg.PlotWidget(name = 'pyrf_plot')

        def widget_range_changed(widget, ranges):
            if not hasattr(ranges, '__getitem__'):
                return  # we're not intereted in QRectF updates
            self.user_xrange_change.emit(ranges[0][0], ranges[0][1])
        self.window.sigRangeChanged.connect(widget_range_changed)

        self.view_box = self.window.plotItem.getViewBox()
        self.view_box.setMouseEnabled(x = True, y = False)

        # initialize the x-axis of the plot
        self.window.setLabel('bottom', text = 'Frequency', units = 'Hz', unitPrefix=None)

        # initialize the y-axis of the plot
        self.window.setYRange(PLOT_BOTTOM, PLOT_TOP)
        self.window.setLabel('left', text = 'Power', units = 'dBm')

        # initialize fft curve
        self.fft_curve = self.window.plot(pen = colors.TEAL_NUM)

        # initialize trigger lines
        self.amptrig_line = pg.InfiniteLine(pos = -100, angle = 0, movable = True)
        self.freqtrig_lines = pg.LinearRegionItem()

        self.grid(True)

        # IQ constellation window
        self.const_window = pg.PlotWidget(name='const_plot')
        self.const_plot = pg.ScatterPlotItem(pen = 'y')
        self.const_window.addItem(self.const_plot)
        self.const_window.setYRange(IQ_PLOT_YMIN, IQ_PLOT_YMAX)
        self.const_window.setXRange(IQ_PLOT_YMIN, IQ_PLOT_YMAX)  

        # IQ time domain  window
        self.iq_window = pg.PlotWidget(name='const_plot')
        self.iq_window.setYRange(IQ_PLOT_YMIN, IQ_PLOT_YMAX)
        self.i_curve = self.iq_window.plot(pen = 'g')
        self.q_curve = self.iq_window.plot(pen = 'r')

        # add traces
        self.traces = []
        first_trace = labels.TRACES[0]

        for trace_name, trace_color in zip(labels.TRACES, colors.TRACE_COLORS):
            trace = Trace(
                self,
                trace_name,
                trace_color,
                blank=True,
                write=False)
            self.traces.append(trace)
        self.traces[0].blank = False
        self.traces[0].write = True

        self.markers = []
        for marker_name in labels.MARKERS:
            self.markers.append(Marker(self, marker_name))

        self.waterfall_data = WaterfallModel(max_len=600)
        if USE_WATERFALL:
            self.waterfall_window = ThreadedWaterfallPlotWidget(
                self.waterfall_data,
                scale_limits=(PLOT_YMIN, PLOT_YMAX),
                max_frame_rate_fps=30,
                mouse_move_crosshair=False,
                )
        else:
            self.waterfall_window = None

        self.connect_plot_controls()

    def connect_plot_controls(self):
        
        def new_trigger_freq():
            self.controller.apply_device_settings(trigger = {'type': 'LEVEL',
                                                            'fstart': min(self.freqtrig_lines.getRegion()),
                                                            'fstop': max(self.freqtrig_lines.getRegion()),
                                                            'amplitude': self.gui_state.device_settings['trigger']['amplitude']})
        def new_trigger_amp():
            self.controller.apply_device_settings(trigger = {'type': 'LEVEL',
                'fstart': self.gui_state.device_settings['trigger']['fstart'],
                'fstop': self.gui_state.device_settings['trigger']['fstop'],
                'amplitude': self.amptrig_line.value()})
        # update trigger settings when ever a line is changed
        self.freqtrig_lines.sigRegionChangeFinished.connect(new_trigger_freq)
        self.amptrig_line.sigPositionChangeFinished.connect(new_trigger_amp)

    def state_changed(self, state, changed):
        self.gui_state = state
        if 'device_settings.trigger' in changed:
            if 'NONE' in state.device_settings['trigger']['type']:
                self.remove_trigger()
            elif 'LEVEL' in state.device_settings['trigger']['type']:
                self.add_trigger(state.device_settings['trigger']['fstart'],
                                state.device_settings['trigger']['fstop'])

    def add_trigger(self,fstart, fstop):
        self.freqtrig_lines.setRegion([fstart,fstop])
        self.window.addItem(self.amptrig_line)
        self.window.addItem(self.freqtrig_lines)

    def remove_trigger(self):
        self.window.removeItem(self.amptrig_line)
        self.window.removeItem(self.freqtrig_lines)

    def center_view(self, fstart, fstop, min_level=None, ref_level=None):
        b = self.window.blockSignals(True)
        self.window.setXRange(float(fstart), float(fstop), padding=0)
        if min_level is not None:
            self.window.setYRange(min_level + AXIS_OFFSET, ref_level - AXIS_OFFSET)
        self.window.blockSignals(b)

    def grid(self,state):
        self.window.showGrid(state,state)
