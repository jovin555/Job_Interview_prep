# tools — Day 15

## Q1: How would you approach setting up a Zephyr RTOS project using the west build system to support both a production firmware build and a development build with additional debug features, without maintaining two separate codebases?

**Answer:** The cleanest approach is to use Kconfig and devicetree overlays to manage the differences, rather than maintaining separate source trees. I'd structure the project so the production configuration is the default, and the development configuration is applied as an overlay on top of it.

For the west build system specifically, I'd set up multiple build directories — one for production and one for development — each pointing to the same source tree but using different configuration fragments. The production build would use the base `prj.conf` and the base devicetree. The development build would use an additional `prj_dev.conf` fragment (applied via `-DOVERLAY_CONFIG=prj_dev.conf`) that enables things like logging at debug level, shell commands for register inspection, and maybe a software-triggered fault injection mechanism for testing error handlers.

For devicetree, I'd use overlays to enable debug interfaces that shouldn't exist in production — for example, a test point UART or a debug GPIO header. The key is that the production build remains the source of truth, and the development overlay is additive only — it never removes or changes production functionality, only adds debug capability.

I'd also use CMake build-type conditionals if there are source-level differences, but I'd keep those minimal. The goal is that the production build is what gets verified and released, and the development build is a superset that's clearly marked as non-release. I'd add a build-time check that fails the build if a release flag is set while debug features are still enabled, to prevent accidental release of a debug build.

**Possible follow-ups:**
- How would you handle the case where a debug feature changes timing behavior enough to mask a bug that only appears in production builds?
- What would you put in a CI pipeline to ensure the production configuration is always buildable and tested, even when developers primarily work with the debug configuration?

---

## Q2: How would you approach using a logic analyzer to debug an I2C bus where the slave device occasionally NACKs a read transaction, but only after the system has been running for several hours?

**Answer:** I'd start by setting up the logic analyzer to capture the I2C bus continuously with a deep buffer, triggering on the NACK condition. Most logic analyzers can trigger on a specific bus condition — in this case, I'd set the trigger to capture when the master receives a NACK on a read operation. The key is to capture enough data *before* the trigger to see the context leading up to the failure.

Since the failure is time-dependent (after several hours), I'd want to look for patterns in the captured data. I'd examine several things:

First, the clock stretching behavior — is the slave stretching the clock longer than usual before the NACK? That could indicate the slave's internal buffer is nearly full or it's busy with an internal operation.

Second, the address and register being accessed — is the failure always on the same register, or does it move around? If it's the same register, that points to a specific issue with that register's handling. If it moves, it suggests a more general resource exhaustion.

Third, the time between transactions — is the failure correlated with a specific pattern of preceding traffic? For example, does it happen after a burst of writes, or after a period of inactivity?

I'd also check whether the NACK is on the address byte or the data byte. A NACK on the address byte means the slave isn't responding at all — possibly it's in a low-power state or has crashed. A NACK on the data byte means the slave is alive but refusing the read — possibly its buffer is full or it's in an error state.

If the logic analyzer has protocol decoding, I'd use it to get a clean transaction-level view. But I'd also keep the raw waveform view available to check signal integrity — rise times, glitches, or noise that might be marginal and only manifest after thermal drift.

**Possible follow-ups:**
- How would you distinguish between a slave that's genuinely busy versus one that's hung or crashed?
- What would you look for if the NACK always occurs on the first transaction after a long idle period?

---

## Q3: How would you approach setting up a thermal simulation in Flotherm or Icepak for a sealed enclosure containing multiple power-dissipating components, and how would you validate the model against real measurements?

**Answer:** I'd approach this in stages, starting with a simplified model and progressively adding detail. The first step is to define the boundary conditions: ambient temperature, enclosure material and thickness, and whether there's any forced convection or if it's purely natural convection and radiation.

For the components themselves, I'd model the major heat sources — the main processor, power regulators, and any high-current drivers — using their thermal dissipation values from the datasheets. I'd also model the PCB as a layered structure with copper planes, since the PCB is often a significant heat-spreading path in a sealed enclosure. The key is to get the board's effective thermal conductivity right, which depends on copper coverage and via density.

I'd model the enclosure as a solid with appropriate material properties — aluminum conducts well, plastic doesn't, and the difference matters enormously for the thermal path. I'd also include any thermal interface materials between components and the enclosure, since those are often the bottleneck.

For validation, I'd build the prototype and measure with thermocouples at the critical component case temperatures, plus a thermal camera for surface temperature distribution. I'd place thermocouples on the hottest components, the PCB near the heat sources, and the enclosure surface. I'd run the device at maximum load until temperatures stabilize — which can take 30-60 minutes in a sealed enclosure — and compare the steady-state temperatures with the simulation.

