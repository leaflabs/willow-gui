from scipy import signal as dsp

# general parameters
NCHAN = 1024
NCHIPS = 32
SAMPLE_RATE = 3e4
MS_PER_SEC = 1000
MICROVOLTS_PER_COUNT = 0.195

# filter parameters
FILT_LOWCUT_HZ = 100.
FILT_HIGHCUT_HZ = 9500.
FILT_ORDER = 5
NYQUIST_RATE = SAMPLE_RATE / 2.
FILTER_B, FILTER_A = dsp.butter(FILT_ORDER,
                        [FILT_LOWCUT_HZ/NYQUIST_RATE, FILT_HIGHCUT_HZ/NYQUIST_RATE],
                        btype='band')

# activity calculation parameters
THRESH_SCALE = -4.5/0.6745 # from JP Kinney
ACTIVITY_SCALE = 100. # arbitrary scaling to get activity approximately normalized to [0,1]
