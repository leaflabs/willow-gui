import numpy as np

class WillowDataset():
    """
    Willow Dataset Container Class
    Common format for passing data between import processes, plot windows, etc.
    Given a ndarray(dtype='uint16') in counts, the constructor converts and stores microvolts
        (self.uv) and a time coordinate in milliseconds (self.ms)
    """

    def __init__(self, data, sampleRange, filename, uvProvided=False):
        self.filename = filename
        self.sampleRange = sampleRange
        if uvProvided:
            self.data_uv = data
        else:
            self.data_uv = (np.array(data, dtype='float')-2**15)*0.2
        self.dataMin = np.min(self.data_uv)
        self.dataMax = np.max(self.data_uv)
        self.time_ms = np.arange(sampleRange[0], sampleRange[1]+1)/30.
        self.timeMin = np.min(self.time_ms)
        self.timeMax = np.max(self.time_ms)
        self.limits = [self.timeMin, self.timeMax, self.dataMin, self.dataMax]
        self.nsamples = len(self.time_ms)

    def getDataSubset(self, c1, c2, t1, t2):
        timeIndices = np.where((t1 <= self.time_ms) & (self.time_ms < t2))
        dataSubset = WillowDataset(self.data_uv[c1:c2, timeIndices],
            sampleRange=[t1*30, t2*30], filename = self.filename, uvProvided=True)
        return dataSubset