The correlation process is iterative. If the simulation predicts a component at 85°C but the measurement shows 95°C, I'd look at where the model is underestimating thermal resistance. Common issues are overestimating PCB thermal conductivity, underestimating radiation heat transfer, or missing a thermal path through a connector or cable. I'd adjust the model and re-run until the correlation is within a reasonable tolerance — typically 5-10°C for a sealed enclosure, which is acceptable for design decisions.

**Possible follow-ups:**
- How would you handle the uncertainty in component thermal dissipation values, which are often worst-case rather than typical?
- What would you do if the simulation shows a component exceeding its maximum junction temperature, but you can't change the enclosure design?

---

## Q4: How would you approach setting up a Segger J-Link debugger for automated firmware testing on a Zephyr RTOS-based medical device, where you need to program the device, run a test sequence, and capture crash dumps without manual intervention?

**Answer:** I'd structure this around J-Link's scripting capabilities and the command-line interface, integrated with the test framework. The key components are: programming the device, running the test, capturing the crash state, and reporting results.

For programming, I'd use the J-Link Commander (JLinkExe) with a command script that loads the firmware image and resets the target. This can be invoked from the test harness. I'd use the flash download command to program the image, then set the PC to the reset vector and run.

For the test sequence itself, I'd use Zephyr's test framework or a custom test harness that runs on the target. The firmware would execute the test sequence and report results over a debug UART or via the J-Link's virtual COM port. The host-side test script would monitor the output and determine pass/fail.

For crash capture, the critical piece is configuring the J-Link to halt the CPU on a hard fault. I'd set up the debugger to catch the fault exception and then dump the CPU registers, stack contents, and key memory regions. The J-Link Commander supports commands to read registers and memory, so I'd script a sequence that captures the program counter, link register, stack pointer, and the fault status registers (CFSR, HFSR, BFAR, MMAR on Cortex-M). I'd also dump a portion of the stack to help with post-mortem analysis.

The key design decision is whether to use the J-Link's built-in flash breakpoint capability or to use the firmware's own fault handler. Using the debugger is more flexible because it doesn't require modifying the firmware, but it does require the debugger to be connected and armed. For automated testing, I'd have the test harness arm the debugger before each test run, then wait for either a test completion message or a crash event.

I'd also use the J-Link's RTT (Real-Time Transfer) feature for logging, since it's non-intrusive and doesn't require a UART. This gives me a circular buffer of recent log messages that I can read after a crash to understand what the firmware was doing leading up to the fault.

**Possible follow-ups:**
- How would you handle the case where the firmware crashes in a way that prevents the J-Link from halting the CPU cleanly, such as a watchdog reset?
- How would you integrate this into a CI pipeline where multiple test targets need to run in parallel?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different I2C address for a sensor than what the hardware actually implements — the firmware is using 7-bit address 0x48, but the hardware has the address pins strapped for 0x49. The firmware team says they tested it on an evaluation board and it worked fine, and they're confident the address is correct. The PCB is already in fabrication, and the project is on a tight schedule. How would you handle this situation?

**Answer:** The first thing I'd do is verify the facts before any confrontation. I'd check the sensor datasheet to confirm the address pin configuration, look at the schematic to see how the address pins are actually strapped, and check the firmware source to confirm what address is being used. I'd also check the evaluation board schematic to see if it matches the production hardware — it's entirely possible the eval board had different strap settings.

Once I've confirmed the discrepancy, I'd bring the firmware team lead into a private conversation to review the evidence together. The goal is to establish the facts collaboratively, not to assign blame. I'd show them the schematic, the datasheet, and the firmware code, and walk through the address calculation together. If the eval board was indeed different, that explains the confusion — it's a legitimate mistake, not negligence.

Then I'd assess the options. Since the PCB is already in fabrication, changing the hardware isn't possible without a board spin, which would be expensive and delay the project. The options are: change the firmware to use the correct address (which is a one-line change if the address is defined as a constant), or find a way to modify the hardware after fabrication (which is risky and not appropriate for a medical device). The firmware change is clearly the right answer — it's simple, low-risk, and doesn't affect the hardware.

I'd also check whether the firmware has any other hardcoded assumptions that might not match the hardware — this is a good opportunity to do a broader review of the interface definitions. I'd suggest creating a shared header file or a hardware abstraction layer that defines all the I2C addresses and register maps in one place, so this class of error is caught at compile time or during integration testing.

Finally, I'd use this as a learning opportunity. I'd suggest adding an integration test that verifies the firmware can communicate with the sensor at the expected address before the full test suite runs. This would catch similar issues earlier in the development cycle. I'd also review whether the hardware and firmware teams have a formal interface control document (ICD) that defines the I2C addresses, register maps, and protocol details — if not, creating one would prevent this class of error in future projects.

**Possible follow-ups:**
- How would you handle the situation if the firmware team lead insists that the eval board behavior is the correct behavior and the hardware should be changed instead?
- What would you do if you discovered this same type of discrepancy had happened on a previous project, and the firmware team has a pattern of not checking the hardware documentation?