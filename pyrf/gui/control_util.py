from PySide import QtCore
import util
import pyqtgraph as pg
from pyrf.config import TriggerSettings
import gui_config as gui_state
import constants
from pyrf.util import read_data_and_context

def _center_plot_view(layout):
    """
    move the view to the center of the current FFT displayed
    """
    layout._plot.center_view(layout.plot_state.center_freq, layout.plot_state.bandwidth)
    
def _select_center_freq(layout):
    """
    select the center freq for arrow control
    """
    layout.plot_state.freq_sel = 'CENT'
    util.select_center(layout)
    
def _select_bw(layout):
    """
    select the bw for arrow control
    """
    layout.plot_state.freq_sel = 'BW'
    util.select_bw(layout)

def _select_fstart(layout):
    """
    select the fstart for arrow control
    """
    layout.plot_state.freq_sel = 'FSTART'
    util.select_fstart(layout)
    
def _select_fstop(layout):
    """
    select the fstop for arrow control
    """
    layout.plot_state.freq_sel = 'FSTOP'
    util.select_fstop(layout)
    
def _up_arrow_key(layout):
    """
    increase the step size of the +/- buttons
    """
    step = layout._fstep_box.currentIndex() + 1
    max_step = layout._fstep_box.count()
    if step > max_step - 1:
        step = max_step -1
    elif step < 0:
        step = 0
        layout._fstep_box.setCurrentIndex(step)
    layout._fstep_box.setCurrentIndex(step)

def _down_arrow_key(layout):
    """
    decrease the step size of the +/- buttons
    """
    step = layout._fstep_box.currentIndex() - 1
    max_step = layout._fstep_box.count()
    if step > max_step - 1:
        step = max_step -1
    elif step < 0:
        step = 0
        layout._fstep_box.setCurrentIndex(step)
    layout._fstep_box.setCurrentIndex(step)
       
def _right_arrow_key(layout):
    """
    handle arrow key right action
    """

    if layout.plot_state.enable_plot:
        layout._freq_plus.click()
        layout.plot_state.mhold_fft = None

def _left_arrow_key(layout):
    """
    handle left arrow key action
    """
    if layout.plot_state.enable_plot:
        layout._freq_minus.click()
        layout.plot_state.mhold_fft = None
        
def _trace_tab_change(layout):
    """
    change the selected trace
    """
    trace = layout._plot.traces[layout._trace_tab.currentIndex()]
    layout.plot_state.trace_sel = trace.name
    if trace.write:
        layout._write.click()
    elif trace.mhold:
        layout._max_hold.click()
    elif trace.blank:
        layout._blank.click()
    
    if layout._plot.traces[layout._trace_tab.currentIndex()].store:
        state =  QtCore.Qt.CheckState.Checked
    else:
        state =  QtCore.Qt.CheckState.Unchecked
    layout._store.setCheckState(state) 
    
def _max_hold(layout):
    """
    disable/enable max hold on a trace
    """
    layout._plot.traces[layout._trace_tab.currentIndex()].write = False
    layout._plot.traces[layout._trace_tab.currentIndex()].mhold = True
    layout._plot.traces[layout._trace_tab.currentIndex()].blank = False
            
def _trace_write(layout):
    """
    disable/enable running FFT mode the selected trace
    """        
    layout._plot.traces[layout._trace_tab.currentIndex()].write = True
    layout._plot.traces[layout._trace_tab.currentIndex()].mhold = False
    layout._plot.traces[layout._trace_tab.currentIndex()].blank = False

def _blank_trace(layout):
    """
    disable/enable the selected trace
    """
    layout._plot.traces[layout._trace_tab.currentIndex()].write = False
    layout._plot.traces[layout._trace_tab.currentIndex()].mhold = False
    layout._plot.traces[layout._trace_tab.currentIndex()].blank = True
    layout._plot.traces[layout._trace_tab.currentIndex()].curve.clear()
    layout._plot.traces[layout._trace_tab.currentIndex()].data = None
            
def _store_trace(layout):
    """
    store the current trace's data
    """
    if layout._store.checkState() is QtCore.Qt.CheckState.Checked:
        layout._plot.traces[layout._trace_tab.currentIndex()].store = True
    else:
        layout._plot.traces[layout._trace_tab.currentIndex()].store = False
        
def _marker_control(layout):
    """
    disable/enable marker
    """
    # if marker is on and selected, turn off
    if layout.plot_state.marker_sel:
        layout.plot_state.disable_marker(layout)

            
    # if marker is on and not selected, select
    elif not layout.plot_state.marker_sel and layout.plot_state.marker: 
        layout.plot_state.enable_marker(layout)

    # if marker is off, turn on and select
    elif not layout.plot_state.marker:
        layout.plot_state.enable_marker(layout)

def _delta_control(layout):
    """
    disable/enable delta (marker 2)
    """

    # if delta is on and selected, turn off
    if layout.plot_state.delta_sel:
        layout.plot_state.disable_delta(layout)
    
    # if delta is on and not selected, select
    elif not layout.plot_state.delta_sel and layout.plot_state.delta: 
        layout.plot_state.enable_delta(layout)

    # if delta is off, turn on and select
    elif not layout.plot_state.delta:
        layout.plot_state.enable_delta(layout)   

def _find_peak(layout):
    """
    move the selected marker to the maximum point of the spectrum
    """
    if not layout.plot_state.marker and not layout.plot_state.delta:
        _marker_control(layout)

    if layout.plot_state.mhold:
       peak = util.find_max_index(layout.plot_state.mhold_fft) 
    else:
        peak = util.find_max_index(layout.pow_data)
    
    if layout.plot_state.marker_sel:
        layout.update_marker()
        layout.plot_state.marker_ind = peak
    elif layout.plot_state.delta_sel:
        layout.update_delta()
        layout.plot_state.delta_ind = peak
    layout.update_diff()

def _trigger_control(layout):
    """
    disable/enable triggers in the layout plot
    """

    if layout.plot_state.trig:
        layout.plot_state.disable_trig(layout)
           
    else:
        layout.plot_state.enable_trig(layout)
        _select_center_freq(layout)
        
hotkey_dict = {'1': _select_fstart,
                '2': _select_center_freq,
                '3': _select_bw,
                '4': _select_fstop,
                'UP KEY': _up_arrow_key, 
                'DOWN KEY': _down_arrow_key,
                'RIGHT KEY': _right_arrow_key,
                'LEFT KEY': _left_arrow_key,
                'C': _center_plot_view,
                'K': _delta_control,
                'M': _marker_control,
                'P': _find_peak,
                'T': _trigger_control
                } 
                
arrow_dict = {'32': 'SPACE', 
                '16777235': 'UP KEY', 
                '16777237': 'DOWN KEY',
                '16777234': 'LEFT KEY', 
                '16777236': 'RIGHT KEY'}


