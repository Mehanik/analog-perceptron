#!/usr/bin/env python3
"""Plot learning test results from ngspice wrdata output."""

import numpy as np
import matplotlib.pyplot as plt

def load_wrdata(filename):
    """Load ngspice wrdata file. Format: time1 val1 time2 val2 ..."""
    data = np.loadtxt(filename)
    # wrdata repeats time column for each signal: t v1 t v2 t v3 ...
    ncols = data.shape[1]
    nsignals = ncols // 2
    t = data[:, 0]
    signals = [data[:, 2*i+1] for i in range(nsignals)]
    return t, signals

# Load data
t_v, (vout, vin1, vin2) = load_wrdata('learning_vout.txt')
t_w, (w1, w2) = load_wrdata('learning_weights.txt')

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Phase shading helper
def shade_phases(ax):
    ax.axvspan(0, 1, alpha=0.08, color='green', label='_')
    ax.axvspan(1, 2, alpha=0.08, color='gray', label='_')
    ax.axvspan(2, 3, alpha=0.08, color='blue', label='_')
    ax.axvspan(3, 4, alpha=0.08, color='orange', label='_')
    ax.axvspan(4, 5, alpha=0.08, color='gray', label='_')

# Plot 1: Output voltage
ax = axes[0]
shade_phases(ax)
ax.plot(t_v, vout, 'b-', linewidth=1.5, label='V(out)')
ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='Target (0.5V)')
ax.axvline(x=1, color='k', linestyle=':', alpha=0.3)
ax.set_ylabel('Voltage (V)')
ax.set_title('Learning Test — Output Voltage')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.text(0.5, -0.8, 'Learning\n(connected)', ha='center', fontsize=8, color='green')
ax.text(1.5, -0.8, 'Hold\n(disconnected)', ha='center', fontsize=8, color='gray')
ax.text(2.5, -0.8, 'VIN1\nramp', ha='center', fontsize=8, color='blue')
ax.text(3.5, -0.8, 'VIN2\nramp', ha='center', fontsize=8, color='orange')
ax.text(4.5, -0.8, 'Hold', ha='center', fontsize=8, color='gray')

# Plot 2: Input voltages
ax = axes[1]
shade_phases(ax)
ax.plot(t_v, vin1, 'r-', linewidth=1.5, label='VIN1')
ax.plot(t_v, vin2, 'b-', linewidth=1.5, label='VIN2')
ax.set_ylabel('Voltage (V)')
ax.set_title('Input Voltages')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

# Plot 3: Weight capacitor voltages
ax = axes[2]
shade_phases(ax)
ax.plot(t_w, w1, 'r-', linewidth=1.5, label='W1')
ax.plot(t_w, w2, 'b-', linewidth=1.5, label='W2')
ax.axhline(y=0.3, color='gray', linestyle=':', alpha=0.5, label='Initial (0.3V)')
ax.set_ylabel('Voltage (V)')
ax.set_xlabel('Time (s)')
ax.set_title('Weight Capacitor Voltages')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('learning_test.png', dpi=150, bbox_inches='tight')
print("Saved learning_test.png")
plt.close()

# Error current through 100k: I = sw * (0.5 - Vout) / 100k
t_sw, (sw,) = load_wrdata('learning_sw.txt')
# Interpolate sw onto vout time base
sw_interp = np.interp(t_v, t_sw, sw)
i_target = sw_interp * (0.5 - vout) / 100e3

fig2, ax2 = plt.subplots(figsize=(12, 4))
shade_phases(ax2)
ax2.plot(t_v, i_target * 1e6, 'g-', linewidth=1.5)
ax2.set_ylabel('Current (μA)')
ax2.set_xlabel('Time (s)')
ax2.set_title('Error Current through 100k Resistor')
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('learning_current.png', dpi=150, bbox_inches='tight')
print("Saved learning_current.png")
plt.close()
