from util import load_user_data, task_ID_list_to_check
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

valid_users, tp_data = load_user_data(folder_name="../anonymized_data", reserved_users=None)
user2condition = tp_data['user2condition']
user_planning_actions = tp_data['user_planning_actions']
condition_count = {}
for user in valid_users:
    tp_condition = user2condition[user]
    if tp_condition not in condition_count:
        condition_count[tp_condition] = 0
    condition_count[tp_condition] += 1
print(condition_count)

user_cognitive_load = tp_data['cognitive_load']
nasatlx_variable_names = ["mental_demand", "physical_demand", "temporal_demand", "performance", "effort", "frustration"]
name_map = {
    "mental_demand": "Mental\nDemand",
    "physical_demand": "Physical\nDemand",
    "temporal_demand": "Temporal\nDemand",
    "performance": "Performance",
    "effort": "Effort",
    "frustration": "Frustration",
}
data_long_format = {
    "condition": [],
    "measure": [],
    "value": []
}
for user in valid_users:
    for variable in nasatlx_variable_names:
        data_long_format["condition"].append(user2condition[user])
        data_long_format["measure"].append(name_map[variable])
        data_long_format["value"].append(user_cognitive_load[user][variable])
# data = [loan_data_variables["Numeracy_level"], loan_data_variables["ATI"], loan_data_variables["TiA-Propensity to Trust"], loan_data_variables["TiA-Familiarity"], loan_data_variables["Analogy_domain_familiarity"]]
# data = [loan_data_variables["Numeracy_level"], loan_data_variables["ATI"], loan_data_variables["TiA-Propensity to Trust"], loan_data_variables["TiA-Familiarity"]]
df = pd.DataFrame(data_long_format, dtype=float)

from statannotations.Annotator import Annotator
pairs = []
pairs.append(((name_map["mental_demand"], "AP-AE"), (name_map["mental_demand"], "UP-UE")))
pairs.append(((name_map["temporal_demand"], "AP-UE"), (name_map["temporal_demand"], "UP-UE")))
pairs.append(((name_map["performance"], "AP-AE"), (name_map["performance"], "AP-UE")))
pairs.append(((name_map["performance"], "AP-AE"), (name_map["performance"], "UP-UE")))
pairs.append(((name_map["effort"], "AP-AE"), (name_map["effort"], "UP-UE")))
pairs.append(((name_map["frustration"], "AP-AE"), (name_map["frustration"], "UP-AE")))
pairs.append(((name_map["frustration"], "AP-AE"), (name_map["frustration"], "UP-UE")))
pairs.append(((name_map["frustration"], "AP-UE"), (name_map["frustration"], "UP-UE")))
pvalues = [0.01, 0.5]

# print(df.isnull().sum())
# print(df)
size=24
params = {'axes.labelsize': size,
            'axes.titlesize': size,
            'xtick.labelsize': size*0.75,
            'ytick.labelsize': size*0.75}
plt.rcParams.update(params)
sns.set_theme(style="whitegrid")
# tips = sns.load_dataset("tips")
# print(type(tips))
# print(df)
# print(type(df))
# print(len(data[0]), len(data[1]), len(data[2]), len(data[3]))
fig = plt.gcf()
color_palette = ['#ffa57e', '#c4515d', '#7f7ecc', '#8bcb83', '#e5dbce']

ax = sns.barplot(data=df, x="measure", y="value", hue="condition", hue_order=['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE'], palette=color_palette)


plotting_parameters = {
    'data':    df,
    'x':       'measure',
    'y':       'value',
    # 'order':   nasatlx_variable_names,
    "hue": "condition",
    "hue_order": ['AP-AE', 'AP-UE', 'UP-AE', 'UP-UE']
}
# pvalue_thresholds = [[1e-4, "****"], [0.05 / 3, "**"], [0.05, "*"], [1, ""]]
pvalue_thresholds = [[0.05 / 4, "**"], [0.05, "*"], [1, ""]]
annotator = Annotator(ax, pairs, **plotting_parameters)
# annotator.set_pvalues(pvalues)
annotator.configure(test='Mann-Whitney', verbose=2, pvalue_thresholds=pvalue_thresholds)
annotator.apply_test()
annotator.annotate()



ax.tick_params(labelsize=13)
ax.set_xlabel("Cognitive Load", fontsize = 24)
ax.set_ylabel("Value", fontsize = 24)
plt.show()
fig.savefig("cognitive_load_bar_plot_new.pdf", format='pdf')