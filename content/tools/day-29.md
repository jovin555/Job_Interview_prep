# tools — Day 29

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** The cleanest approach is to use Zephyr's built-in build configuration system — Kconfig and devicetree overlays — rather than maintaining separate codebases. I'd structure the project so the core application code is hardware-agnostic and the differences live entirely in configuration.

First, I'd define the production sensor configuration in the base devicetree and defconfig. Then, for the development build, I'd create a devicetree overlay file that replaces the real sensor node with a mock sensor node, and a fragment Kconfig file that enables debug logging (`CONFIG_LOG=y`, `CONFIG_DEBUG=y`) and any mock-specific options. The mock sensor driver would be implemented as a separate driver that implements the same sensor API as the real one, so the application layer doesn't need to change.

The build would be invoked with `west build -d build/prod -b <board> app` for production and `west build -d build/dev -b <board> app -- -DOVERLAY_CONFIG=overlays/dev.conf -DDTC_OVERLAY_FILE=overlays/dev.overlay` for development. Keeping separate build directories is important because it prevents configuration contamination between the two builds.

I'd also add a CMake-level check or a runtime assertion that verifies the correct sensor driver is actually instantiated, because a common failure mode is that the overlay file is silently ignored due to a path typo, and you end up testing the real sensor instead of the mock. A simple `BUILD_ASSERT` on a Kconfig symbol that's only defined in the dev configuration can catch this at compile time.

**Possible follow-ups:**
- How would you handle the case where the mock sensor needs to simulate fault conditions that the real sensor can't produce?
- What would you do if the production and development builds need different linker scripts or memory layouts?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** This is a classic case where the symptom points to marginal timing margins rather than a hard protocol violation. I'd start by capturing the full enumeration sequence on both a host that works and a host that fails, using the logic analyzer with USB 2.0 protocol decoding enabled. The key is to capture the same transaction on both hosts and compare the timing parameters side by side.

Specifically, I'd look at:
- The device's response time to SETUP packets — USB 2.0 specifies a device response timeout, and if the device is right at the edge, some hosts will tolerate it while others won't.
- The chirp sequence during reset — if the device is slow to respond to the host's chirp, high-speed negotiation can fail intermittently.
- The frame timing — check for jitter in the SOF packets and whether the device's clock recovery is causing drift.

The logic analyzer's triggering is critical here. I'd set up a trigger on the first SETUP packet after reset, then capture a long window (several milliseconds) to see the entire enumeration sequence. I'd also enable timing measurements on the D+ and D- lines to quantify rise/fall times and cross-over points, because a marginal signal integrity issue can manifest as intermittent enumeration failures on hosts with slightly different receiver thresholds.

If the timing measurements show the device is consistently near a spec limit, the fix is usually in firmware — for example, adjusting the USB clock source or the response timing in the USB peripheral configuration. If the measurements show the timing varies significantly between captures, I'd suspect a power supply issue, such as droop during the inrush current at connect time, and would move to an oscilloscope with a current probe to correlate power events with the enumeration failures.

**Possible follow-ups:**
- How would you distinguish between a device-side timing issue and a host-side issue?
- What specific timing parameters in the USB 2.0 spec would you check first?

---

## Q3: How would you approach setting up a thermal simulation in Flotherm or Icepak for a sealed enclosure containing multiple power-dissipating components, and how would you validate the model against real measurements?

**Answer:** I'd start by defining the simulation's purpose — is this a steady-state thermal check, a worst-case ambient analysis, or a transient cooldown study? That determines the level of model fidelity needed. For a sealed enclosure, the dominant heat transfer paths are conduction through the PCB and enclosure, and natural convection and radiation from the enclosure surfaces to the environment. I'd model the enclosure as a solid with the correct material properties (typically aluminum or a plastic with known thermal conductivity), the PCB as an orthotropic material with in-plane and through-plane conductivities, and the components as lumped masses with specified power dissipation.

The critical step is assigning accurate power dissipation values to each component. I'd get these from the datasheet's thermal derating curves or from actual measurements on a prototype using a thermal camera or thermocouples. Guessing power dissipation is the most common source of simulation error.

For the mesh, I'd use a local grid refinement around the high-power components and the enclosure walls, because the thermal boundary layer is where the largest temperature gradients occur. A grid independence check — running the same simulation with a coarser and finer mesh and confirming the temperatures change by less than a few percent — is essential before trusting any absolute numbers.

