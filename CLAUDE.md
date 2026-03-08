# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Analog neural network implemented as an ngspice circuit. A single neuron computes `V_out = W1*Vin1 + W2*Vin2` using Gilbert cell analog multipliers, with capacitor-based weight storage and a transistor-level backward path for gradient descent learning.

## File Structure

- `models.spice` — NPN_AN and PNP_AN BJT model definitions
- `neuron.spice` — Subcircuit definitions: `bk_mult`, `bk_mult_ac`, `neuron`
- `testbench.spice` — Shared testbench (power, weight programming, neuron instance)
- `test_forward.spice` — Tests 1-3 (DC op, DC sweep, transient)
- `test_backward.spice` — Test 4 (weight update via bk_mult_ac)
- `test_impedance.spice` — Test 5 (output impedance)
- `test_gradient.spice` — Tests 6-7 (chain rule, gradient linearity)
- `test_integration.spice` — Tests 8-10 (isolation, coexistence, multi-config)
- `neuron_tests.spice` — All 10 tests in one file (gradient tests less accurate due to VIN loading from weight update cells)
- `test_bk_mult.spice` — Standalone bk_mult characterization
- `test_bk_opt.spice` — Validates bk_mult/bk_mult_ac optimization (EF+divider removal)
- `test_bias_sharing.spice` — Validates shared w_bias/tail_ref between forward and backward paths
- `test_ref3_sharing.spice` — Validates shared ref3 between forward and backward paths (coupling test)
- `gilbert_test.spice` — Standalone forward Gilbert cell test
- `bk_test.spice` — Legacy backward cell test (uses old bk_gilbert subcircuit)

## Running Simulations

```bash
# Individual test groups (recommended):
ngspice -b test_forward.spice
ngspice -b test_backward.spice
ngspice -b test_impedance.spice
ngspice -b test_gradient.spice
ngspice -b test_integration.spice

# All tests in one file:
ngspice -b neuron_tests.spice
```

## Circuit Architecture

### Neuron Interface

**Subcircuit `neuron`** (ports: VIN1 VIN2 OUT VCC VEE W1_EXT W2_EXT ERR)

- **VIN1, VIN2** (input terminals): Accept input voltages. Output = W1×VIN1 + W2×VIN2. Each input terminal also generates gradient current proportional to `K × W_i × ERR` (~1 μA/V²). Positive gradient is encoded as positive current sinking from the upstream output into the input terminal.
- **OUT** (output terminal): Drives the forward result as a low-impedance voltage (Z_out ≈ 100Ω). Voltage remains stable regardless of load within limits. In a multi-neuron chain, the current sinking into/out of OUT from downstream gradient cells serves as the error signal for this neuron's backward path.
- **ERR** (error input): Receives the error signal (voltage) that drives the backward path. In the current single-neuron testbench, ERR is driven by an explicit voltage source. In a chain, this would be derived from the current sensed at OUT.
- **W1_EXT, W2_EXT** (weight nodes): External access to weight capacitors for programming and monitoring.

### Forward Path (Gilbert Cell Multipliers)

- Two NPN Gilbert cells: one per input channel, sharing PNP mirror load
- 15:1 symmetric weight divider (14k/1k) keeps upper quad in linear tanh region
- E-element weight buffers prevent divider from loading weight caps
- Emitter degeneration: Re=1k, I_tail=2mA (linear to ~1V)
- PNP current mirror load (diff-to-single-ended)
- Two-EF output stage: R_trans(1.1k) + EF1 + R_level(1.1k) + current source + EF2 + R_out(80)
- Gain: slope ~0.617 V/V at W=0.636, Z_out ~100

### Backward Path

Two types of backward multiplier subcircuits:

- **`bk_mult`** (DC-compatible): for gradient cells where TARGET is a voltage source
  - NPN Gilbert cell + PNP mirror + R_trans(1.1k) + R_inject(960k)
  - Mirror output drives R_inject directly (960k negligible load vs R_trans)
  - DC offset at outn_bk absorbed by voltage source at INJECT
  - Gradient cells share w_bias, tail_ref, and ref3 with forward path
  - ref3 shared with forward path; coupling ~14mV at ERR=1V (acceptable for learning; forward slope/gradient/Z_out unaffected)

- **`bk_mult_ac`** (transient-only): for weight update cells where TARGET is a capacitor
  - Same as bk_mult but with 1uF coupling cap before R_inject(960k)
  - Coupling cap blocks DC offset that would drift weight caps
  - Requires `.ic V(x.bk_ac)=V_target_init` to pre-charge coupling cap

### Weight Storage
- 100nF caps with 100M bleed resistors
- Programming: voltage sources through 10M (DC: ~0.91x programmed value)
- `.ic` sets initial cap voltages; `UIC` flag used in transient

### Sign Convention
- Gradient current: positive gradient at VIN_i = positive current sinking from upstream output into VIN_i. Magnitude: I = K × W_i × ERR (K ≈ 1 μA/V²).
- Error signal: positive ERR means output is too low (err = target - actual). Current flowing into OUT from downstream gradient cells is the error signal.
- Weight update: positive VIN × positive ERR → weight increases (stable negative feedback loop).

## ngspice Pitfalls

- `IC=0` on a capacitor definition overrides `.ic V(node)=X` even with UIC. Remove `IC=` from cap lines.
- When SIN spec is defined (even `SIN(0 0 0)`), transient uses SIN offset, not DC value.
- `let` variables from one `op`/`dc` are lost in the next. Use transient for measurements across analyses.
- `meas DC ... AT=value` may fail at sweep boundaries due to floating-point precision. Use interior points.
- 15:1 dividers in bk_mult draw ~127uA from INA. When INA is a VIN source, this loads it significantly.
- `.include` files should use `.spice` extension for neovim syntax highlighting (not `.lib`).
