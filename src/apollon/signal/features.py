"""apollon/signal/features.py -- Feature extraction routines
j
Licensed under the terms of the BSD-3-Clause license.
Copyright (C) 2019 Michael Blaß
mblass@posteo.net

Functions:
    cdim            Fractal correlation dimension.
    correlogram     Windowed auto-correlation.
    energy          Total signal energy.
    rms             Root mean square.
    spectral_centroid
    spectral_spread
    spectral_flux
    spl             Sound preassure level.
    splc
    loudness        Estimate of perceived loudness.
    roughness       Estimate of perceived roughness.
    sharpness       Estimate of perceived sharpness.
"""

import numpy as _np
from scipy.signal import hilbert as _hilbert

import _features
from . import tools as _sigtools
from .. import segment as _segment
from .. import tools
from .. types import Array as _Array
from . import critical_bands as _cb
from .. audio import fti16
from .. import _defaults


def cdim(inp: _Array, delay: int, m_dim: int, n_bins: int = 1000,
         scaling_size: int = 10, mode: str = 'bader') -> _Array:
    # pylint: disable = too-many-arguments
    """Compute an estimate of the correlation dimension of the input data.

    If ``mode`` is set to 'bader', the input array must have at least
    2400 elements. Otherwise, the result is undefined.

    Args:
        inp:       Input array.
        delay:     Embedding delay in samples.
        m_dim:     Number of embedding dimensions.
        n_bins:    Number of bins.
        mode:      Use either 'bader' for the original algorithm
                   or 'blass' for the refined version.

    Returns:
        Array of correlation dimension estimates.

    Raises:
        ValueError
    """
    if inp.ndim != 2:
        raise ValueError(f'Input array must be two-dimensional.')

    if mode == 'bader':
        cdim_func = _features.cdim_bader
        if inp.dtype != 'int16':
            inp = fti16(inp)
    elif mode == 'blass':
        raise NotImplementedError
        # cdim_func = fractal.cdim
    else:
        raise ValueError(f'Unknown mode "{mode}". Expected either "bader", '
                         'or "blass"')
    out = _np.zeros(inp.shape[1])
    for i, seg in enumerate(inp.T):
        out[i] = _np.nan_to_num(cdim_func(seg, delay, m_dim, n_bins,
                                          scaling_size))
    return _np.expand_dims(out, 0)


def correlogram(inp: _Array, wlen: int, n_delay: int,
                total: bool = False) -> _Array:
    """Windowed autocorrelation of ``inp``.

    This function computes the autocorrelation of a ``wlen``-sized
    window of the input.

    Args:
        inp:        One-dimensional input signal.
        wlen:       Length of the autocorrelation window.
        n_delay:    Number of delay.

    Returns:
        Two-dimensional array in which each column is an auto-correlation
        function.
    """
    if not isinstance(inp, _np.ndarray):
        raise TypeError(f'Argument ``inp`` is of type {type(inp)}. It has '
                        'to be an numpy array.')

    if inp.ndim != 2:
        raise ValueError('Input must be two-dimensional.')

    out = _np.zeros((inp.shape[1], n_delay, inp.shape[0]-wlen-n_delay))
    for i, seg in enumerate(inp.T):
        out[i] = _features.correlogram(seg, wlen, n_delay)
    if total is True:
        return out.sum(axis=(1, 2)) / _np.prod(out.shape[1:])
    return out


def energy(sig: _Array) -> _Array:
    """Total energy of time domain signal.

    Args:
        sig:  Time domain signal.

    Returns:
        Energy along fist axis.
    """
    if not _np.isfinite(sig).all():
        raise ValueError('Input ``sig`` contains NaNs or infinite values.')
    return _np.sum(_np.square(_np.abs(sig)), axis=0, keepdims=True)


def rms(sig: _Array) -> _Array:
    """Root mean square of time domain signal.

    Args:
        sig:  Time domain signal

    Returns:
        RMS of signal along first axis.
    """
    return _np.sqrt(_np.mean(_np.square(_np.abs(sig)), axis=0, keepdims=True))


def frms(bins: _Array, n_sig: int, window: str = None) -> _Array:
    """Root meann square of signal energy estimated in the spectral domain.

    Args:
        bins:    DFT bins.
        n_sig:   Size of original signal.
        window:  Window function applied to original signal.

    Returns:
        Estimate of signal energy along first axis.
    """
    vals = bins * n_sig
    if n_sig % 2:
        vals /= 2
    else:
        vals[:-1] /= 2
    rms_ = _np.sqrt(2*energy(vals)) / n_sig
    if window:
        rms_ /= rms(getattr(_np, window)(n_sig))
    return rms_


def spectral_centroid(frqs: _Array, bins: _Array) -> _Array:
    """Estimate the spectral centroid frequency.

    Spectral centroid is always computed along the second axis of ``bins``.

    Args:
        frqs:     Nx1 array of DFT frequencies.
        power:    NxM array of DFT bin values.

    Returns:
        1xM array of spectral centroids.
    """
    return tools.fsum(frqs*_power_distr(bins), axis=0, keepdims=True)


def spectral_flux(inp: _Array, delta: float = 1.0,
                  total: bool = True) -> _Array:
    """Estimate the spectral flux

    Args:
        inp:      Input data. Each row is assumend FFT bins.
        delta:    Sample spacing.
        total:    If ``True`` sum flux per bin.

    Returns:
        Two-dimensional array of Spectral Flux.
    """
    inp = _np.atleast_2d(inp).astype('float64')
    out = _np.maximum(_np.gradient(inp, delta, axis=-1), 0)
    if total:
        return out.sum(axis=0, keepdims=True)
    return out