For validation, I'd build the prototype, instrument it with thermocouples at the hottest predicted spots (typically the component case tops and the enclosure surface), and run it at the same ambient temperature and power levels as the simulation. I'd compare the steady-state temperatures and look for systematic offsets — if the simulation consistently predicts higher temperatures than measured, the model is conservative, which is acceptable for a design check. If the simulation predicts lower temperatures, I'd investigate whether I underestimated a component's power dissipation or missed a heat path, such as a thermal pad or a metal bracket that acts as a heatsink.

**Possible follow-ups:**
- How would you handle the uncertainty in the thermal conductivity of the PCB's internal copper layers?
- What would you do if the measured temperatures are significantly higher than the simulation predicts?

---

## Q4: How would you approach setting up a constraint management system in Cadence Allegro for a mixed-signal PCB that has both high-speed digital interfaces (USB 2.0, SPI at 20 MHz) and sensitive analog sensor inputs?

**Answer:** I'd approach this in layers, starting with the physical constraints that are non-negotiable and working up to the more nuanced electrical constraints.

First, I'd set up the layer stack in the constraint manager, because everything else depends on it. I'd define the dielectric materials, thicknesses, and copper weights, and let Allegro calculate the impedance for the controlled impedance nets. For USB 2.0, I'd create a differential pair constraint with 90-ohm differential impedance, and for the SPI at 20 MHz, I'd set up a single-ended constraint with a target impedance — typically 50 ohms, though at 20 MHz the trace length is usually short enough that impedance matching is less critical than length matching.

Next, I'd create net classes to group the signals by their electrical requirements: a "USB" class for the D+/D- pair, a "SPI_HIGH_SPEED" class for the clock and data lines, an "ANALOG_SENSITIVE" class for the sensor inputs, and a "POWER" class for the supply rails. Each class gets its own spacing rules — for example, the analog nets need larger spacing from the digital nets to minimize coupling, and the USB pair needs specific spacing from other nets to maintain the differential impedance.

For the analog sensor inputs, the key constraints are spacing and shielding, not impedance. I'd set up a rule that requires a ground guard trace around the analog nets, or at least a minimum spacing of 3-5 times the dielectric thickness from any digital signal. I'd also constrain the analog nets to a specific layer — typically the top or bottom layer — to avoid vias that can pick up noise from the digital layers.

Finally, I'd set up length matching rules. For USB 2.0, the D+ and D- pair needs to be matched to within a few mils. For the SPI bus, I'd match the clock to the data lines to ensure setup and hold times are met, especially if the SPI signals are routed over a longer distance.

The verification step is critical — I'd run the constraint manager's DRC after routing and review the violation report. I'd also use the cross-probe feature to visually inspect the critical nets in the layout, because some issues — like a differential pair that splits around a via — can pass DRC but still be electrically problematic.

**Possible follow-ups:**
- How would you handle the conflict between the analog spacing requirements and the board size constraints?
- How would you verify that the impedance targets are actually achieved in the fabricated board?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is stop the discussion about who's right and get the facts on the table. I'd call a short meeting with both teams and ask them to bring their source of truth — the firmware team brings the sensor datasheet and their I2C driver code, and the hardware team brings the schematic and the sensor's datasheet. The goal is to determine which implementation matches the actual hardware that's on the board, because that's the ground truth.

Once we've confirmed which side is correct — and it's usually the hardware, because the schematic reflects the physical part that's soldered down — I'd assess the impact. The key question is whether the firmware can be fixed in two days. If the sensor supports both 7-bit and 10-bit addressing, the fix might be a one-line change in the driver configuration. If the register map is different, the fix could be more substantial.

I'd also check whether the firmware team's code was tested on an evaluation board with a different sensor variant. If so, that explains the discrepancy — the eval board had a different part or different address strap settings. I'd document this as a lesson learned: the firmware team should have verified the address and register map against the actual schematic before writing the driver.

For the immediate path forward, I'd have the firmware team make the fix and test it on the actual hardware, not the eval board. I'd also have the hardware team double-check the schematic against the physical board to make sure there are no other discrepancies. If the fix is too large for two days, I'd negotiate with the project manager to delay integration testing, because shipping a device with a non-functional sensor interface is worse than a schedule slip.

After the immediate issue is resolved, I'd implement a process change: a formal hardware-firmware interface review before integration testing, where both teams walk through the protocol details — addressing, register maps, timing — against the schematic and datasheet. This is a standard practice in medical device development and would catch this class of error earlier.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct because it works on the eval board?
- What would you do if the hardware team discovers that the schematic itself is wrong, and the physical board has a different sensor than what's documented?