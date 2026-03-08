#!/bin/bash
# Run learning test simulation and plot results
set -e
cd "$(dirname "$0")"

ngspice -b test_learning.spice
.venv/bin/python3 plot_learning.py
