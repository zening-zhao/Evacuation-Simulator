import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import seaborn as sns

# Data preparation
data = {
    'L': [29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29,
          34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34, 34,
          41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41],
    'r': [2, 2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15, 15, 15, 20, 20, 20, 20, 20, 20, 40, 40, 40, 40, 40, 40,
          2, 2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15, 15, 15, 20, 20, 20, 20, 20, 20, 40, 40, 40, 40, 40, 40,
          2, 2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 10, 15, 15, 15, 15, 15, 15, 20, 20, 20, 20, 20, 20, 40, 40, 40, 40, 40, 40],
    'theta': [0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10,
              0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10,
              0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10, 0.1, 0.5, 1, 2, 5, 10],
    'average': [565.67, 578.33, 745, 708.67, 750.67, 757.33, 564, 609.33, 751, 707.33, 748, 747.67, 553, 583, 719.67, 750.67, 751, 747.67, 574.67, 580.33, 739.33, 752.33, 720.33, 742.67, 548.33, 623, 746.67, 712.33, 750.67, 752.67,
                541.33, 540.33, 551, 538, 545.33, 546.67, 548, 537, 554, 535, 542.67, 545.33, 537.33, 541.33, 551, 539.67, 548.67, 541.67, 551, 551.67, 548.67, 546, 538.33, 536.33, 537.33, 548.67, 540.67, 543, 533.67, 548.33,
                637.33, 656, 800.33, 812.67, 771.33, 802.33, 625.67, 678, 802.67, 807.33, 800, 761.67, 645, 706.33, 785.33, 774.67, 778.67, 788.67, 650.33, 725.33, 747.67, 770.33, 803.33, 786, 627, 682.67, 801.33, 807.33, 800.67, 811.33]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Convert L to layout size
df['layout_size'] = df['L'].apply(lambda x: f"{round(200/x)}x{round(200/x)}")

# Create a pivot table for the heatmap
pivot = df.pivot_table(index='layout_size', columns='theta', values='average')

# Plot heatmap
plt.figure(figsize=(12, 6))
ax = sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".2f", cbar_kws={'label': 'Average Value'}, square=True,
                 annot_kws={"size": 12, "weight": "bold"}, linewidths=0.5)

# Set title and labels with larger, bold font
plt.title('Average Evacuation Time for Different Subarea Size and Theta Combinations', fontsize=14, fontweight='bold')
plt.xlabel('Theta', fontsize=14, fontweight='bold')
plt.ylabel('Sub Area Size', fontsize=14, fontweight='bold')

# Set tick labels with larger, bold font
plt.xticks(fontsize=12, fontweight='bold')
plt.yticks(fontsize=12, fontweight='bold')

# Set color bar label and tick labels with larger, bold font
cbar = ax.collections[0].colorbar
cbar.ax.yaxis.set_label_position('right')
cbar.ax.set_ylabel('Average Evacuation Time', fontsize=14, fontweight='bold')
cbar.ax.tick_params(labelsize=12)
for label in cbar.ax.get_yticklabels():
    label.set_fontweight('bold')

# Highlight the column for theta = 0.5
theta_col = pivot.columns.get_loc(0.5)
rect_theta = patches.FancyBboxPatch((theta_col, 0.2), 1, len(pivot) - 0.4, boxstyle="round,pad=0.1", edgecolor='red', linewidth=4, facecolor='none')
plt.gca().add_patch(rect_theta)

# Highlight the row for L = 34
L_row = pivot.index.get_loc('6x6')
rect_L = patches.FancyBboxPatch((0.2, L_row), len(pivot.columns) - 0.4, 1, boxstyle="round,pad=0.1", edgecolor='red', linewidth=4, facecolor='none')
plt.gca().add_patch(rect_L)

plt.tight_layout()
plt.show()
