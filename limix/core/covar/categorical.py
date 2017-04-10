from .covar_base import Covariance
from limix.hcache import cached
import numpy as np

# TODO can we do import LowRankCov ?
import lowrank
import freeform


class Categorical(Covariance):
    """
    Categorical covariance.
    cov_{i,j} depends on the category of i and j only

    Main members of the class:
        - categories: a vector of length the dimension of the cov matrix with the
        categories to which every sample belongs
        - cat_cov, a covariance matrix between categories, whose dimensions are determined
        by the number of categories -> can be free form or low rank
    """
    def __init__(self, categories, rank=None, cat_star=None, jitter= 1e-4):
        Covariance.__init__(self)

        self.cat = categories
        self.jitter = jitter
        self.rank = rank

        # TODO do this cleanly with setters and properties (including the initialise_function)
        # initialisation predictions
        self.cat_star = cat_star

        # if self.cat_star is None:
        #     self._use_to_predict = False
        # else:
        #     self.initialize_cat_star()
        #     self._use_to_predict = True

        # initialise covariance matrix between categories
        # self.initialize_cov()
        # # build a categories_num vector where categories are integers from 0 to number of categories
        # self.initialize_cats()
        #
    # def initialize_cov(self):
    #     if self.rank is None:
    #         self.cat_cov = freeform.FreeFormCov(self.n_cats, jitter=self.jitter)
    #     else:
    #         self.cat_cov = lowrank.LowRankCov(self.n_cats, self.rank)
    #
    # def initialize_cats(self):
    #     self._i_cats = np.zeros(len(self.cat))
    #     for i in range(self.n_cats):
    #         self._i_cats += (self.cat == self.unique_cats[i])*i

    # def initialize_cat_star(self):
    #     # check that all categories in cat_star are also found in cats
    #     cat_star_uq = np.unique(self.cat_star)
    #     assert all(np.in1d(cat_star_uq, self.unique_cats)), 'all categories used for prediction must be seen during training'
    #
    #     # build the int category vector
    #     self.i_cat_star = np.zeros(len(self.cat_star))
    #     for i in range(self.n_cats):
    #         self.i_cat_star += (self.cat_star == self.unique_cats[i])*i

    #####################
    # properties
    #####################
    @property
    def cat(self):
        return self._cat

    @property
    def rank(self):
        return self._rank

    @property
    def cat_star(self):
        return self._cat_star

    #####################
    # Setters
    #####################
    @cat.setter
    def cat(self, value):
        self._cat = value

        # initialise related members
        self.dim = len(value)
        self.unique_cats = np.unique(value)
        self.n_cats = len(self.unique_cats)

        # initialise int indexed categories
        self._i_cats = np.zeros(len(value))
        for i in range(self.n_cats):
            self._i_cats += (value == self.unique_cats[i])*i

    @rank.setter
    def rank(self, value):
        self._rank = value
        if value is None:
            self.cat_cov = freeform.FreeFormCov(self.n_cats, jitter=self.jitter)
        else:
            assert value <= self.n_cats, 'rank cant be higher than number of categories'
            self.cat_cov = lowrank.LowRankCov(self.n_cats, value)

    @cat_star.setter
    def cat_star(self, value):
        if value is None:
            self._use_to_predict = False
            self._cat_star = value
        else:
            self._use_to_predict = True

            # check that all categories in cat_star are also found in cats
            cat_star_uq = np.unique(self.cat_star)
            assert all(np.in1d(cat_star_uq, self.unique_cats)), 'all categories used for prediction must be seen during training'

            # build the int category vector
            self.i_cat_star = np.zeros(len(self.cat_star))
            for i in range(self.n_cats):
                self.i_cat_star += (self.cat_star == self.unique_cats[i])*i

    #####################
    # Params handling
    #####################
    def setParams(self, params):
        self.cat_cov.setParams(params)

    def getParams(self):
        return self.cat_cov.getParams()

    def getInterParams(self):
        return self.cat_cov.getInterParams()

    def getNumberParams(self):
        return self.cat_cov.getNumberParams()

    #####################
    # cov and gradient
    # DO NOT CACHE here (cached in member cat_cov)
    #####################
    def K(self):
        R = self.cat_cov.K()
        return self.expand(R)

    def K_grad_i(self, i):
        R = self.cat_cov.K_grad_i(i)
        return self.expand(R)

    def Kcross(self):
        R = self.cat_cov.K()
        return self.expand_star(R)

    # TODO: hessian ? not implemented for lowrank

    #####################
    # Expanding the category * category matrices
    #####################
    # for the covariance or its gradient
    def expand(self, mat):
        R = np.zeros([self.dim, self.dim])
        for i in range(self.n_cats):
            for j in range(self.n_cats):
                tmp_i = (self._i_cats == i)[:, None]
                tmp_j = (self._i_cats == j)[None, :]
                R += tmp_i.dot(tmp_j) * mat[i,j]
        return R

    # for the cross covariance
    def expand_star(self, mat):
        n_star = len(self.cat_star)
        R = np.zeros([n_star, self.dim])
        for i in range(self.n_cats):
            for j in range(self.n_cats):
                tmp_i = (self.i_cat_star == i)[:, None]
                tmp_j = (self._i_cats == j)[None, :]
                R += tmp_i.dot(tmp_j) * mat[i,j]
        return R
