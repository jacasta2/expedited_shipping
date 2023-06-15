"""
helper_functions.py
    Functions used to engineer some features for data analysis and run some statistical tests. 
"""

from itertools import combinations
import pandas as pd
import numpy as np
import numpy_indexed as npi
from statsmodels.stats.libqsturng import qsturng, psturng
from hypothetical.descriptive import var


def assign_exp_profit(data):
    """
    This function adds columns with profit performance to the experiment data.

    Args:
        data: DataFrame with the experiment data.

    Returns:
        A DataFrame with the profit performance columns.
    """

    # Load the DataFrame with the normalized expected profits (from 0 to 1) for each order quantity
    # for each treatment
    exp_profit_df = pd.read_csv("exp_profit.csv")

    data[["exp_profit_norm", "proportion_max_exp_profit"]] = data.apply(
        lambda x: assign_exp_profit_work(x["order"], x["treatment_id"], exp_profit_df),
        axis=1,
    )

    return data


def assign_exp_profit_work(order, treatment, exp_profit_df):
    """
    This function assigns the normalized expected profit to an order quantity from a given treatment
    and computes its proportion of maximum expected profit achieved.

    Args:
        order: the order quantity.
        treatment: the treatment id.
        exp_profit_df: DataFrame with the normalized expected profits (from 0 to 1) for each order
            quantity for each treatment.

    Returns:
        A Series with the order's normalized expected profit and proportion of maximum expected
            profit achieved.
    """

    # Orders range from 0 to 100, just as the indexes of 'exp_profit_df'. Moreover, 'exp_profit_df'
    # has the E[profit] of Q = 0 in row 0, the E[profit] of Q = 1 in row 1, and so on, which
    # allows to use orders as indexes in 'iloc' to match orders with their expected profits.
    # Since the expected profits are normalized from 0 to 1, the computation of the second number
    # in the Series is unncesary. However, in case the expected profits come in a different scale,
    # we leave the computations as they are.

    # Treatments with k = 4 have the normalized expected profits in column 0
    if treatment in (8, 10):
        return pd.Series(
            [
                exp_profit_df.iloc[order, 0],
                exp_profit_df.iloc[order, 0] / exp_profit_df.iloc[:, 0].max(),
            ]
        )

    # Treatments with k = 6 have the normalized expected profits in column 1
    if treatment in (3, 11):
        return pd.Series(
            [
                exp_profit_df.iloc[order, 1],
                exp_profit_df.iloc[order, 1] / exp_profit_df.iloc[:, 1].max(),
            ]
        )

    # Treatments with k = 12 have the normalized expected profits in column 2
    if treatment in (4, 12):
        return pd.Series(
            [
                exp_profit_df.iloc[order, 2],
                exp_profit_df.iloc[order, 2] / exp_profit_df.iloc[:, 2].max(),
            ]
        )

    # Treatments with k = 18 have the normalized expected profits in column 3
    if treatment in (5, 13):
        return pd.Series(
            [
                exp_profit_df.iloc[order, 3],
                exp_profit_df.iloc[order, 3] / exp_profit_df.iloc[:, 3].max(),
            ]
        )

    # Treatments with k = 30 have the normalized expected profits in column 4
    if treatment in (9, 14):
        return pd.Series(
            [
                exp_profit_df.iloc[order, 4],
                exp_profit_df.iloc[order, 4] / exp_profit_df.iloc[:, 4].max(),
            ]
        )

    return pd.Series([0, 0])


def run_games_howell(avg_metric_df):
    """
    This function computes the Games-Howell post-hoc comparison test. The code is taken from
    Aaron Schlegel's work:
        https://aaronschlegel.me/games-howell-post-hoc-multiple-comparisons-test-python.html
        https://rpubs.com/aaronsc32/games-howell-test

    Args:
        avg_metric_df: DataFrame with the metric (e.g., average orders) and its labels.

    Return:
        A DataFrame with the Games-Howell results.
    """

    main = avg_metric_df.to_numpy()
    alpha = 0.05
    k = len(np.unique(main[:, 0]))

    group_means = dict(npi.group_by(main[:, 0], main[:, 1], np.mean))
    group_obs = dict(npi.group_by(main[:, 0], main[:, 1], len))
    # np.var leads to some very small differences
    group_variance = dict(npi.group_by(main[:, 0], main[:, 1], var))

    combs = list(combinations(np.unique(main[:, 0]), 2))
    group_comps = []
    mean_differences = []
    degrees_freedom = []
    t_values = []
    p_values = []
    std_err = []
    up_conf = []
    low_conf = []

    for comb in combs:
        # Mean differences of each group combination
        diff = group_means[comb[1]] - group_means[comb[0]]

        # t-value of each group combination
        t_val = np.abs(diff) / np.sqrt(
            (group_variance[comb[0]] / group_obs[comb[0]])
            + (group_variance[comb[1]] / group_obs[comb[1]])
        )

        # Numerator of the Welch-Satterthwaite equation
        df_num = (
            group_variance[comb[0]] / group_obs[comb[0]]
            + group_variance[comb[1]] / group_obs[comb[1]]
        ) ** 2

        # Denominator of the Welch-Satterthwaite equation
        df_denom = (group_variance[comb[0]] / group_obs[comb[0]]) ** 2 / (
            group_obs[comb[0]] - 1
        ) + (group_variance[comb[1]] / group_obs[comb[1]]) ** 2 / (
            group_obs[comb[1]] - 1
        )

        # Degrees of freedom
        degrees_of_freedom = df_num / df_denom

        # p-value of the group comparison
        p_val = psturng(t_val * np.sqrt(2), k, degrees_of_freedom)

        # Standard error of each group combination
        standard_error = np.sqrt(
            0.5
            * (
                group_variance[comb[0]] / group_obs[comb[0]]
                + group_variance[comb[1]] / group_obs[comb[1]]
            )
        )

        # Upper and lower confidence intervals
        # '* se' was lacking in the code copied from Aaron's website
        upper_conf = diff + qsturng(1 - alpha, k, degrees_of_freedom) * standard_error
        # '* se' was lacking in the code copied from Aaron's website
        lower_conf = diff - qsturng(1 - alpha, k, degrees_of_freedom) * standard_error

        # Append the computed values to their respective lists
        mean_differences.append(diff)
        degrees_freedom.append(degrees_of_freedom)
        t_values.append(t_val)
        p_values.append(p_val)
        std_err.append(standard_error)
        up_conf.append(upper_conf)
        low_conf.append(lower_conf)
        group_comps.append(str(comb[0]) + " : " + str(comb[1]))

    results_df = pd.DataFrame(
        {
            "group": group_comps,
            "mean_difference": mean_differences,
            "std_error": std_err,
            "t_value": t_values,
            "p_value": p_values,
            "lower_limit": low_conf,
            "upper_limit": up_conf,
        }
    )

    return results_df
