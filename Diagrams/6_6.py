import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data for 6x6 layout
data_6x6 = {
    'r': [2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 50, 50, 50, 50, 50],
    'theta': [0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5],
    'average': [177.67,
190.00,
196.00,
232.00,
224.33,
177.67,
187.33,
192.33,
239.67,
225.67,
184.33,
189.67,
186.33,
247.00,
236.33,
208.67,
200.67,
203.33,
242.33,
239.33
]
}

# Create a DataFrame
df_6x6 = pd.DataFrame(data_6x6)

# Plot
plt.figure(figsize=(10, 6))
for r_value in df_6x6['r'].unique():
    subset = df_6x6[df_6x6['r'] == r_value]
    plt.plot(subset['theta'], subset['average'], marker='o', linestyle='-', label=f'r = {r_value}')

# Labels and title with larger and bold font
plt.xlabel('Theta', fontsize=16, fontweight='bold')
plt.ylabel('Evacuation Time (Steps)', fontsize=16, fontweight='bold')
plt.title('Average Evacuation Time for 6x6 Layout Subarea Size', fontsize=18, fontweight='bold')

# Set x-axis ticks and grid
plt.xticks(np.arange(0.0, 5.5, 0.5), fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.grid(True)

# Legend with larger font
plt.legend(title='r Values', fontsize=12, title_fontsize=14)

# Show plot
plt.show()
