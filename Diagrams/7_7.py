import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data for 6x6 layout
data_7x7 = {
    'r': [2, 2, 2, 2, 2, 10, 10, 10, 10, 10, 20, 20, 20, 20, 20, 50, 50, 50, 50, 50],
    'theta': [0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5, 0.1, 0.5, 1, 2, 5],
    'average': [200.333333333333,
200,
223.666666666667,
242.666666666667,
240.666666666667,
198.666666666667,
191,
216,
238.666666666667,
241.333333333333,
196,
192.666666666667,
212.666666666667,
234.666666666667,
243.666666666667,
200.333333333333,
210,
217,
240,
240
]
}

# Create a DataFrame
df_7x7 = pd.DataFrame(data_7x7)

# Plot
plt.figure(figsize=(10, 6))
for r_value in df_7x7['r'].unique():
    subset = df_7x7[df_7x7['r'] == r_value]
    plt.plot(subset['theta'], subset['average'], marker='o', linestyle='-', label=f'r = {r_value}')

# Labels and title with larger and bold font
plt.xlabel('Theta', fontsize=16, fontweight='bold')
plt.ylabel('Evacuation Time (Steps)', fontsize=16, fontweight='bold')
plt.title('Average Evacuation Time for 7x7 Layout Subarea Size', fontsize=18, fontweight='bold')

# Set x-axis ticks and grid
plt.xticks(np.arange(0.0, 5.5, 0.5), fontsize=14, fontweight='bold')
plt.yticks(fontsize=14, fontweight='bold')
plt.grid(True)

# Legend with larger font
plt.legend(title='r Values', fontsize=12, title_fontsize=14)

# Show plot
plt.show()
