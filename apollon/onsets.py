#!/usr/bin/python
# -*- coding: utf-8 -*-


import matplotlib.pyplot as _plt
import numpy as _np
import scipy.signal as _sps
from typing import Dict, Tuple

from apollon import fractal as _fractal
from apollon import segment as _segment
from apollon import tools as _tools
from . signal.spectral import stft as _stft
from . signal.tools import trim_spectrogram as _trim_spectrogram
from . types import Array as _Array

class EnrtopyOnsetDetector:

    __slots__ = ['audio_file_name', 'bins', 'idx', 'm', 'odf', 'order', 'tau',
                 'time_stamp', 'window_length', 'window_hop_size']

    def __init__(self):
        pass

    def detect(self, sig, tau=10, m=3, bins=50, wlen=16, whs=8, order=22):
        """Detect note onsets in (percussive) music as local maxima of information
        entropy.

        Params:
            sig      (array-like) Audio signal.
            tau      (int) Phase-space: delay parameter in samples.
            m        (int) Phase-space: number of dimensions.
            bins     (int) Phase-space: number of boxes per axis.
            wlen     (int) Segmentation: window length in ms.
            whs      (int) Segmentation: window displacement in ms.
            order    (int) Peak-picling: Order of filter in samples.
        """
        # meta
        self.audio_file_name = str(sig.file)
        self.bins = bins
        self.m = m
        self.order = order
        self.tau = tau
        self.time_stamp = _tools.time_stamp()
        self.window_hop_size = whs
        self.window_length = wlen


        # segment audio
        chunks = _segment.by_ms_with_hop(sig, self.window_length,
                                         self.window_hop_size)

        # calculate entropy for each chunk
        H = _np.empty(len(chunks))
        for i, ch in enumerate(chunks):
            em = _fractal.embedding(ch, self.tau, m=self.m, mode='wrap')
            H[i] = _fractal.pps_entropy(em, self.bins)

        # Take imaginary part of the Hilbert transform of the enropy
        self.odf = _np.absolute(_sps.hilbert(H).imag)

        # pick the peaks
        peaks, = _sps.argrelmax(self.odf, order=self.order)

        # calculate onset position to be in the middle of chunks
        self.idx = _np.array( [(i+j)//2
                              for (i, j) in chunks.get_limits()[peaks]])



class FluxOnsetDetector:
    """Onset detection based on spectral flux."""

    __slots__ = ('odf', 'peaks', 'index', 'times')

    def __init__(self, inp: _Array, fps: int, n_perseg: int = 2048, window: str = 'hamming',
                 hop_size: int = 441, smooth: int = 10):

        self.odf, self.peaks = self._detect(inp, fps, window, n_perseg, hop_size)
        self.index = self.peaks * hop_size
        self.times = self.index / fps

    def _detect(self, inp: _Array, fps: int, window: str, n_perseg: int, hop_size: int,
                smooth: int = None):
        """Detects onsets based on spectral flux."""

        spctrgrm = _stft(inp, fps, window, n_perseg, hop_size)
        sb_flux, sb_frqs = _trim_spectrogram(spctrgrm.flux(subband=True), spctrgrm.frqs, 80, 10000)
        odf = sb_flux.sum(axis=0)

        if smooth:
            wh = _sps.get_window('boxcar', smooth)
            odf = _np.convolve(self.odf, wh, mode='same')

        peaks = peak_picking(odf)

        return odf, peaks


def peak_picking(odf, post_window=3, pre_window=3, alpha=.1, delta=.1):
    """Pick local maxima from a numerical time series.

    Pick local maxima from the onset detection function `odf`, which is assumed
    to be an one-dimensional array. Typically, `odf` is the Spectral Flux per
    time step.

    Params:
        odf         (np.ndarray)    Onset detection function,
                                    e.g., Spectral Flux.
        post_window (int)           Window lenght to consider after now.
        pre_window  (int)           Window lenght to consider before now.
        alpha       (float)         Smoothing factor. Must be in ]0, 1[.
        delta       (float)         Difference to the mean.

    Return:
        (np.ndarray)    Peak indices.
    """
    g = [0]
    out = []

    for n, val in enumerate(odf):

        # set local window
        idx = _np.arange(n-pre_window, n+post_window+1, 1)
        window = _np.take(odf, idx, mode='clip')

        cond1 = _np.all(val >= window)
        cond2 = val >= (_np.mean(window) + delta)

        foo = max(val, alpha*g[n] + (1-alpha)*val)
        g.append(foo)
        cond3 = val >= foo

        if cond1 and cond2 and cond3:
            out.append(n)

    return _np.array(out)


def evaluate_onsets(targets:   Dict[str, _np.ndarray],
                    estimates: Dict[str, _np.ndarray]) -> Tuple[float, float,
                                                                float]:
    """Evaluate the performance of an onset detection.

    Params:
        targets    (dict) of ground truth onset times, with
                            keys   == file names, and
                            values == target onset times in ms.

        estimates  (dict) of estimated onsets times, with
                            keys   == file names, and
                            values == estimated onset times in ms.

    Return:
        (p, r, f)    Tupel of precison, recall, f-measure
    """

    out = []
    for name, tvals in targets.items():
        od_eval = _me.onset.evaluate(tvals, estimates[name])
        out.append([i for i in od_eval.values()])

    return _np.array(out)
