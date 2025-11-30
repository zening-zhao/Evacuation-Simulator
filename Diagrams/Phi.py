

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data
data = {
    'phi': [0.5, 1, 1.5, 2, 3, 4, 5],
    'average': [220.00, 156.00, 144.67, 141.67, 139.67, 139.67, 137.00],
    'std_error' : [5.507570547,
1.527525232,
2.40370085,
0.666666667,
0.881917104,
0.666666667,
0.577350269]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Plot with error bars
plt.figure(figsize=(12, 7))
plt.errorbar(df['phi'], df['average'], yerr=df['std_error'],
             marker='o', linestyle='-', color='blue', linewidth=2,
             ecolor='gray', elinewidth=3, capsize=8, capthick=3,
             label=r'$\bf{Average\ with\ SE}$')

# Formatting
plt.xlabel(r'$\bf{Phi}$', fontsize=20, fontweight='bold')
plt.ylabel(r'$\bf{Evacuation\ Time\ (Steps)}$', fontsize=20, fontweight='bold')
plt.title(r'$\bf{Avarage\ Evacuation\ Time\ Across\ Different\ Phi\ Values}$',
          fontsize=20, fontweight='bold')


# Set x-axis ticks and grid with bold fonts
plt.xticks(np.arange(0, 5.5, 0.5), fontsize=20, fontweight='bold')
plt.yticks(fontsize=20, fontweight='bold')
plt.grid(True)


# Highlight chosen epsilon
chosen_phi = 1.0
chosen_index = df.index[df['phi'] == chosen_phi][0]
plt.scatter(chosen_phi, df.loc[chosen_index, 'average'],
            s=300, facecolors='none', edgecolors='red', linewidth=2.5,
            zorder=10, label=r'$\bf{Chosen\ \Phi:\ 1.0}$')

# Adjust y-axis limits to accommodate large error bar at ε=0.1
# plt.ylim(100, 500)
# Legend with adjusted position
plt.legend(fontsize=18, loc='upper right', framealpha=0.9)

plt.tight_layout()
plt.show()

