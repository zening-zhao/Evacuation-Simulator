import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data with actual standard errors from your table
data = {
    'epsilon': [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
    'average': [417.00, 221.67, 176.67, 158.00, 147.00, 148.00, 144.00, 137.67, 140.33, 142.00],
    'std_error': [15.17673658, 6.009252126, 5.364492313,
                  2.516611478, 1, 1.527525232, 1.527525232,
                  0.666666667, 0.881917104, 0.577350269]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Plot with error bars
plt.figure(figsize=(12, 7))
plt.errorbar(df['epsilon'], df['average'], yerr=df['std_error'],
             marker='o', linestyle='-', color='blue', linewidth=2,
             ecolor='gray', elinewidth=3, capsize=8, capthick=3,
             label=r'$\bf{Average\ with\ SE}$')

# Formatting
plt.xlabel(r'$\bf{Epsilon}$', fontsize=20, fontweight='bold')
plt.ylabel(r'$\bf{Evacuation\ Time\ (Steps)}$', fontsize=20, fontweight='bold')
plt.title(r'$\bf{Avarage\ Evacuation\ Time\ Across\ Different\ Epsilon\ Values}$',
          fontsize=20, fontweight='bold')

plt.xticks(np.arange(0, 5.5, 0.5), fontsize=24, fontweight='bold')
plt.yticks(fontsize=24, fontweight='bold')
plt.grid(True, alpha=0.3)

# Highlight chosen epsilon
chosen_epsilon = 2.0
chosen_index = df.index[df['epsilon'] == chosen_epsilon][0]
plt.scatter(chosen_epsilon, df.loc[chosen_index, 'average'],
            s=300, facecolors='none', edgecolors='red', linewidth=2.5,
            zorder=10, label=r'$\bf{Chosen\ \epsilon:\ 2.0}$')

# Adjust y-axis limits to accommodate large error bar at ε=0.1
plt.ylim(100, 500)

# Legend with adjusted position
plt.legend(fontsize=18, loc='upper right', framealpha=0.9)

plt.tight_layout()
plt.show()
