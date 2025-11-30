import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data for 4x4 layout
data_4x4 = {
    'r': [2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 50, 50, 50, 50, 50],
    'theta': [0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5],
    'average': [285.67, 231.33, 231.33, 238.33, 234.33, 267.67, 222.00, 234.67, 234.67, 233.00,
                271.67, 221.00, 232.67, 234.00, 232.67, 226.33, 221.00, 235.00, 229.00, 232.00]
}

# Create a DataFrame
df_4x4 = pd.DataFrame(data_4x4)

# Plot
plt.figure(figsize=(10, 6))
for r_value in df_4x4['r'].unique():
    subset = df_4x4[df_4x4['r'] == r_value]
    plt.plot(subset['theta'], subset['average'], marker='o', linestyle='-', label=f'r = {r_value}')



# Labels and title with larger and bold font
plt.xlabel('Theta', fontsize=16, fontweight='bold')
plt.ylabel('Evacuation Time (Steps)', fontsize=16, fontweight='bold')
plt.title('Average Evacuation Time for 4x4 Layout Subarea Size', fontsize=18, fontweight='bold')

# Set x-axis ticks and grid
plt.xticks(np.arange(0.0, 5.5, 0.5), fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.grid(True)
# Legend with larger font
plt.legend(title='r Values', fontsize=12, title_fontsize=14)

# Show plot
plt.show()
