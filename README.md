# Analog Neural Network

A single neuron implemented entirely in transistor-level analog circuitry, simulated in [ngspice](https://ngspice.sourceforge.io/). The neuron computes a weighted sum of two inputs using Gilbert cell analog multipliers, stores weights on capacitors, and performs gradient descent learning through a transistor-level backward path.

## The Idea

Digital neural networks multiply, add, and differentiate using floating-point arithmetic. This project does the same thing with currents and voltages — no ADCs, no DACs, no digital logic. A single neuron computes:

```
V_out = W1 × VIN1 + W2 × VIN2
```

Each multiplication is a Gilbert cell (a cross-coupled BJT differential amplifier pair). Weights are voltages stored on capacitors. The backward path — computing how much each weight should change — uses additional Gilbert cells that multiply the error signal by the input, producing a gradient current that charges or discharges the weight capacitors.

The entire forward and backward path is built from ~40 BJTs, resistors, and capacitors. No op-amps, no digital control.

## Neuron Interface

```
         W1_EXT  W2_EXT
           |       |
    VIN1 --+-------+-- VIN2
           |       |
           | neuron|
           |       |
           +--OUT--+
               |
```

**Subcircuit `neuron`** — ports: `VIN1 VIN2 OUT VCC VEE W1_EXT W2_EXT`

| Port | Direction | Function |
|------|-----------|----------|
| VIN1, VIN2 | Voltage in, gradient current out | Input terminals. Accept ±1V signals. Also source/sink gradient current for upstream weight updates. |
| OUT | Voltage out, error current in | Low-impedance output (~277 Ω). Error from downstream enters as current here. |
| W1_EXT, W2_EXT | Bidirectional | External access to 100 nF weight capacitors for programming and monitoring. |
| VCC, VEE | Power | +5V and −5V rails. |

### Forward Path

Two NPN Gilbert cells (one per input channel) share a PNP current mirror load. Each cell multiplies its input voltage by its weight through a 15:1 resistive divider that keeps the upper quad in the linear region of tanh. The combined differential current converts to a voltage through a transimpedance resistor, then passes through an emitter follower and resistive divider for level shifting.

### Backward Path

Error enters as current at the OUT terminal. A zero-volt sense source (`V_isense`) and CCVS (`H_err`, 1 MΩ transimpedance) convert the error current to an internal voltage: 1 μA of error current produces 1 V of internal error signal. This error voltage drives per-channel gradient cells — each a `bk_mult` Gilbert cell that multiplies the weight by the error, producing a gradient current at the input terminal:

```
I_gradient(VIN_i) ≈ K × W_i × err_v       (K ≈ 1 μA/V²)
```

### Sign Convention

- **Gradient current**: positive = current sinking from upstream output into VIN.
- **Error current**: positive = current flowing into OUT from the external circuit.
- **Weight update**: positive input × positive error → weight increases. This forms a stable negative feedback loop.

## Learning Demonstration

The learning test (`test_learning.spice`) demonstrates the neuron adapting its weights to match a target output voltage. Run it with:

```bash
./run_learning.sh
```

This runs the ngspice simulation and produces two plots.

### learning_test.png

![Learning test results](learning_test.png)

Three panels showing the neuron's behavior over a 5-second simulation across five phases:

| Phase | Time | Description |
|-------|------|-------------|
| Learning | 0–1 s | Target (0.5 V) connected via 100 kΩ. Weights adapt to reduce output error. |
| Hold | 1–2 s | Target disconnected. Output and weights hold steady — capacitors retain learned values. |
| VIN1 ramp | 2–3 s | VIN1 ramps from +0.5 to −0.5 V. Output tracks the change scaled by learned W1. |
| VIN2 ramp | 3–4 s | VIN2 ramps from −0.5 to +0.5 V. Output responds according to learned W2. |
| Hold | 4–5 s | Final steady state with new input configuration. |

- **Top panel**: Output voltage (blue) converging toward the 0.5 V target (red dashed) during the learning phase, then responding to input changes.
- **Middle panel**: Input voltages VIN1 (red) and VIN2 (blue).
- **Bottom panel**: Weight capacitor voltages W1 (red) and W2 (blue) evolving during learning and slowly decaying through bleed resistors afterward.

### learning_current.png

![Error current](learning_current.png)

Error current through the 100 kΩ target resistor. Starts at ~7 μA (large initial error) and decays exponentially as the neuron learns, reaching near zero by disconnect at 1 s.

## Running Tests

```bash
# Individual test groups:
ngspice -b test_forward.spice      # DC operating point, DC sweep, transient
ngspice -b test_backward.spice     # Weight update via bk_mult
ngspice -b test_impedance.spice    # Output impedance
ngspice -b test_gradient.spice     # Chain rule, gradient linearity
ngspice -b test_integration.spice  # Isolation, coexistence, multi-config

# All tests in one file:
ngspice -b neuron_tests.spice
```

## File Structure

| File | Description |
|------|-------------|
| `neuron.spice` | Subcircuit definitions: `bk_mult`, `neuron_ch`, `neuron` |
| `models.spice` | NPN and PNP BJT model definitions |
| `testbench.spice` | Shared testbench (power, weight programming, neuron instance) |
| `test_forward.spice` | Forward path tests (DC op, DC sweep, transient) |
| `test_backward.spice` | Backward path test (weight update) |
| `test_impedance.spice` | Output impedance measurement |
| `test_gradient.spice` | Gradient chain rule and linearity |
| `test_integration.spice` | Channel isolation, forward/backward coexistence |
| `test_learning.spice` | Learning demonstration (gradient descent to target) |
| `plot_learning.py` | Generates plots from learning test output |
| `run_learning.sh` | Runs learning simulation and plotting |