def spectral_spread(frqs: _Array, bins: _Array,
                    centroids: _Array=None) -> _Array:
    """Estimate spectral spread.

    Spectral spread is always computed along the second axis of ``bins``.
    This function computes the square roote of spectral spread.

    Args:
        frqs:       Nx1 array of DFT frequencies.
        power:      NxM array of DFT bin values.
        centroids:  Array Spectral Centroid values.

    Returns:
        Square root of spectral spread.
    """
    if centroids is None:
        centroids = spectral_centroid(frqs, bins)
    deviation = _np.power(frqs-centroids, 2)
    return _np.sqrt(tools.fsum(deviation*_power_distr(bins), axis=0,
                               keepdims=True))


def spl(sig: _Array, ref: float = _defaults.SPL_REF):
    """Computes the average sound pressure level of time domain signal.

    Args:
        sig:  Time domain signal.
        ref:  Reference preassure in Pascal.

    Returns:
        Average sound pressure level.
    """
    level = rms(sig)/ref
    return 20 * _np.log10(level, where=level>0)


def spl_f(amps: _Array, total: bool = False,
          ref: float = _defaults.SPL_REF) -> _Array:
    """Sound preassure level estimated in spectral domain.

    The values of ``amp`` are assumed to be magnitudes of DFT bins.

    The reference pressure defaults to the human hearing treshold of 20 μPa.

    Args:
        amps:     Amplitude values.
        total:    If True, returns the total spl over all values. In case
                  ``amp`` is two-dimensional, the first axis is aggregated.
        ref:      Reference preassure in Pascal.

    Returns:
        Sound pressure level of ``amp``.
    """
    vals = _np.power(amps/ref, 2)
    if total:
        vals = vals.sum(axis=0, keepdims=True)
    vals = _np.maximum(1.0, vals)
    return 10.0*_np.log10(vals)


def fsplc(frqs: _Array, amps: _Array, total: bool = False,
          ref: float = _defaults.SPL_REF) -> _Array:
    """Apply C-weighted to SPL.

    Args:
        frqs:    Center frequency of DFT band.
        amps:    Magnitude of DFT band.
        ref:     Reference preassure in Pascal.

    Returns:
        C-weighted sound pressure level.
    """
    return spl(_sigtools.c_weighting(frqs)*amps, total, ref)


def log_attack_time(inp: _Array, fps: int, ons_idx: _Array,
                    wlen: float = 0.05) -> _Array:
    """Estimate the attack time of each onset and return its logarithm.

    This function estimates the attack time as the duration between the
    onset and the local maxima of the magnitude of the Hilbert transform
    of the local window.

    Args:
        inp:      Input signal.
        fps:      Sampling frequency.
        ons_idx:  Sample indices of onsets.
        wlen:     Local window length in samples.

    Returns:
        Logarithm of the attack time.
    """
    wlen = int(fps * wlen)
    segs = _segment.by_onsets(inp, wlen, ons_idx)
    attack_time = _np.absolute(_hilbert(segs)).argmax(axis=1) / fps
    attack_time[attack_time == 0.0] = 1.0
    return _np.log(attack_time)


def loudness(frqs: _Array, bins: _Array) -> _Array:
    """Calculate a measure for the perceived loudness from a spectrogram.

    Args:
        frqs:   Frquency axis.
        bins:   Magnitude spectrogram.

    Returns:
        Estimate of the total loudness.
    """
    cbrs = _cb.filter_bank(frqs) @ bins
    return _cb.total_loudness(cbrs)


def roughness_helmholtz(d_frq: float, bins: _Array, frq_max: float,
                        total: bool = True) -> _Array:
    kernel = _roughnes_kernel(d_frq, frq_max)
    out = _np.empty((kernel.size, bins.shape[1]))
    for i, bin_slice in enumerate(bins.T):
        out[:, i] = _np.correlate(bin_slice, kernel, mode='same')

    if total is True:
        out = out.sum(axis=0, keepdims=True)
    return out


def sharpness(frqs: _Array, bins: _Array) -> _Array:
    """Calculate a measure for the perception of auditory sharpness from a
    spectrogram.

    Args:
        frqs:    Frequencies.
        bins:    DFT magnitudes.

    Returns:
        Sharpness.
    """
    cbrs = _cb.filter_bank(frqs.squeeze()) @ bins
    return _cb.sharpness(cbrs)


def _power_distr(bins: _Array) -> _Array:
    """Computes the spectral energy distribution.

    Args:
        bins:    NxM array of DFT bins.

    Returns:
        NxM array of spectral densities.
    """
    total_power = tools.fsum(bins, axis=0, keepdims=True)
    total_power[total_power == 0] = 1
    return bins / total_power


def _roughnes_kernel(frq_res: float, frq_max: float) -> _Array:
    """Comput the convolution kernel for roughness computation.

    Args:
        frq_res:    Frequency resolution
        frq_max:    Frequency bound.

    Returns:
        Weight for each frequency below ``frq_max``.
    """
    frm = 33.5
    bin_idx = int(_np.round(frq_max/frq_res))
    norm = frm * _np.exp(-1)
    base = _np.abs(_np.arange(-bin_idx, bin_idx+1)) * frq_res
    return base / norm * _np.exp(-base/frm)
