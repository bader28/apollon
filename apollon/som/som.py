# Licensed under the terms of the BSD-3-Clause license.
# Copyright (C) 2019 Michael Blaß
# michael.blass@uni-hamburg.de

# apollon/som/som.py
# SelfOrganizingMap module
#

import numpy as _np
import matplotlib.pyplot as _plt
from scipy import stats as _stats
from scipy.spatial import distance as _distance

from apollon.io import save as _save
from apollon.som import utilities as _utilities
from apollon.som import defaults as _defaults
from apollon.aplot import _new_axis, _new_axis_3d
from apollon import aplot as aplot

class _som_base:
    def __init__(self, dims, eta, nhr, n_iter, metric, mode, init_distr, seed=None):

        # check dimensions
        for d in dims:
            if not isinstance(d, int) or not d >= 1:
                raise ValueError('Dimensions must be integer > 0.')


        # shape parameters
        self.dims = dims
        self.dx = self.dims[0]
        self.dy = self.dims[1]
        self.dw = self.dims[2]
        self.shape = (self.dx, self.dy)

        # total number of neuros on the map
        self.n_N = self.dx * self.dy

        # center index of the map
        self.center = self.dx // 2, self.dy // 2

        # number of iterations to perform
        self.n_iter = n_iter

        # training mode
        self.mode = mode

        # metric for similarity ratings
        self.metric = metric

        # check training parameters
        if eta is None:
            self.init_eta = None
        else:
            if (0 <= eta <= 1.):
                self.init_eta = eta
            else:
                raise ValueError('eta not in [0, 1]')

        if isinstance(nhr, int) and nhr > 1:
            self.init_nhr = nhr
            #self.final_nhr = max(self.dx, self.dy) / _defaults.nhr_scale_factor
        else:
            raise ValueError('Neighbourhood radius must be int > 0.')

        # Initialize the weights
        if seed is not None:
            _np.random.seed(seed)

        # TODO: init range should be in terms of data
        if init_distr == 'uniform':
            self.weights = _np.random.uniform(0, 1, size=(self.n_N, self.dw))
        elif init_distr == 'simplex':
            self.weights = self._init_st_mat()

        # Allocate array for winner histogram
        # TODO: add array to collect for every winner the correspondig inp vector.
        self.whist = _np.zeros(self.n_N)

        # grid data for neighbourhood calculation
        self._grid = _np.mgrid[:self.dx, :self.dy]
        self._grid = _np.dstack(self._grid).reshape(self.n_N, 2)

        # calibration
        self.isCalibrated = False
        self.calibration = None

        # measures
        self.quantization_error = []

        # winner trajectories on Map
        self.trajectories = []

    def get_winners(self, data, argax=1):
        """Get the best matching neurons for every vector in data.

            Args:
                data:  Input data set
                argax: Axis used for minimization 1=x, 0=y.

            Returna:
                Indices of bmus and min dists.
        """
        # TODO: if the distance between an input vector and more than one lattice
        #       neuro is the same, choose winner randomly.

        if data.ndim == 1:
            d = _distance.cdist(data[None, :], self.weights, metric=self.metric)
            return _np.argmin(d), _np.min(d**2, axis=1)
        elif data.ndim == 2:
            ds = _distance.cdist(data, self.weights, metric=self.metric)
            return _np.argmin(ds, axis=argax), _np.sum(_np.min(ds, axis=argax)**2)
        else:
            raise ValueError('Wrong dimension of input data: {}'.format(data.ndim))


    def nh_gaussian_L2(self, center, r):
        """Compute 2D Gaussian neighbourhood around `center`. Distance between
           center and m_i is calculate by Euclidean distance.
        """
        d = _distance.cdist(_np.array(center)[None, :], self._grid,
                           metric='sqeuclidean')
        ssq = 2 * r**2
        return _np.exp(-d/ssq).reshape(-1, 1)


    def _init_st_mat(self):
        """Initialize the weights with stochastic matrices.

        The rows of each n by n stochastic matrix are sampes drawn from the
        Dirichlet distribution, where n is the number of rows and cols of the
        matrix. The diagonal elemets of the matrices are set to twice the
        probability of the remaining elements.
        The square root n of the weight vectors' size must be element of the
        natural numbers, so that the weight vector is reshapeable to a square
        matrix.
        """
        # check for square matrix
        d = _np.sqrt(self.dw)
        is_not_qm = bool(d - int(d))
        if is_not_qm:
            raise ValueError('Weight vector (len={}) must be reshapeable to square matrix.'.format(self.dw))
        else:
            d = int(d)

        # set alpha
        alpha = _np.full((d, d), 500)
        _np.fill_diagonal(alpha, 1000)

        # sample from dirichlet distributions
        st_matrix = _np.hstack([_stats.dirichlet.rvs(alpha=a, size=self.n_N)
                               for a in alpha])
        return st_matrix


    def calibrate(self, data, targets):
        """Retriev for every map unit the best matching vector of the input
        data set. Save its target value at the map units position on a
        new array called `calibration`.

        Args:
            data:     Input data set.
            targets:  Target labels.
        """
        bmiv, err = self.get_winners(data, argax=0)
        self._cmap = targets[bmiv]
        self.isCalibrated = True


    def plot_calibration(self, lables=None, ax=None, cmap='plasma', **kwargs):
        """Plot calibrated map.

        Args:
            labels:
            ax
            cmap:

        Returns:
        """
        if not self.isCalibrated:
            raise ValueError('Map not calibrated.')
        else:
            if ax is None:
                fig, ax = _new_axis()
            ax.set_title('Calibration')
            ax.set_xlabel('# units')
            ax.set_ylabel('# units')
            ax.imshow(self._cmap.reshape(self.dx, self.dy), origin='lower',
                      cmap=cmap)
            #return ax


    def plot_datamap(self, data, targets, interp='None', marker=False,
                     cmap='viridis', **kwargs):
        """Represent the input data on the map by retrieving the best
        matching unit for every element in `data`. Mark each map unit
        with the corresponding target value.

        Args:
            data:    Input data set.
            targets: Class labels or values.
            interp:  matplotlib interpolation method name.
            marker:  Plot markers in bmu position if True.

        Returns:
           axis, umatrix, bmu_xy
        """
        ax, udm = self.plot_umatrix(interp=interp, cmap=cmap, **kwargs)

        #
        # TODO: Use .transform() instead
        #
        bmu, err = self.get_winners(data)

        x, y = _np.unravel_index(bmu, (self.dx, self.dy))
        fd = {'color':'#cccccc'}
        if marker:
            ax.scatter(y, x, s=40, marker='x', color='r')

        for i, j, t in zip(x, y, targets):
            ax.text(j, i, t, fontdict=fd,
                    horizontalalignment='center',
                    verticalalignment='center')
        return (ax, udm, (x, y))


    def plot_qerror(self, ax=None, **kwargs):
        """Plot quantization error."""
        if ax is None:
            fig, ax = _new_axis(**kwargs)

        ax.set_title('Quantization Errors per iteration')
        ax.set_xlabel('# interation')
        ax.set_ylabel('Error')

        ax.plot(self.quantization_error, lw=3, alpha=.8,
                label='Quantizationerror')


    def plot_umatrix(self, interp='None', cmap='viridis', ax=None, **kwargs):
        """Plot unified distance matrix.

        The unified distance matrix (udm) allows to visualize weight matrices
        of high dimensional weight vectors. The entries (x, y) of the udm
        correspondto the arithmetic mean of the distances between weight
        vector (x, y) and its 4-neighbourhood.

        Args:
            w:        Neighbourhood width.
            interp:   matplotlib interpolation method name.
            ax:       Provide custom axis object.

       Returns:
           axis, umatrix
        """
        if ax is None:
            fig, ax = aplot._new_axis()
        udm = _utilities.umatrix(self.weights, self.shape, metric=self.metric)

        ax.set_title('Unified distance matrix')
        ax.set_xlabel('# units')
        ax.set_ylabel('# units')
        ax.imshow(udm, interpolation=interp, cmap=cmap, origin='lower')
        return ax, udm


    def plot_umatrix3d(self, w=1, cmap='viridis', **kwargs):
        """Plot the umatrix in 3d. The color on each unit (x, y) represents its
           mean distance to all direct neighbours.

        Args:
            w: Neighbourhood width.

        Returns:
            axis, umatrix
        """
        fig, ax = _new_axis_3d(**kwargs)
        udm = _utilities.umatrix(self.weights, self.shape, metric=self.metric)
        X, Y = _np.mgrid[:self.dx, :self.dy]
        ax.plot_surface(X, Y, udm, cmap=cmap)
        return ax, udm


    def plot_features(self, figsize=(8, 8)):
        """Values of each feature of the weight matrix per map unit.

        This works currently ony for feature vectors of len dw**2.

        Args:
            Size of figure.
        """
        d = _np.sqrt(self.dw).astype(int)
        rweigths = self.weights.reshape(self.dims)

        fig, _ = _plt.subplots(d, d, figsize=figsize, sharex=True, sharey=True)
        for i, ax in enumerate(fig.axes):
            ax.axison=False
            ax.imshow(rweigths[..., i], origin='lower')


    def plot_whist(self, interp='None', ax=None, **kwargs):
        """Plot the winner histogram.

        The darker the color on position (x, y) the more often neuron (x, y)
        was choosen as winner. The number of winners at edge neuros is
        magnitudes of order higher than on the rest of the map. Thus, the
        histogram is shown in log-mode.

        Args:
            interp: matplotlib interpolation method name.
            ax:     Provide custom axis object.

        Returns:
            The axis.
        """
        if ax is None:
            fig, ax = _new_axis(**kwargs)
        ax.imshow(_np.log1p(self.whist.reshape(self.dx, self.dy)),
                  vmin=0, cmap='Greys', interpolation=interp, origin='lower')
        return ax


    def save(self, path):
        """Save som object to file using pickle.

        Args:
            path: Save SOM to this path.
        """
        _save(self, path)


    def transform(self, data, flat=True):
        """Transform input data to feature space.

        Args:
            data:  2d array of shape (N_vect, N_features).
            flat:  Return flat index of True else 2d multi index.

        Returns:
            Position of each data item in the feature space.
        """
        bmu, err = self.get_winners(data)

        if flat:
            return bmu

        else:
            midx = _np.unravel_index(bmu, (self.dx, self.dy))
            return _np.array(midx)


    def inspect(self):
        fig = _plt.figure(figsize=(12, 5))
        ax1 = _new_axis(sp_pos=(1, 3, 1), fig=fig)
        ax2 = _new_axis(sp_pos=(1, 3, 2), fig=fig)
        ax3 = _new_axis(sp_pos=(1, 3, 3), fig=fig)

        _, _ = self.plot_umatrix(ax=ax1)

        if self.isCalibrated:
            _ = self.plot_calibration(ax=ax2)
        else:
            _ = self.plot_whist(ax=ax2)

        self.plot_qerror(ax=ax3)



