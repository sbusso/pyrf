import logging

from PySide import QtCore

from pyrf.sweep_device import SweepDevice
from pyrf.capture_device import CaptureDevice
from pyrf.gui import gui_config
from pyrf.numpy_util import compute_fft

logger = logging.getLogger(__name__)

class SpecAState(object):
    """
    Representation of the Spec-A + device state for passing
    to UI widgets when changed and for passing to plots when
    captures are received. This object should be treated as
    read-only.

    Parameters after 'other' may be unspecified/set to None to leave
    the value unchanged.

    :param other: existing DeviceState object to copy
    :param mode: Spec-A mode, e.g. 'ZIF' or 'SH sweep'
    :param center: center frequency in Hz
    :param rbw: RBW in Hz
    :param span: span in Hz
    :param decimation: decimation where 1 is no decimation
    :param fshift: fshift in Hz
    :param device_settings: device-specific settings dict
    :param device_class: name of device class, e.g. 'thinkrf.WSA'
    :param device_identifier: device identification string
    :param playback: set to True if this state is from a recording
    """
    def __init__(self, other=None, mode=None, center=None, rbw=None,
            span=None, decimation=None, fshift=None, device_settings=None,
            device_class=None, device_identifier=None, playback=None):

        self.mode = other.mode if mode is None else mode
        self.center = other.center if center is None else center
        self.rbw = other.rbw if rbw is None else rbw
        self.span = other.span if span is None else span
        self.decimation = (other.decimation
            if decimation is None else decimation)
        self.fshift = other.fshift if fshift is None else fshift
        self.device_settings = dict(other.device_settings
            if device_settings is None else device_settings)
        self.device_class = (other.device_class
            if device_class is None else device_class)
        self.device_identifier = (other.device_identifier
            if device_identifier is None else device_identifier)
        self.playback = other.playback if playback is None else playback

    @classmethod
    def from_json_object(cls, j, playback=True):
        """
        Create state from an unserialized JSON dict.

        :param j: dict containing values for all state parameters
            except playback
        :param playback: plaback value to use, default True
        """
        try:
            return cls(None, playback=playback, **j)
        except AttributeError:
            raise TypeError('JSON missing required settings %r' % data)

    def to_json_object(self):
        """
        Return this state as a dict that can be serialized as JSON.

        Playback state is excluded.
        """
        return {
            'mode': self.mode,
            'center': self.center,
            'rbw': self.rbw,
            'span': self.span,
            'decimation': self.decimation,
            'fshift': self.fshift,
            'device_settings': self.device_settings,
            'device_class': self.device_class,
            'device_identifier': self.device_identifier,
            # don't serialize playback info
            }

    def sweeping(self):
        return self.mode.startswith('Sweep ')

    def rfe_mode(self):
        if self.mode.startswith('Sweep '):
            return self.mode[6:]
        return self.mode


class SpecAController(QtCore.QObject):
    """
    The controller for the speca-gui.

    Issues commands to device, stores and broadcasts changes to GUI state.
    """
    _dut = None
    _sweep_device = None
    _capture_device = None
    _plot_state = None
    _state = None

    device_change = QtCore.Signal(object)
    state_change = QtCore.Signal(SpecAState, list)
    capture_receive = QtCore.Signal(SpecAState, float, float, object, object, object, object)

    def set_device(self, dut, playback=False):
        """
        Attach to a new device or playback stream
        """
        if self._dut:
            self._dut.disconnect()
        self._dut = dut
        self._sweep_device = SweepDevice(dut, self.process_sweep)
        self._capture_device = CaptureDevice(dut,
            async_callback=self.process_capture)

        self.device_change.emit(dut)

        self._state = SpecAState.from_json_object(
            dut.properties.SPECA_DEFAULTS, playback)
        self.state_change.emit(
            self._state,
            # assume everything has changed
            list(dut.properties.SPECA_DEFAULTS),
            )

        self.start_capture()

    def read_block(self):
        self._capture_device.capture_time_domain(
            self._state.mode,
            self._state.center,
            self._state.rbw,
            self._state.device_settings)

    def read_sweep(self):
        device_set = dict(self._state.device_settings)
        device_set.pop('iq_output_path')
        device_set.pop('pll_reference')
        self._sweep_device.capture_power_spectrum(
            self._state.center - self._state.span / 2.0,
            self._state.center + self._state.span / 2.0,
            self._state.rbw,
            device_set,
            mode=self._state.rfe_mode())


    def start_capture(self):
        if self._state.sweeping():
            self.read_sweep()
        else:
            self.read_block()


    def process_capture(self, fstart, fstop, data):
        # store usable bins before next call to capture_time_domain
        usable_bins = list(self._capture_device.usable_bins)

        # only read data if WSA digitizer is used
        if self._state.device_settings['iq_output_path'] == 'DIGITIZER':
            if self._state.sweeping():
                self.read_sweep()
                return
            self.read_block()
            if 'reflevel' in data['context_pkt']:
                self._ref_level = data['context_pkt']['reflevel']

            pow_data = compute_fft(self._dut,
                data['data_pkt'], data['context_pkt'], ref=self._ref_level)

            if self._state.device_settings.get('attenuator'):
                pow_data += self._dut.properties.RFE_ATTENUATION

            self.capture_receive.emit(
                self._state,
                fstart,
                fstop,
                data['data_pkt'],
                pow_data,
                usable_bins,
                None)

    def process_sweep(self, fstart, fstop, data):
        sweep_segments = list(self._sweep_device.sweep_segments)
        if not self._state.sweeping():
            self.read_block()
            return
        self.read_sweep()

        if len(data) > 2:
            self.pow_data = data
        self.iq_data = None

        self.capture_receive.emit(
            self._state,
            fstart,
            fstop,
            None,
            self.pow_data,
            None,
            sweep_segments)

    def apply_device_settings(self, **kwargs):
        """
        Apply device-specific settings and trigger a state change event.

        :param kwargs: keyword arguments of SpecAState.device_settings
        """
        device_settings = dict(self._state.device_settings, **kwargs)
        self._state = SpecAState(self._state,
            device_settings=device_settings)
        self.state_change.emit(self._state, ['device_settings'])

        # FIXME find appropriate area for this
        if device_settings['iq_output_path'] == 'DIGITIZER':
            self.start_capture()

    def apply_settings(self, **kwargs):
        """
        Apply state settings and trigger a state change event.

        :param kwargs: keyword arguments of SpecAState attributes
        """
        if self._state is None:
            logger.warn('apply_settings with _state == None: %r' % kwargs)
            return
        self._state = SpecAState(self._state, **kwargs)
        self.state_change.emit(self._state, kwargs.keys())


