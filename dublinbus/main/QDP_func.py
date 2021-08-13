import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from statistics import variance
from scipy.stats import lognorm


# code adapted from https://gist.github.com/tupui/c8dd181fd1e732584bbd7109b96177e3

# function to plot quantile dot plot given the normalised data and model prediction
def quantile_dotplot(lineid, normdata, pred):
    sample = 20
    p_less_than_x = np.linspace(1 / sample / 2, 1 - (1 / sample / 2), sample)

    # scaling up the data and shifting it with the prediction
    preddata = []
    for i in normdata:
        preddata += [i * pred + pred]

    # getting standard deviation and mean of the new data
    stdev = variance(preddata) ** 0.5
    sum = 0
    for j in preddata:
        sum += j
    mean = sum / len(preddata)

    # probability density function
    pdf = lognorm.pdf

    # applying the inverse CDF to our new data
    x2 = np.percentile(preddata, p_less_than_x * 100)  # Inverce CDF (ppf)

    # Create bins
    n_bins = 7
    hist = np.histogram(x2, bins=n_bins)
    bins, edges = hist
    radius = (edges[1] - edges[0]) / 2

    fig, ax = plt.subplots()
    ax.set_xlabel("Minutes")

    # Dotplot
    ax2 = ax.twinx()
    patches = []
    max_y = 0
    max_len = 0
    for i in range(n_bins):
        x_bin = (edges[i + 1] + edges[i]) / 2
        y_bins = [(i + 1) * (radius * 2) for i in range(bins[i])]

        # if y_bins is empty, continue
        if not y_bins:
            continue

        if len(y_bins) > max_len:
            max_len = len(y_bins)

        max_y = max(y_bins) if max(y_bins) > max_y else max_y

        for _, y_bin in enumerate(y_bins):
            circle = Circle((x_bin, y_bin), radius)
            patches.append(circle)

    # putting the circles together, setting colour
    p = PatchCollection(patches, alpha=0.4)
    p.set_facecolor("royalblue")
    ax2.add_collection(p)

    # dictionary for scale factors
    scale_dict = {
        "68": 1.6,
        "45A": 1.4,
        "25A": 1.5,
        "14": 1.7,
        "77A": 1.25,
        "39": 1.4,
        "16": 1.2,
        "40D": 1.2,
        "27B": 1.35,
        "142": 1.1,
        "83": 1.3,
        "130": 1,
        "15": 1.6,
        "46A": 1.3,
        "33": 1.4,
        "7": 1.5,
        "39A": 1.5,
        "1": 1.3,
        "41": 1.2,
        "67X": 1.1,
        "59": 1.3,
        "9": 1.5,
        "40": 1.6,
        "239": 1.6,
        "84": 1.1,
        "53": 1.1,
        "185": 0.7,
        "151": 1.3,
        "13": 1.35,
        "15B": 1.3,
        "65B": 1.1,
        "29A": 1.6,
        "61": 1,
        "140": 7.2,
        "123": 1.3,
        "79A": 1,
        "38A": 1.5,
        "31": 1,
        "69": 1.35,
        "44": 1.6,
        "42": 2.2,
        "67": 1.3,
        "184": 1.4,
        "238": 1,
        "145": 1.45,
        "17A": 1.6,
        "32": 1.5,
        "27A": 1.3,
        "17": 1.4,
        "27X": 1.5,
        "122": 1.45,
        "54A": 1.3,
        "66": 1.6,
        "150": 1.2,
        "56A": 1.3,
        "37": 1.5,
        "27": 1.6,
        "15A": 1,
        "65": 1.3,
        "47": 1.6,
        "76": 1.45,
        "79": 1.15,
        "83A": 1.4,
        "63": 1.5,
        "33B": 0.9,
        "4": 1.35,
        "120": 1.6,
        "41C": 1.45,
        "70": 1.2,
        "84A": 1.5,
        "220": 1.45,
        "32X": 1.45,
        "68A": 1,
        "84X": 0.7,
        "38": 1.35,
        "102": 1.6,
        "270": 1.4,
        "51X": 1,
        "33X": 1.6,
        "75": 1.35,
        "26": 1.5,
        "66A": 1.3,
        "31A": 1,
        "49": 1.2,
        "111": 0.8,
        "18": 1.3,
        "11": 1.5,
        "14C": 1.4,
        "114": 1.4,
        "76A": 1.1,
        "44B": 1.5,
        "7A": 1.6,
        "43": 1.3,
        "25": 1.6,
        "104": 1.6,
        "33A": 1.1,
        "16C": 1.3,
        "42D": 1.1,
        "31B": 0.8,
        "66X": 1,
        "31D": 1.6,
        "33D": 1.6,
        "39X": 1.7,
        "41B": 1.45,
        "25B": 1.2,
        "7D": 1.4,
        "46E": 1.6,
        "118": 0.8,
        "51D": 1.8,
        "15D": 1.4,
        "41A": 1.6,
        "25D": 1.1,
        "38D": 1.2,
        "40B": 1.6,
        "66B": 1.4,
        "38B": 1.6,
        "236": 0.7,
        "7B": 1.45,
        "41X": 0.8,
        "40E": 1.4,
        "161": 1,
        "70D": 1.4,
        "69X": 1.6,
        "116": 1.6,
        "77X": 1.6,
        "25X": 1.6,
        "68X": 1.5,
        "16D": 1.4,
        "33E": 1.5,
        "41D": 2.3,
    }

    scale = scale_dict[lineid]

    # dictionary for the shift factor
    shift_dict = {
        "68": 0.08,
        "45A": -0.1,
        "25A": -0.02,
        "14": 0.06,
        "77A": -0.15,
        "39": 0.05,
        "16": -0.15,
        "40D": -0.2,
        "27B": -0.1,
        "142": -0.22,
        "83": -0.05,
        "130": -0.35,
        "15": 0,
        "46A": -0.05,
        "33": 0.02,
        "7": 0.02,
        "39A": 0.02,
        "1": -0.2,
        "41": -0.1,
        "67X": -0.3,
        "59": -0.17,
        "9": 0,
        "40": 0,
        "239": 0.05,
        "84": -0.15,
        "53": -0.12,
        "185": -0.45,
        "151": -0.07,
        "13": -0.07,
        "15B": 0,
        "65B": -0.1,
        "29A": 0.02,
        "61": -0.11,
        "140": 0.57,
        "123": -0.06,
        "79A": -0.2,
        "38A": 0,
        "31": 0,
        "69": 0.03,
        "44": -0.02,
        "42": 0.22,
        "67": 0,
        "184": -0.1,
        "238": -0.23,
        "145": -0.02,
        "17A": 0.1,
        "32": 0,
        "27A": -0.1,
        "17": 0,
        "27X": -0.1,
        "122": 0,
        "54A": -0.13,
        "66": 0.02,
        "150": 0,
        "56A": 0,
        "37": 0.05,
        "27": 0,
        "15A": 0,
        "65": 0,
        "47": 0.03,
        "76": 0.05,
        "79": -0.1,
        "83A": -0.2,
        "63": 0,
        "33B": 0,
        "4": -0.03,
        "120": 0,
        "41C": 0.03,
        "70": -0.03,
        "84A": 0.01,
        "220": -0.04,
        "32X": -0.08,
        "68A": -0.16,
        "84X": -0.7,
        "38": 0,
        "102": 0.1,
        "270": 0.05,
        "51X": -0.23,
        "33X": 0.06,
        "75": -0.1,
        "26": 0,
        "66A": 0,
        "31A": -0.25,
        "49": -0.1,
        "111": -0.4,
        "18": -0.1,
        "11": 0,
        "14C": -0.18,
        "114": -0.16,
        "76A": -0.27,
        "44B": -0.1,
        "7A": 0.05,
        "43": -0.15,
        "25": 0.07,
        "104": 0,
        "33A": -0.25,
        "16C": 0,
        "42D": -0.15,
        "31B": -0.6,
        "66X": -0.3,
        "31D": 0,
        "33D": 0,
        "39X": 0.03,
        "41B": 0,
        "25B": -0.15,
        "7D": -0.1,
        "46E": 0,
        "118": -0.65,
        "51D": 0.02,
        "15D": -0.18,
        "41A": -0.04,
        "25D": -0.07,
        "38D": -0.22,
        "40B": 0.1,
        "66B": -0.13,
        "38B": 0,
        "236": -0.8,
        "7B": -0.03,
        "41X": -0.5,
        "40E": -0.12,
        "161": 0,
        "70D": -0.1,
        "69X": -0.02,
        "116": 0.07,
        "77X": -0.07,
        "25X": -0.02,
        "68X": -0.12,
        "16D": -0.15,
        "33E": -0.1,
        "41D": 0.25,
    }

    shift = shift_dict[lineid]

    # window size the same as a normal distribution with the same data, scale determines window size, shift determines
    # where it looks
    x1 = np.linspace(
        (mean - 3 * stdev) / scale + 0.45 * pred + shift * pred,
        (mean + 3 * stdev) / scale + 0.45 * pred + shift * pred,
        100,
    )

    # Axis tweak
    # arguments for lognorm function
    args = {"s": 0.2, "scale": 11.4}
    y_scale = (max_y + radius) / max(pdf(x1, **args))
    ticks_y = ticker.FuncFormatter(lambda x1, pos: "{0:g}".format(x1 / y_scale))
    ax2.yaxis.set_major_formatter(ticks_y)
    ax2.set_yticklabels([])
    ax2.set_xlim([min(x1) - radius, max(x1) + radius])
    ax2.set_ylim([0, max_y + radius])
    ax2.set_aspect(1)

    # turn off y ticks
    plt.yticks([])
    ax.yaxis.set_major_locator(plt.NullLocator())

    # adding more x ticks
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))

    # adding vertical line for the mean
    plt.axvline(x=pred, color="r")

    # showing the plot in the interface (won't work like this in the app)
    plt.savefig("QDTtest.png")


# testing the function (line 39A, prediction of 40.5)
lineid = "39A"
linedist = pd.read_csv("knn_dist_csvs/knn_dist_{}".format(lineid), header=None)
quantile_dotplot(lineid, linedist[0].to_list(), 40.5)
