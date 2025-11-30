import matplotlib.pyplot as plt
import numpy as np

# Data
densities = np.arange(10000, 12501, 100)
exp_avg = [737, 742, 753, 761, 768, 778, 783, 788, 798, 803, 809, 817, 822, 831, 836, 840, 848, 856, 863, 867, 875, 881, 887, 892, 900, 906]
shortest_avg = [758, 761, 767, 769, 772, 779, 780, 784, 789, 795, 798, 804, 806, 808, 813, 814, 817, 823, 827, 834, 839, 843, 850, 854, 861, 872]

# Set global font settings to bold
plt.rcParams.update({'font.weight': 'bold'})

plt.figure(figsize=(12, 6))
plt.plot(densities, exp_avg, marker='o', label=r'$\bf{With\ Exit\ Guidance}$',
         color='#ff7f0e', linewidth=4)  # Make label bold
plt.plot(densities, shortest_avg, marker='s', label=r'$\bf{Without\ Exit\ Guidance}$',
         color='#1f77b4', linewidth=4)  # Make label bold

# Labels and title with bold and larger font
plt.title(r'$\bf{Evacuation\ Time\ Comparison: \ With\ Exit\ Guidance\ vs.\ Without\ Exit\ Choice\ Guidance}$',
          fontsize=16, fontweight='bold')
plt.xlabel(r'$\bf{Number\ of\ Pedestrian}$', fontsize=18, fontweight='bold')
plt.ylabel(r'$\bf{Average\ Evacuation\ Time\ (Steps)}$', fontsize=18, fontweight='bold')

# Set x-axis ticks and grid with all text bold
plt.xticks(np.arange(10000, 12501, 500), fontsize=16, fontweight='bold')
plt.yticks(fontsize=16, fontweight='bold')
plt.grid(True, linestyle='--', alpha=0.7)

# Legend with all text bold
plt.legend(fontsize=14, title_fontsize=16, frameon=True)

# Show plot
plt.show()
