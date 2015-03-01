from __future__ import print_function
import numpy as np
import pandas as pd
import numpy.testing as npt

from .. import statistics as stats
from ..datasets import load_waltons, load_g3


def test_unequal_intensity_with_random_data():
    data1 = np.random.exponential(5, size=(2000, 1))
    data2 = np.random.exponential(1, size=(2000, 1))
    test_result = stats.logrank_test(data1, data2)
    assert test_result.test_result


def test_logrank_test_output_against_R_1():
    df = load_g3()
    ix = (df['group'] == 'RIT')
    d1, e1 = df.ix[ix]['time'], df.ix[ix]['event']
    d2, e2 = df.ix[~ix]['time'], df.ix[~ix]['event']

    expected = 0.0138
    result = stats.logrank_test(d1, d2, event_observed_A=e1, event_observed_B=e2)
    assert abs(result.p_value - expected) < 0.0001


def test_logrank_test_output_against_R_2():
    # from https://stat.ethz.ch/education/semesters/ss2011/seminar/contents/presentation_2.pdf
    control_T = [1, 1, 2, 2, 3, 4, 4, 5, 5, 8, 8, 8, 8, 11, 11, 12, 12, 15, 17, 22, 23]
    control_E = np.ones_like(control_T)

    treatment_T = [6, 6, 6, 7, 10, 13, 16, 22, 23, 6, 9, 10, 11, 17, 19, 20, 25, 32, 32, 34, 25]
    treatment_E = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    result = stats.logrank_test(control_T, treatment_T, event_observed_A=control_E, event_observed_B=treatment_E)
    expected_p_value = 4.17e-05

    assert abs(result.p_value - expected_p_value) < 0.0001
    assert abs(result.test_statistic - 16.8) < 0.1


def test_unequal_intensity_event_observed():
    data1 = np.random.exponential(5, size=(2000, 1))
    data2 = np.random.exponential(1, size=(2000, 1))
    eventA = np.random.binomial(1, 0.5, size=(2000, 1))
    eventB = np.random.binomial(1, 0.5, size=(2000, 1))
    result = stats.logrank_test(data1, data2, event_observed_A=eventA, event_observed_B=eventB)
    assert result.test_result


def test_integer_times_logrank_test():
    data1 = np.random.exponential(5, size=(2000, 1)).astype(int)
    data2 = np.random.exponential(1, size=(2000, 1)).astype(int)
    result = stats.logrank_test(data1, data2)
    assert result.test_result


def test_equal_intensity_with_negative_data():
    data1 = np.random.normal(0, size=(2000, 1))
    data1 -= data1.mean()
    data1 /= data1.std()
    data2 = np.random.normal(0, size=(2000, 1))
    data2 -= data2.mean()
    data2 /= data2.std()
    result = stats.logrank_test(data1, data2)
    assert result.test_result is None


def test_unequal_intensity_with_negative_data():
    data1 = np.random.normal(-5, size=(2000, 1))
    data2 = np.random.normal(5, size=(2000, 1))
    result = stats.logrank_test(data1, data2)
    assert result.test_result


def test_waltons_dataset():
    df = load_waltons()
    ix = df['group'] == 'miR-137'
    waltonT1 = df.ix[ix]['T']
    waltonT2 = df.ix[~ix]['T']
    result = stats.logrank_test(waltonT1, waltonT2)
    assert result.test_result


def test_logrank_test_is_symmetric():
    data1 = np.random.exponential(5, size=(2000, 1)).astype(int)
    data2 = np.random.exponential(1, size=(2000, 1)).astype(int)
    result1 = stats.logrank_test(data1, data2)
    result2 = stats.logrank_test(data2, data1)
    assert abs(result1.p_value - result2.p_value) < 10e-8
    assert result2.test_result == result1.test_result


def test_multivariate_unequal_intensities():
    T = np.random.exponential(10, size=300)
    g = np.random.binomial(2, 0.5, size=300)
    T[g == 1] = np.random.exponential(1, size=(g == 1).sum())
    result = stats.multivariate_logrank_test(T, g)
    assert result.test_result


def test_pairwise_waltons_dataset_is_significantly_different():
    waltons_dataset = load_waltons()
    R = stats.pairwise_logrank_test(waltons_dataset['T'], waltons_dataset['group'])
    assert R.values[0, 1].test_result


def test_pairwise_logrank_test_with_identical_data_returns_inconclusive():
    t = np.random.exponential(10, size=100)
    T = np.tile(t, 3)
    g = np.array([1, 2, 3]).repeat(100)
    R = stats.pairwise_logrank_test(T, g, alpha=0.99).applymap(lambda r: r.test_result if r is not None else None)
    V = np.array([[None, None, None], [None, None, None], [None, None, None]])
    npt.assert_array_equal(R.values, V)


def test_pairwise_allows_dataframes():
    N = 100
    df = pd.DataFrame(np.empty((N, 3)), columns=["T", "C", "group"])
    df["T"] = np.random.exponential(1, size=N)
    df["C"] = np.random.binomial(1, 0.6, size=N)
    df["group"] = np.random.binomial(2, 0.5, size=N)
    stats.pairwise_logrank_test(df['T'], df["group"], event_observed=df["C"])


def test_log_rank_returns_None_if_equal_arrays():
    T = np.random.exponential(5, size=200)
    result = stats.logrank_test(T, T, alpha=0.95)
    assert result.test_result is None

    C = np.random.binomial(2, 0.8, size=200)
    result = stats.logrank_test(T, T, C, C, alpha=0.95)
    assert result.test_result is None


def test_multivariate_log_rank_is_identital_to_log_rank_for_n_equals_2():
    N = 200
    T1 = np.random.exponential(5, size=N)
    T2 = np.random.exponential(5, size=N)
    C1 = np.random.binomial(2, 0.9, size=N)
    C2 = np.random.binomial(2, 0.9, size=N)
    result = stats.logrank_test(T1, T2, C1, C2, alpha=0.95)

    T = np.r_[T1, T2]
    C = np.r_[C1, C2]
    G = np.array([1] * 200 + [2] * 200)
    result_m = stats.multivariate_logrank_test(T, G, C, alpha=0.95)
    assert result.test_result == result_m.test_result
    assert result.p_value == result_m.p_value

def test_StatisticalResult_class():
    sr = stats.StatisticalResult(True, 0.04, 5.0)
    assert sr.significant

    sr = stats.StatisticalResult(None, 0.04, 5.0)
    assert not sr.significant

    sr = stats.StatisticalResult(True, 0.05, 5.0, kw='some_value')
    assert hasattr(sr, 'kw')
    assert getattr(sr, 'kw') == 'some_value'
    assert 'some_value' in sr.__unicode__()