class SelfOrganizingMap(_som_base):

    def __init__(self, dims=(10, 10, 3), eta=.8, nh=5, n_iter=100,
                 metric='euclidean', mode='incremental', init_distr='simplex',
                 seed=None):

        super().__init__(dims, eta, nh, n_iter, metric, mode, init_distr, seed)

        #
        # TODO: Implement mechanism to choose nh_function
        #
        self._neighbourhood = self.nh_gaussian_L2

    def _incremental_update(self, data_set, c_eta, c_nhr):
        total_qE = 0
        for fv in data_set:
            bm_units, c_qE = self.get_winners(fv)
            total_qE += c_qE

            # update activation map
            self.whist[bm_units] += 1
            self.trajectories.append(bm_units)

            # get bmu's multi index
            bmu_midx = _np.unravel_index(bm_units, self.shape)

            # calculate neighbourhood over bmu given current radius
            c_nh = self._neighbourhood(bmu_midx, c_nhr)

            # update lattice
            self.weights += c_eta * c_nh * (fv - self.weights)
        self.quantization_error.append(total_qE)


    def _batch_update(self, data_set, c_nhr):
        # get bmus for vector in data_set
        bm_units, total_qE = self.get_winners(data_set)
        self.quantization_error.append(total_qE)

        # get bmu's multi index
        bmu_midx = _np.unravel_index(bm_units, self.shape)

        w_nh = _np.zeros((self.n_N, 1))
        w_lat = _np.zeros((self.n_N, self.dw))

        for bx, by, fv in zip(*bmu_midx, data_set):
            # TODO:  Find a way for faster nh computation
            c_nh = self._neighbourhood((bx, by), c_nhr)
            w_nh += c_nh
            w_lat += c_nh * fv

        self.weights = w_lat / w_nh


    def train_batch(self, data, verbose=False):
        """Feed the whole data set to the network and update once
           after each iteration.

        Args:
            data:    Input data set.
            verbose: Print verbose messages if True.
        """
        # main loop
        for (c_iter, c_nhr) in \
            zip(range(self.n_iter),
                _utilities.decrease_linear(self.init_nhr, self.n_iter)):

            if verbose:
                print(c_iter, end=' ')

            self._batch_update(data, c_nhr)


    def train_minibatch(self, data, verbose=False):
        raise NotImplementedError

    def train_incremental(self, data, verbose=False):
        """Randomly feed the data to the network and update after each
           data item.

        Args:
            data:     Input data set.
            verbose:  Print verbose messages if True.
        """
        # main loop
        for (c_iter, c_eta, c_nhr) in \
            zip(range(self.n_iter),
                _utilities.decrease_linear(self.init_eta, self.n_iter, _defaults.final_eta),
                _utilities.decrease_expo(self.init_nhr, self.n_iter, _defaults.final_nhr)):

            if verbose:
                print('iter: {:2} -- eta: {:<5} -- nh: {:<6}' \
                 .format(c_iter, _np.round(c_eta, 4), _np.round(c_nhr, 5)))

            # always shuffle data
            self._incremental_update(_np.random.permutation(data), c_eta, c_nhr)


    def fit(self, data, verbose=False):
        """Train the SOM on the given data set."""

        if self.mode == 'incremental':
            self.train_incremental(data, verbose)

        elif self.mode == 'batch':
            self.train_batch(data, verbose)


    def predict(self, data):
        """Predict a class label for each item in input data. SOM needs to be
        calibrated in order to predict class labels.
        """
        if self.isCalibrated:
            midx = self.transform(data)
            return self._cmap[midx]
        else:
            raise AttributeError('SOM is not calibrated.')


