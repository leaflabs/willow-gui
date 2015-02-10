import numpy as np

class WillowDataset():
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    Given a ndarray(dtype='uint16') in counts, the constructor converts and stores microvolts
        (self.uv) and a time coordinate in milliseconds (self.ms)
    """

    def __init__(self, data_uint16, sampleRange, filename):
        self.filename = filename
        self.sampleRange = sampleRange
        self.data_uv = (np.array(data_uint16, dtype='float')-2**15)*0.2
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.time_ms = np.arange(sampleRange[0], sampleRange[1]+1)/30.
        self.timeMin = np.min(self.time_ms)
        self.timeMax = np.max(self.time_ms)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.nsamples = len(self.time_ms)

