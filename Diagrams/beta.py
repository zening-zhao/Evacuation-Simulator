import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data
data = {
    'beta': [0.1, 0.5, 1, 2, 3, 6, 10],
    'average': [259.67, 208.00, 176.00, 195.33, 184.33, 186.67, 189.33]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(df['beta'], df['average'], marker='o', linestyle='-', color='blue', label='Average')

# Labels and title
plt.xlabel('Beta')
plt.ylabel('Evacuation Time (Steps)')
plt.title('Average Evacuation Time Across Different Beta Values')
plt.xticks(np.arange(0, 10.5, 0.5))  # Set x-axis intervals to 0.5
plt.grid(True)

# Highlight the chosen beta value
chosen_beta = 1
plt.axvline(x=chosen_beta, color='red', linestyle='--', label=f'Chosen Beta: {chosen_beta}')

plt.legend()

# Show plot
plt.show()
