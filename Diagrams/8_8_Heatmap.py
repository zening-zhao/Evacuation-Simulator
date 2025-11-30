import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import seaborn as sns

# Data preparation
data = {
    'subarea': ['7*7'] * 20 + ['6*6'] * 20 + ['5*5'] * 20 + ['4*4'] * 20,
    'r': [2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 50, 50, 50, 50, 50] * 4,
    'theta': [0.1, 0.5, 1, 2, 5] * 4 * 4,
    'average': [
        200.33, 200.00, 223.67, 242.67, 240.67, 198.67, 191.00, 216.00, 238.67, 241.33,
        196.00, 192.67, 212.67, 234.67, 243.67, 200.33, 210.00, 217.00, 240.00, 240.00,
        177.67, 190.00, 196.00, 232.00, 224.33, 177.67, 187.33, 192.33, 239.67, 225.67,
        184.33, 189.67, 186.33, 247.00, 236.33, 208.67, 200.67, 203.33, 242.33, 239.33,
        237.00, 229.67, 257.67, 269.33, 281.33, 234.00, 221.67, 248.00, 279.33, 285.67,
        226.00, 226.33, 234.00, 273.67, 281.33, 236.67, 231.67, 245.67, 273.33, 280.00,
        285.67, 231.33, 231.33, 238.33, 234.33, 267.67, 222.00, 234.67, 234.67, 233.00,
        271.67, 221.00, 232.67, 234.00, 232.67, 226.33, 221.00, 235.00, 229.00, 232.00
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Create a pivot table for the heatmap
pivot = df.pivot_table(index='subarea', columns='theta', values='average')

# Plot heatmap
plt.figure(figsize=(12, 8))
ax = sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".2f", cbar_kws={'label': 'Average Value'}, square=True,
                 annot_kws={"size": 12, "weight": "bold"}, linewidths=0.5)

# Set title and labels with larger, bold font
plt.title('Average Evacuation Time for Different Subarea Sizes and Theta Combinations', fontsize=14, fontweight='bold')
plt.xlabel('Theta', fontsize=14, fontweight='bold')
plt.ylabel('Subarea Size', fontsize=14, fontweight='bold')

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

# Highlight the row for subarea 6x6
subarea_row = pivot.index.get_loc('6*6')
rect_subarea = patches.FancyBboxPatch((0.2, subarea_row), len(pivot.columns) - 0.4, 1, boxstyle="round,pad=0.1", edgecolor='red', linewidth=4, facecolor='none')
plt.gca().add_patch(rect_subarea)

plt.tight_layout()
plt.show()
