from util import load_user_data, task_ID_list_to_check
import pandas as pd
import numpy as np

valid_users, tp_data = load_user_data(folder_name="../anonymized_data", reserved_users=None)
user2condition = tp_data['user2condition']
condition_count = {}
for user in valid_users:
    tp_condition = user2condition[user]
    if tp_condition not in condition_count:
        condition_count[tp_condition] = 0
    condition_count[tp_condition] += 1
print(condition_count)

user_task_confidence_dict = tp_data['confidence']
user_task_order = tp_data['task_order']
all_conditions = ["AP-AE", "AP-UE", "UP-AE", "UP-UE"]
data_long_format = {}
condition_count = {}
for condition in ["planning", "execution"]:
    data_long_format[condition] = {
        "task_index": [],
        "confidence": [],
        "condition": []
    }
task_id_map = {
    'test-149': 1,
    'test-200': 2,
    'test-859': 3,
    'test-388': 4,
    'test-497': 5,
    'test-675': 6
}
for user in valid_users:
    tp_condition = user2condition[user]
    tp_task_order = user_task_order[user]
    for index, task_id in enumerate(tp_task_order):
        confidence_planning = user_task_confidence_dict[user][task_id]["planning"]
        confidence_execution = user_task_confidence_dict[user][task_id]["execution"]

        # data_long_format[tp_condition]["task_index"].append(task_id_map[task_id])
        data_long_format["planning"]["task_index"].append(index + 1)
        data_long_format["planning"]["confidence"].append(confidence_planning)
        data_long_format["planning"]["condition"].append(tp_condition)

        # data_long_format[tp_condition]["task_index"].append(task_id_map[task_id])
        data_long_format["execution"]["task_index"].append(index + 1)
        data_long_format["execution"]["confidence"].append(confidence_execution)
        data_long_format["execution"]["condition"].append(tp_condition)

# color_palette = ['#00d5d9', '#4de8b8', '#a5f48f', '#f9f871']

def color_calc():
    # RGB
    color_tuples = [(199, 160, 133), (252, 240, 225), (251,180,174), (201, 71, 55)]
    # color_tuples = [(229,195,198), (225,233,183), (249,97,97), (188,210,208), (208,183,131)]
    # color_tuples = [(102,194,165), (252,141,98), (141,160,203), (231,138,195), (166,216,84)]
    # color_tuples = [(229,195,198), (225,233,183), (249,97,97), (188,210,208), (208,183,131)]
    float_tuples = []
    for tuple_ in color_tuples:
        tp_tuple = (tuple_[0] / 255.0, tuple_[1] / 255.0, tuple_[2] / 255.0)
        float_tuples.append(tp_tuple)
    return float_tuples

color_palette = ['#ffa57e', '#c4515d', '#7f7ecc', '#8bcb83', '#e5dbce']

import matplotlib.pyplot as plt
import seaborn as sns
def multiplot_new(data_long_format):
    size=24
    params = {'axes.labelsize': size,
                'axes.titlesize': size,
                'xtick.labelsize': size*0.75,
                'ytick.labelsize': size*0.75}
    plt.rcParams.update(params)

    # # print(y_control)
    # # print(y_R)
    fig, axs = plt.subplots(1, 2)
    # # fig1, axs = plt.subplots(ncols=4, nrows=4, constrained_layout=True)

    # axs[0, 0].plot(x, y_control, marker='+')
    # axs[0].plot(x, y_control_1, 'tab:blue')
    # axs[0].plot(x, y_control_2, 'tab:orange')
    df1 = pd.DataFrame(data_long_format["planning"])
    # sns.pointplot(data=df1, x='task_index', y='confidence', hue='Decision', ax=axs[0])
    sns.barplot(data=df1, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[0], palette=color_palette, errwidth=1.0, capsize=.1)
    # sns.pointplot(data=df1, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[0], palette=color_palette, errwidth=1.5, capsize=.1, markers=["o", "s", "*", "d"], linewidth=0, pointsize=10, join=False)
    # sns.boxplot(data=df1, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[0], palette=color_palette)
    axs[0].set_title('Planning')
    axs[0].set_ylim([3.0, 4.8])
    # axs[0].set_ylim([2.0, 5.0])
    # axs[0, 0].plot([10] * 21, np.arange(0.4, 1.24, 0.04), 'tab:brown', linestyle='--')
    # axs[0, 0].set_marker("+")
    # axs[1].plot(x, y_dashboard_1, 'tab:blue')
    # axs[1].plot(x, y_dashboard_2, 'tab:orange')
    df2 = pd.DataFrame(data_long_format["execution"])
    # sns.pointplot(data=df2, x='task_index', y='confidence', hue='Decision', ax=axs[1])
    sns.barplot(data=df2, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[1], palette=color_palette, errwidth=1.0, capsize=.1)
    # sns.pointplot(data=df2, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[1], palette=color_palette, errwidth=1.5, capsize=.1, markers=["o", "s", "*", "d"], linewidth=0, pointsize=10, join=False)
    # sns.boxplot(data=df2, x='task_index', y='confidence', hue='condition', hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], ax=axs[1], palette=color_palette)
    axs[1].set_title('Execution')
    axs[1].set_ylim([3.0, 4.8])
    # axs[1].set_ylim([2.0, 5.0])
    # axs[1].plot([10] * 21, np.arange(0.4, 1.24, 0.04), 'tab:brown', linestyle='--')

    for ax in axs.flat:
        ax.set(xlabel='Tasks', ylabel='Confidence')

    # Hide x labels and tick labels for top plots and y ticks for right plots.
    for ax in axs.flat:
        ax.label_outer()

    # Move legend position
    axs[0].get_legend().remove()
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.subplots_adjust(wspace=0.05, hspace=0)
    plt.show()
    fig.savefig("confidence_planning_execution_barplot.pdf", format='pdf')

multiplot_new(data_long_format)