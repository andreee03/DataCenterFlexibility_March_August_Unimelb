
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append(r"C:\Users\andre\UniMelb")

import TOOL_scientific_plots 

# Define the function R² -> R
def f(T_e, T_c):
    return 0.25211 + 0.013241*T_e - 0.0086373*T_e**2 + 0.085811*T_c - 0.0042612*T_c**2 + 0.0086619*T_e*T_c




# Select a finite region of R² to display
x = np.linspace(10, 25, 200)
y = np.linspace(15, 30, 200)

# Construct every (x, y) combination
X, Y = np.meshgrid(x, y)

# Evaluate the function on the grid
Z = f(X, Y)

# Create the figure
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Plot the surface
surface = ax.plot_surface(
    X,
    Y,
    Z,
    cmap="viridis",
    edgecolor="none"
)

# Axis labels
ax.set_xlabel("Temperature of the evaporator water")
ax.set_ylabel("Temperature of the condensor water")
ax.set_zlabel("CAPFT(T_e, T_c)")
ax.set_title("Vizualisation of the CAPFT")

# Add the colour scale
fig.colorbar(surface, ax=ax, shrink=0.6, label="CAPFT(T_e, T_c)")

plt.tight_layout()
plt.show()