#from apollon.hmm.poisson_hmm import hmm_distance

class DotSom(_som_base):
    def __init__(self, dims=(10, 10, 3), eta=.8, nh=8, n_iter=10,
                 metric='euclidean', mode=None, init_distr='uniform', seed=None):
        """ This SOM assumes a stationary PoissonHMM on each unit. The weight vector
        represents the HMMs distribution parameters in the following order
        [lambda1, ..., lambda_m, gamma_11, ... gamma_mm]

        Args:
            dims    (tuple) dx, dy, m
        """
        super().__init__(dims, eta, nh, n_iter, metric, mode, init_distr, seed)
        self._neighbourhood = self.nh_gaussian_L2

    def get_winners(self, data, argax=1):
        """Get the best matching neurons for every vector in data.

        Args:
            data:  Input data set
            argax: Axis used for minimization 1=x, 0=y.

        Returns:
            Indices of bmus and min dists.
        """
        # TODO: if the distance between an input vector and more than one lattice
        #       neuro is the same, choose winner randomly.

        d = _np.inner(data, self.weights)
        return _np.argmax(d), 0



    def fit(self, data, verbose=True):
        for (c_iter, c_eta, c_nhr) in \
            zip(range(self.n_iter),
                _utilities.decrease_linear(self.init_eta, self.n_iter, _defaults.final_eta),
                _utilities.decrease_expo(self.init_nhr, self.n_iter, _defaults.final_nhr)):

            if verbose:
                print('iter: {:2} -- eta: {:<5} -- nh: {:<6}' \
                 .format(c_iter, _np.round(c_eta, 4), _np.round(c_nhr, 5)))

            # always shuffle data
            self._incremental_update(_np.random.permutation(data), c_eta, c_nhr)


    def _incremental_update(self, data_set, c_eta, c_nhr):
        total_qE = 0
        for fv in data_set:
            bm_units, c_qE = self.get_winners(fv)
            total_qE += c_qE

            # update activation map
            self.whist[bm_units] += 1

            # get bmu's multi index
            bmu_midx = _np.unravel_index(bm_units, self.shape)

            # calculate neighbourhood over bmu given current radius
            c_nh = self._neighbourhood(bmu_midx, c_nhr)

            # update lattice
            u = self.weights + c_eta * fv
            self.weights = u / _distance.norm(u)

        self.quantization_error.append(total_qE)
