

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data
data = {
    'delta': [0.5, 1, 1.5, 2, 3, 4, 5],
    'average': [
177.67,
176.67,
184.00,
189.00,
192.00,
188.33,
188.33],
    'std_error' : [
2.185812841,
0.881917104,
2.081665999,
0.577350269,
2.309401077,
0.666666667,
2.728450924]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Plot with error bars
plt.figure(figsize=(12, 7))
plt.errorbar(df['delta'], df['average'], yerr=df['std_error'],
             marker='o', linestyle='-', color='blue', linewidth=2,
             ecolor='gray', elinewidth=3, capsize=8, capthick=3,
             label=r'$\bf{Average\ with\ SE}$')

# Formatting
plt.xlabel(r'$\bf{Delta}$', fontsize=20, fontweight='bold')
plt.ylabel(r'$\bf{Evacuation\ Time\ (Steps)}$', fontsize=20, fontweight='bold')
plt.title(r'$\bf{Avarage\ Evacuation\ Time\ Across\ Different\ Delta\ Values}$',
          fontsize=20, fontweight='bold')


# Set x-axis ticks and grid with bold fonts
plt.xticks(np.arange(0, 5.5, 0.5), fontsize=20, fontweight='bold')
plt.yticks(fontsize=20, fontweight='bold')
plt.grid(True)


# Highlight chosen epsilon
chosen_phi = 1.0
chosen_index = df.index[df['delta'] == chosen_phi][0]
plt.scatter(chosen_phi, df.loc[chosen_index, 'average'],
            s=300, facecolors='none', edgecolors='red', linewidth=2.5,
            zorder=10, label=r'$\bf{Chosen\ \Delta:\ 1.0}$')

# Adjust y-axis limits to accommodate large error bar at ε=0.1
# plt.ylim(100, 500)
# Legend with adjusted position
plt.legend(fontsize=18, loc='lower right', framealpha=0.9)

plt.tight_layout()
plt.show()

