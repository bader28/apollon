#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""em.py

Generic implementation of the Expectation Maximization algorithm.
"""

import numpy as _np
from scipy import stats
from apollon.hmm.fwbw import forward_backward

__author__ = "Michael Blaß"


def EM(x, m, theta, maxiter=1000, tol=1e-6):
    '''    Estimate the parameters of an m-state PoissonHMM.

    Params:
        x          (array-like of ints) the data to train the HMM
        phmm       (int)
        maxiter    (int) maximum number of EM iterations
            tol    (float) break the loop if the difference between
                           to consecutive iterations is < tol
    '''
    
    n = len(x)

    m_lambda = theta[0].copy()
    m_gamma = theta[1].copy()
    m_delta = theta[2].copy()

    next_lambda = theta[0].copy()
    next_gamma = theta[1].copy()
    next_delta = theta[2].copy()

    for i in range(maxiter):
        alpha, beta, allprobs = forward_backward(x, m, m_lambda, m_gamma, m_delta)

        c = max(alpha[-1])
        log_likelihood = c + _np.log(_np.sum(_np.exp(alpha[-1] - c)))

        for j in range(m):
            for k in range(m):
                next_gamma[j, k] *= _np.sum(_np.exp(alpha[:n - 1, j] +
                                            beta[1:n, k] +
                                            allprobs[1:n, k] -
                                            log_likelihood))

            rab = _np.exp(alpha[:, j] + beta[:, j] - log_likelihood)
            next_lambda[j] = _np.sum(rab * x) / _np.sum(rab)

        next_gamma /= _np.sum(next_gamma, axis=1)
        next_delta = _np.exp(alpha[0] + beta[0] - log_likelihood)
        next_delta /= _np.sum(next_delta)

        crit = (_np.sum(_np.absolute(m_lambda - next_lambda)) +
                _np.sum(_np.absolute(m_gamma - next_gamma)) +
                _np.sum(_np.absolute(m_delta - next_delta)))

        if crit < tol:
            nparams = m*m + m-1
            aic = -2 * (log_likelihood - nparams)
            bic = -2 * log_likelihood + nparams * _np.log(n)

            return (m_lambda, m_gamma, m_delta, i, -log_likelihood,
                    0, True, aic, bic)

        m_lambda = next_lambda
        m_gamma = next_gamma
        m_delta = next_delta
    return False
