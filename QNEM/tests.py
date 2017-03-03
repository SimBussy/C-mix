import unittest
import rpy2.robjects as ro
import pandas as pd
import numpy as np
from QNEM.inference import QNEM
from QNEM.simulation import CensoredGeomMixtureRegression
from sklearn.model_selection import ShuffleSplit


class Test(unittest.TestCase):
    def test_global_behavior(self):
        n_samples = 50
        n_features = 20
        nb_active_features = 5
        K = 1.
        gap = .3
        rho = 0.5
        r_cf = .5
        r_c = 0.5
        pi0 = 0.75
        p0 = .01
        p1 = 0.5
        verbose = True

        simu = CensoredGeomMixtureRegression(verbose, n_samples, n_features,
                                             nb_active_features, K, rho, pi0,
                                             gap, r_c, r_cf, p0, p1)
        X, Y, delta = simu.simulate()
        n_samples, n_features = X.shape

        test_size = .3
        rs = ShuffleSplit(n_splits=1, test_size=test_size, random_state=0)
        for train_index, test_index in rs.split(X):
            X_test = X[test_index]
            delta_test = delta[test_index]
            Y_test = Y[test_index]

            X = X[train_index]
            Y = Y[train_index]
            delta = delta[train_index]

        tol = 1e-6
        eta = 0.2
        fit_intercept = True
        warm_start = True
        grid_size = 3
        metric = 'C-index'
        verbose = True
        model = "C-mix"

        learner = QNEM(l_elastic_net=0., eta=eta, max_iter=100, tol=tol,
                       warm_start=warm_start, verbose=verbose, model=model,
                       fit_intercept=fit_intercept)
        learner.n_features = n_features

        learner.cross_validate(X, Y, delta, n_folds=5, verbose=False, eta=eta,
                               grid_size=grid_size, metric=metric)
        l_elastic_net_chosen = learner.l_elastic_net_chosen

        learner = QNEM(l_elastic_net=l_elastic_net_chosen, eta=eta, tol=tol,
                       warm_start=warm_start, verbose=verbose, model=model,
                       fit_intercept=fit_intercept)
        learner.n_features = n_features
        learner.fit(X, Y, delta)

        coeffs = learner.coeffs
        marker = QNEM.predict_proba(X_test, fit_intercept, coeffs)

        nb_t = 14
        timesAUC = pd.DataFrame(Y).quantile(
            q=(1. / nb_t + np.linspace(0, 1, nb_t, endpoint=False))[1:-1]
        ).drop_duplicates().as_matrix()

        ro.globalenv['Y_test'] = Y_test
        ro.globalenv['delta_test'] = delta_test
        ro.globalenv['marker'] = marker
        ro.globalenv['timesAUC'] = timesAUC
        ro.r('library(timeROC)')
        ro.r('auc_t = timeROC(Y_test,delta_test,marker,cause=1,times=timesAUC)')

if __name__ == "main":
    unittest.main()
