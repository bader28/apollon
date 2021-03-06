# Licensed under the terms of the BSD-3-Clause license.
# Copyright (C) 2019 Michael Blaß
# michael.blass@uni-hamburg.de

"""apollon/signal/tools.py    (c) Michael Blaß 2016

Signal processing tools

Functions:
    acf                 Normalized autocorrelation.
    acf_pearson         Normalized Pearson acf.
    amp2db              Transform amplitude to dB.
    corr_coef_pearson   Correlation coefficient after Pearson.
    freq2mel            Transform frequency to mel.
    mel2freq            Transform mel to frequency.
    frq2bark            Transform frequency to Bark scale.
    maxamp              Maximal amplitude of signal.
    minamp              Minimal amplitude of signal.
    normalize           Scale data betwee -1.0 and 1.0.
    noise               Generate withe noise.
    sinusoid            Generate sinusoidal signal.
    zero_padding        Append array with zeros.
    trim_spectrogram    Trim spectrogram to a frequency range.
"""


import numpy as _np
from scipy import stats as _stats

from .. types import Array as _Array

def acf(inp_sig):
    """Normalized estimate of the autocorrelation function of `inp_sig`
       by means of cross correlation."""

    N = len(inp_sig)
    norm = inp_sig @ inp_sig

    out = _np.empty(N)
    out[0] = 1
    for m in range(1, N):
        a = inp_sig[:-m]
        b = inp_sig[m:]
        s = a @ b
        if s == 0:
            out[m] = 0
        else:
            out[m] = s / norm

    return out


def acf_pearson(inp_sig):
    """Normalized estimate of the autocorrelation function of `inp_sig`
       by means of pearson correlation coefficient."""

    N = len(inp_sig)
    out = _np.empty(N-1)

    out[0] = 1
    for m in range(1, N-1):

        a = inp_sig[:-m]
        b = inp_sig[m:]

        s = corr_coef_pearson(a, b)

        if s == 0:
            out[m] = 0
        else:
            out[m] = s

    return out


def amp2db(amp, ref:float = 20e-6) -> _Array:
    """Transform amplitude to dB.

    Return a copy of `amp` in dB scaling regarding a reference pressure `ref`.
    The reference pressure is commonly the human hearing treshold at
    20 micro Pa.

    `amp` is supposed to be a inon-negative scalar or numpy.array taken from a
    magnitude spectrum.

    This function set all values of `amp` smaller then `ref` to `ref`, hence
    eliminating inaudible singnal energy in the log domain.

    Params:
        amp    (array-like or number) Given amplitude values.

    Return:
        (ndarray)    values in dB.
    """
    return 20 * _np.log10(_np.maximum(amp, ref) / ref)


def corr_coef_pearson(x, y):
    """Fast perason correlation coefficient."""
    detr_x = x - _np.mean(x)
    detr_y = y - _np.mean(y)

    r_xy = _np.convolve(detr_x, detr_y[::-1], mode='valid')
    r_xx_yy = (detr_x @ detr_x) * (detr_y @ detr_y)

    return r_xy / r_xx_yy


def freq2mel(f):
    """Transforms Hz to Mel-Frequencies.

    Params:
        f:    (real number) Frequency in Hz

    Return:
        (real number) Mel-Frequency
    """
    f = _np.atleast_1d(f)
    return 1125 * _np.log(1 + f / 700)


def mel2freq(z):
    """Transforms Mel-Frequencies to Hz.

    Params:
        z:     (real number) Mel-Frequency.

    Return:
        (real number) Frequency in Hz.
    """
    z = _np.atleast_1d(z)
    return 700 * (_np.exp(z / 1125) - 1)




def maxamp(sig):
    """Maximal absolute elongation within the signal.

    Params:
        sig    (array-like) Input signal.

    Return:
        (scalar) Maximal amplitude.
    """
    return _np.max(_np.absolute(sig))


def minamp(sig):
    """Minimal absolute elongation within the signal.

    Params
        sig    (array-like) Input signal.

    Return:
        (scalar) Maximal amplitude.
    """
    return _np.min(_np.absolute(sig))


def noise(level, n=9000):
    """Generate withe noise.

    Params:
        level       (float) Noise level as standard deviation of a gaussian.
        n           (int) Length of noise signal in samples.

    Return:
        (ndarray)   White noise signal.
    """
    return _stats.norm.rvs(0, level, size=n)


def normalize(sig):
    """Normlize a signal to [-1.0, 1.0].

    Params:
        sig (np.nadarray)    Signal to normalize.

    Return:
        (np.ndarray) Normalized signal.
    """
    return sig / _np.max(_np.absolute(sig), axis=0)

    
def sinusoid(f, amps=1, fs=9000, length=1, retcomps=False):
    """Generate sinusoidal signal.

    Params:
        f       (iterable) Component frequencies.
        amps    (int or interable) Amplitude of each component in f.
                    If `amps` is an integer each component of f will be
                    scaled according to `amps`. If `amps` is an iterable
                    each frequency will be scaled with the respective amplitude.
        fs      (int) Sample rate.
        length  (number) Length of signal in seconds.
        retcomps(bool) If True return the components of the signal,
                    otherwise return the sum.

    Return:
        (ndarray)   Sinusoidal signal.
    """
    f = _np.atleast_1d(f)
    amps = _np.atleast_1d(amps)

    if f.shape == amps.shape or amps.size == 1:
        t = _np.arange(fs*length)[:, None] / fs
        sig = _np.sin(2*_np.pi*f*t) * amps
    else:
        raise ValueError('Shapes of f and amps must be equal.')

    if retcomps:
        return sig
    else:
        return sig.sum(axis=1)


def zero_padding(sig, n):
    """Append n zeros to signal. `sig` must be 1D array.

    Params:
        sig    (np.ndarray) a list of data points.
        n      (int) number of zeros to be appended.

    Return:
        (array) zero-padded input signal.
    """
    container = _np.zeros(sig.size+n)
    container[:sig.size] = sig
    return container


def trim_spectrogram(inp: _Array, frqs: _Array, low: float, high: float) -> _Array:
    """Trim spectrogram and frequency array to the frequency range [low, high].

    Args:
        inp  (ndarray)    Input spectrogram.
        frqs (ndarray)    Spectrogram frequency axis.
        low  (float)      Lower trim boundary.
        high (float)      Upper trim boundary.

    Returns:
        (tuple)    (trimmed_spectrogram, trimmed_frqs)
    """
    lower_bound = _np.maximum(low, frqs[0])
    upper_bound = _np.minimum(high, frqs[-1])

    clip_range = _np.logical_and(lower_bound <= frqs, frqs <= upper_bound)

    return inp[clip_range], frqs[clip_range]
