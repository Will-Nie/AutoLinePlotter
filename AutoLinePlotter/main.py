import os
import csv
from tensorboard.backend.event_processing import event_accumulator
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import pandas as pd
from typing import List


def simple_moving_average(interval, windowsize):
    from collections import deque
    window = np.ones(int(windowsize)) / float(windowsize)
    re = deque(np.convolve(interval, window, 'valid'))
    while len(re) < len(interval):
        re.appendleft(interval[0])
    return list(re)


def exponentially_weighted_moving_average(interval, beta, bias=True):
    mean_total = []
    bias_correction = 1
    mean = 0
    for i in range(len(interval)):
        if bias:
            mean = ((beta) * mean + (1 - beta) * interval[i])
            revised_mean = mean / (1 - beta ** (bias_correction))
            mean_total.append(revised_mean)
        else:
            mean = ((beta) * mean + (1 - beta) * interval[i])
            mean_total.append(mean)
        bias_correction += 1
    return mean_total


def x_update_scale_value(temp, position):
    if temp / 1e+6 % 1 == 0:
        result = int(temp // 1e+6)
    else:
        result = temp / 1e+6
    return "{}M".format(result)


def plot(data: list, xlabel: str, ylabel: str, title: str, pth: str = './picture.png'):
    """
    Overview:
        Draw training polyline
    Interface:
        data (:obj:`List[Dict]`): the data we will use to draw polylines
            data[i]['step']: horizontal axis data
            data[i]['value']: vertical axis data
            data[i]['label']: the data label
        xlabel (:obj:`str`): the x label name
        ylabel (:obj:`str`): the y label name
        title (:obj:`str`): the title name
    """
    # sns.set(style="darkgrid", font_scale=1.5)
    sns.set()
    f = plt.figure(figsize=(7, 5.5))
    for nowdata in data:
        step, value, label = nowdata['x'], nowdata['y'], nowdata['label']
        sns.lineplot(x=step, y=value, label=label)

    plt.gca().xaxis.set_major_formatter(FuncFormatter(x_update_scale_value))
    plt.tick_params(axis='both', labelsize=16)
    plt.title(title, fontsize=23)
    plt.legend(loc='upper left', prop={'size': 8}, fontsize=12)
    plt.xlabel(xlabel, fontsize=23)
    plt.ylabel(ylabel, fontsize=23)
    plt.tight_layout()
    f.savefig(pth, bbox_inches='tight')


def plotter(
    root: str,
    titles: List[str],
    labels: List[str],
    x_axes: List[str],
    y_axes: List[str],
    max_x: int = None,
    output_format: str = '.pdf',
    normalise: str = None,
    windowsize=10,
    beta=0.9,
    bias=True,
    plot_together: bool = False,
    plot_together_x_axis: str = None,
    plot_together_y_axis: str = None,
    plot_together_title: str = None,
):
    '''
    root: the location of the folder containing all algorithms data. Each is a folder containing a few seeds of event file generated from TensorBoard
    titles: the titles to be plotted in each diagram; This has no effect in plot_together mode
    labels: the labels for each algorithm
    x_axes: the x-axis for each diagram; This has no effect in plot_together mode
    y_axes: the y-axis for each diagram; This has no effect in plot_together mode
    max_x: the maximum x in x-axis ones wants to plot
    output_format: output format is either .pdf or .png
    normalise: whether to use normalisation (ema or sma) or not
    windowsize: windowsize for sma
    beta: beta for ema
    bias: wether to use bias correction
    plot_together: whether to plot together or not
    plot_together_x_axis: if plot_together, indicates the x axis for the plot
    plot_together_y_axis: if plot_together, indicates the y axis for the plot
    plot_together_title: if plot_together, indicates the title for the plot
    '''

    headers = ['steps', 'value']

    count_file = 0
    data_holder = []  # for plotting together only
    foot_root = root  # for plotting together only
    for root, dirs, _ in os.walk(root):
        if len(dirs) > 1:
            dirs.sort()
        for d in dirs:

            title = titles[count_file]
            label = labels[count_file]
            x_axis = x_axes[count_file]
            y_axis = y_axes[count_file]
            count_file += 1
            exp_path = os.path.join(root, d)
            print(exp_path)
            env, agent = d.split('_')
            print(env, agent)
            results = {}
            for exp_root, _, exp_files in os.walk(exp_path):
                reward_seeds = []
                for exp_i, exp_file in enumerate(exp_files):  # ToDo: offline
                    if ('.csv' in exp_file or '.png' in exp_file or '.pdf' in exp_file):
                        continue
                    try:
                        ea = event_accumulator.EventAccumulator(os.path.join(exp_root, exp_file))
                        ea.Reload()
                        rewards = ea.scalars.Items('evaluator_step/reward_mean')
                        reward_seeds.append(rewards)
                    except:
                        raise Exception("{0} should not be in the directory: {1}".format(exp_file, exp_path))
                dummy = [len(i) for i in reward_seeds]
                max_steps = max([len(i) for i in reward_seeds])
                index = dummy.index(max_steps)
                if max_x is not None and max_x < reward_seeds[index][len(reward_seeds[index]) - 1].step:
                    assert type(max_x) == int, 'max_x should be an integer'
                    result = []
                    for k in range(len(reward_seeds[index])):
                        if reward_seeds[index][k].step <= max_x:
                            result.append(reward_seeds[index][k].step)
                        else:
                            max_steps = k - 1
                            break
                    results['step'] = result
                    for j in range(len(reward_seeds)):
                        max_steps_seed = len(reward_seeds[j])
                        reward_j = []
                        i = 0
                        while i <= max_steps:
                            if i <= max_steps_seed - 1:
                                reward_j.append(reward_seeds[j][i].value)
                                i += 1
                            else:
                                i = max_steps_seed - 1
                                for _ in range(max_steps - max_steps_seed + 1):
                                    reward_j.append(reward_seeds[j][i].value)
                                break
                        if normalise == 'sma':
                            results[j] = simple_moving_average(reward_j, windowsize)
                        elif normalise == 'ema':
                            results[j] = exponentially_weighted_moving_average(reward_j, beta, bias)
                        else:
                            results[j] = reward_j

                else:
                    result = []
                    for i, reward in enumerate(reward_seeds[index]):
                        result.append(reward.step)
                    results['step'] = result
                    for j in range(len(reward_seeds)):
                        reward_j = []
                        for i, reward in enumerate(reward_seeds[j]):
                            reward_j.append(reward.value)
                        while i < max_steps - 1:
                            reward_j.append(reward.value)
                            i += 1
                        i = 0
                        if normalise == 'sma':
                            results[j] = simple_moving_average(reward_j, windowsize=10)
                        elif normalise == 'ema':
                            results[j] = exponentially_weighted_moving_average(reward_j, beta=0.9, bias=True)
                        else:
                            results[j] = reward_j
            steps = results['step'] * (len(results) - 1)
            results.pop('step')
            value = []
            for i in range(len(results)):
                value.extend(results[i])
            if not plot_together:
                sns.set()
                f = plt.figure(figsize=(7, 5.5))
                #figure_lineplot = sns.lineplot(x=steps, y=value, label=label, color='#ad1457')
                #sns.set(style="darkgrid", font_scale=1.5)
                sns.lineplot(x=steps, y=value, label=label)
                plt.gca().xaxis.set_major_formatter(FuncFormatter(x_update_scale_value))
                plt.tick_params(axis='both', labelsize=16)

                plt.title(title, fontsize=23)
                plt.legend(loc='upper left', fontsize=12)
                plt.xlabel(x_axis, fontsize=23)
                plt.ylabel(y_axis, fontsize=23)
                plt.tight_layout()
                #plt.show()
                #figure = figure_lineplot.get_figure()
                f.savefig(exp_path + '/' + title + output_format, bbox_inches='tight')
                plt.close()
            else:
                data_holder.append({'x': steps, 'y': value, 'label': label})
            csv_dicts = []
            for i, _ in enumerate(steps):
                csv_dicts.append({'steps': steps[i], 'value': value[i]})
            with open(os.path.join(exp_path, '{}.csv'.format(d)), 'w', newline='') as f:
                writer = csv.DictWriter(f, headers)
                writer.writeheader()
                writer.writerows(csv_dicts)
    if plot_together:
        assert type(plot_together_x_axis) is str and type(plot_together_y_axis) is str and type(
            plot_together_title
        ) is str, 'Please indicate the x-axis, the y-axis and the title'
        plot(
            data_holder,
            plot_together_x_axis,
            plot_together_y_axis,
            plot_together_title,
            pth=foot_root + foot_root[foot_root.rfind('/'):] + output_format
        )
