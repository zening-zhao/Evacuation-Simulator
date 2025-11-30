import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data for 5x5 layout
data_5x5 = {
    'r': [2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 50, 50, 50, 50, 50],
    'theta': [0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5],
    'average': [237.00, 229.67, 257.67, 269.33, 281.33, 234.00, 221.67, 248.00, 279.33, 285.67,
                226.00, 226.33, 234.00, 273.67, 281.33, 236.67, 231.67, 245.67, 273.33, 280.00]
}

# Create a DataFrame
df_5x5 = pd.DataFrame(data_5x5)

# Plot
plt.figure(figsize=(10, 6))
for r_value in df_5x5['r'].unique():
    subset = df_5x5[df_5x5['r'] == r_value]
    plt.plot(subset['theta'], subset['average'], marker='o', linestyle='-', label=f'r = {r_value}')

# Labels and title with larger and bold font
plt.xlabel('Theta', fontsize=16, fontweight='bold')
plt.ylabel('Evacuation Time (Steps)', fontsize=16, fontweight='bold')
plt.title('Average Evacuation Time for 5x5 Layout Subarea Size', fontsize=18, fontweight='bold')

# Set x-axis ticks and grid
plt.xticks(np.arange(0.0, 5.5, 0.5), fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.grid(True)

# Legend with larger font
plt.legend(title='r Values', fontsize=12, title_fontsize=14)

# Show plot
plt.show()
