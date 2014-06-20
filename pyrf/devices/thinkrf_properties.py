from pyrf.units import M
from pyrf.vrt import I_ONLY, IQ


def wsa_properties(device_id):
    """
    Return a WSA*Properties class for device_id passed
    """
    if device_id.startswith('ThinkRF,WSA4000'):
        return WSA4000Properties
    elif device_id.startswith('ThinkRF,WSA5000-220 v2'):
        return WSA5000_220_v2Properties
    elif device_id.startswith('ThinkRF,WSA5000-208 v2'):
        return WSA5000_208_v2Properties
    elif device_id.startswith('ThinkRF,WSA5000-208'):
        return WSA5000_208Properties
    elif device_id.startswith('ThinkRF,WSA5000-108'):
        return WSA5000_108Properties
    else:
        return WSA5000_220Properties


class WSA4000Properties(object):
    model = 'WSA4000'

    ADC_DYNAMIC_RANGE = 72.5
    NOISEFLOOR_CALIBRATION = -10
    CAPTURE_FREQ_RANGES = [(0, 40*M, I_ONLY), (90*M, 10000*M, IQ)]
    SWEEP_FREQ_RANGE = (90*M, 10000*M)

    RFE_MODES = ('ZIF',)

    DEFAULT_SAMPLE_TYPE = {'ZIF': IQ} # almost true, see CAPTURE_FREQ_RANGES
    FULL_BW = {'ZIF': 125*M}
    USABLE_BW = {'ZIF': 90*M}
    MIN_TUNABLE = {'ZIF': 90*M}
    MAX_TUNABLE = {'ZIF': 10000*M}
    MIN_DECIMATION = {'ZIF': 4}
    MAX_DECIMATION = {'ZIF': 1023}
    DECIMATED_USABLE = 0.5
    PASS_BAND_CENTER = {'ZIF': 0.5}
    DC_OFFSET_BW = 240000 # XXX: an educated guess
    TUNING_RESOLUTION = 100000
    FSHIFT_AVAILABLE = {'ZIF': True}
    SWEEP_SETTINGS = ['fstart', 'fstop', 'fstep', 'fshift', 'decimation',
        'antenna', 'gain', 'ifgain', 'spp', 'ppb', 'dwell_s', 'dwell_us',
        'trigtype', 'level_fstart', 'level_fstop', 'level_amplitude']

    SPECA_DEFAULTS = {
        'mode': 'ZIF',
        'center': 2450 * M,
        'rbw': 122070,
        'span': 125 * M,
        'decimation': 1,
        'fshift': 0,
        'device_settings': {
            'antenna': 1,
            'ifgain': 0,
            'gain': 'low',
            },
        'device_class': 'thinkrf.WSA',
        'device_identifier': 'unknown',
        }


class WSA5000_220Properties(object):
    model = 'WSA5000-220'
    MINIMUM_FW_VERSION = '3.2.0-rc1'

    ADC_DYNAMIC_RANGE = 72.5
    NOISEFLOOR_CALIBRATION = -10
    CAPTURE_FREQ_RANGES = [(50*M, 20000*M, IQ)]
    SWEEP_FREQ_RANGE = (100*M, 20000*M)
    RFE_ATTENUATION = 20
    RFE_MODES = ('ZIF', 'SH', 'SHN', 'HDR', 'IQIN', 'DD')
    DEFAULT_SAMPLE_TYPE = {
        'ZIF': IQ,
        'SH': I_ONLY,
        'SHN': I_ONLY,
        'HDR': I_ONLY,
        'IQIN': IQ,
        'DD': I_ONLY,
        }
    FULL_BW = {
        'ZIF': 125 * M,
        'HDR': 0.16276 * M,
        'SH': 62.5 * M,
        'SHN': 62.5 * M,
        'IQIN': 125 * M,
        'DD': 62.5 * M,
        }
    USABLE_BW = {
        'ZIF': 100 * M,
        'HDR': 0.1 * M,
        'SH': 40 * M,
        'SHN': 10 * M,
        'IQIN': 100 * M,
        'DD': 62.5 * M,
        }
    MIN_TUNABLE = {
        'ZIF': 50 * M,
        'HDR': 50 * M,
        'SH': 50 * M,
        'SHN': 50 * M,
        'IQIN': 0,
        'DD': 31.24 * M,
        }
    MAX_TUNABLE = {
        'ZIF': 20000 * M,
        'HDR': 20000 * M,
        'SH': 20000 * M,
        'SHN': 20000 * M,
        'IQIN': 0,
        'DD': 31.24 * M,
        }
    MIN_DECIMATION = {
        'ZIF': 4,
        'HDR': None,
        'SH': 4,
        'SHN': 4,
        'IQIN': 4,
        'DD': 4,
        }
    MAX_DECIMATION = {
        'ZIF': 1024,
        'HDR': None,
        'SH': 4,
        'SHN': 4,
        'IQIN': 1024,
        'DD': 1024,
        }
    DECIMATED_USABLE = 0.80
    PASS_BAND_CENTER = {
        'ZIF': 0.5,
        'HDR': 0.6,
        'SH': 0.56,
        'SHN': 0.45,
        'IQIN': 0.5,
        'DD': 0.5,
        }
    DC_OFFSET_BW = 240000 # XXX: an educated guess
    TUNING_RESOLUTION = 100000
    FSHIFT_AVAILABLE = {
        'ZIF': True,
        'HDR': False,
        'SH': True,
        'SHN': True,
        'IQIN': True,
        'DD': True,
        }
    MAX_FSHIFT = {'ZIF': 62.5*M}
    SWEEP_SETTINGS = ['rfe_mode', 'fstart', 'fstop', 'fstep', 'fshift',
        'decimation', 'attenuator', 'ifgain', 'spp', 'ppb',
        'dwell_s', 'dwell_us',
        'trigtype', 'level_fstart', 'level_fstop', 'level_amplitude']

    LEVEL_TRIGGER_RFE_MODES = ['SH', 'SHN', 'ZIF']

    SPECA_DEFAULTS = {
        'mode': 'ZIF',
        'center': 2450 * M,
        'rbw': 122070,
        'span': 125 * M,
        'decimation': 1,
        'fshift': 0,
        'device_settings': {
            'attenuator': True,
            'iq_output_path': 'DIGITIZER',
            'pll_reference': 'INT',
            'trigger': {'type': 'NONE',
                        'fstart': 2440 * M,
                        'fstop': 2460 * M,
                        'amplitude': -110},
            },
        'device_class': 'thinkrf.WSA',
        'device_identifier': 'unknown',
        }


class WSA5000_220_v2Properties(WSA5000_220Properties):
    model = 'WSA5000-220 v2'
    # v2 -> hardware revision without SHN mode
    RFE_MODES = ('ZIF', 'SH', 'HDR', 'IQIN', 'DD')


class WSA5000_208Properties(WSA5000_220Properties):
    model = 'WSA5000-208'
    # 208 -> limited to 8GHz

    MAX_TUNABLE = dict((mode, min(8000*M, f))
        for mode, f in WSA5000_220Properties.MAX_TUNABLE.iteritems())

class WSA5000_108Properties(WSA5000_208Properties):
    model = 'WSA5000-108'
    # 108 -> limited to SHN, HDR, and DD mode
    RFE_MODES = ('SHN', 'HDR', 'DD')

class WSA5000_208_v2Properties(WSA5000_220_v2Properties, WSA5000_208Properties):
    model = 'WSA5000-208 v2'

