# tools — Day 16

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with additional debug features, without maintaining two separate codebases?

**Answer:** The cleanest approach is to use Zephyr's Kconfig and devicetree overlay system to create build-time configurations that share the same source tree. I'd structure the project with a base application directory containing all common source files, then use separate configuration files for each build variant.

For the production build, I'd have a `prj.conf` that enables only what's needed — minimal logging, no shell, no debug features. For the development build, I'd create a `prj_dev.conf` (or use a `boards/` overlay) that enables the shell, verbose logging, thread analyzer, and any debug GPIOs or test hooks. The key is using Kconfig options to conditionally compile debug code, so the production binary doesn't even contain the debug paths.

For hardware-specific differences, I'd use devicetree overlays — for example, a development overlay that enables an extra UART for debug output or remaps a button to trigger a test mode. The `west build` command then just selects the right configuration: `west build -b <board> -- -DCONF_FILE=prj_dev.conf` for development, or the default `prj.conf` for production.

I'd also make sure debug features are gated behind Kconfig options that default to disabled, so there's no risk of accidentally shipping debug code. For example, a `CONFIG_DEV_MODE` option that enables test hooks, with the production build explicitly setting it to `n`. This keeps the codebase single-source while making the build variant explicit and auditable.

**Possible follow-ups:**
- How would you ensure that the development build doesn't accidentally get flashed into a production device during manufacturing?
- What Kconfig options would you use to conditionally compile test-only code paths?

---

## Q2: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This is a classic intermittent failure that's likely temperature-related, so I'd approach it as a two-part problem: first, capture the failure when it happens, and second, correlate the timing with environmental conditions.

For the logic analyzer setup, I'd connect probes to SCK, MOSI, MISO, and the chip select line, making sure to use a sampling rate at least 4-5x the SPI clock to capture glitches and setup/hold violations. I'd trigger on the chip select falling edge or on a missing MISO response, depending on what "fails to receive" means — is the slave not responding at all, or is it responding with corrupted data?

Since the failure is temperature-related, I'd want to capture the bus activity continuously or in a looped buffer. Most logic analyzers have deep memory or streaming modes, so I'd set up a long capture window. I'd also add a temperature sensor reading to the capture — either by logging the enclosure temperature separately and timestamping it, or by using a logic analyzer channel to monitor a temperature-dependent signal (like a thermistor output through a comparator).

When analyzing the captured data, I'd look for:
- **Timing violations**: Are setup/hold times on MISO relative to SCK marginal at temperature? Silicon gets slower as it heats up, so a slave that barely met timing at room temperature might fail at 60°C.
- **Signal integrity degradation**: Rising edge slew rates on MISO might slow down as the driver IC heats up, causing the master to sample at the wrong time.
- **Chip select issues**: Glitches or slow edges on CS can cause the slave to miss the start of a transaction.
- **Clock stretching or missing clocks**: If the master is generating fewer clocks than expected, the slave might not shift out all its data.

If the logic analyzer shows the slave is responding correctly but the master is sampling at the wrong time, I'd suspect a timing margin issue. If the slave isn't responding at all, I'd look at whether the slave's power supply is drooping under temperature — a separate issue that might require an oscilloscope on the supply rail.

**Possible follow-ups:**
- How would you set up the logic analyzer to capture a failure that happens only once every few hours?
- What would you look for in the captured data to distinguish between a slave-side timing issue and a master-side sampling issue?

---

## Q3: How would you approach setting up a thermal simulation in Flotherm or Icepak for a sealed enclosure containing multiple power-dissipating components, and how would you validate the model against real measurements?

**Answer:** The key to useful thermal simulation is building a model that's accurate enough to guide design decisions without being so detailed that it's impractical to set up and solve. I'd start by identifying the major heat sources — power regulators, processors, motor drivers, and any high-current paths — and their dissipation values. For a sealed enclosure, the dominant heat transfer paths are conduction through the PCB and enclosure, and natural convection and radiation inside the enclosure, so I'd model those carefully.

For the simulation setup, I'd:
1. **Create the geometry**: Import the PCB outline, enclosure, and major components. For components, I'd use compact thermal models (two-resistor or Delphi models) rather than detailed transistor-level models, since the goal is system-level temperature prediction.
2. **Assign material properties**: FR4 thermal conductivity (anisotropic — in-plane vs. through-plane are different), copper pour coverage on each layer, aluminum or plastic enclosure properties, and thermal interface materials.
3. **Set boundary conditions**: Ambient temperature, and for a sealed enclosure, the external convection coefficient (natural convection, so typically 5-10 W/m²K depending on orientation).
4. **Define heat sources**: Power dissipation values for each component, ideally from measured or estimated load conditions.

For validation, I'd build the prototype and place thermocouples at the hottest predicted locations — typically on the top of major ICs, on the PCB near the power stage, and on the enclosure wall. I'd also use a thermal imaging camera to get a full-surface temperature map, which is especially useful for identifying hot spots I didn't predict. The correlation process is iterative: I'd compare simulated vs. measured temperatures, and if they diverge by more than a few degrees, I'd investigate why — maybe the component thermal model is wrong, the copper pour is more effective than modeled, or there's an unexpected heat path.

One common pitfall is assuming the enclosure is perfectly sealed with no airflow, but in reality there's always some internal air movement from natural convection. I'd model the internal air as a fluid domain, not just a void, because the air circulation inside the enclosure significantly affects heat spreading.

**Possible follow-ups:**
- How would you handle components that have significant heat spreading through their leads or pads?
- What would you do if the simulation predicted a component would exceed its maximum junction temperature, but the design couldn't be changed?

---

## Q4: How would you approach setting up a Segger J-Link debugger for automated firmware testing on a Zephyr RTOS-based medical device, where you need to program the device, run a test sequence, and capture crash dumps without manual intervention?

**Answer:** The goal is a fully automated test loop that can run overnight or in CI, so I'd structure this in layers: the J-Link scripting layer, the test orchestration layer, and the crash analysis layer.

For the J-Link layer, I'd use the J-Link Commander (JLinkExe) or the J-Link SDK to create a script that:
1. Connects to the target via SWD or JTAG
2. Programs the flash with the firmware image
3. Resets and runs the target
4. Monitors for a test completion signal (e.g., a specific value written to a known memory location, or a UART message)

For crash capture, the key is configuring the J-Link to halt the CPU on a hard fault. I'd set up the J-Link's flash breakpoint feature to break on the hard fault handler, then use the J-Link's RTT (Real-Time Transfer) or a crash dump routine in firmware to capture the register state, stack contents, and the RTOS thread that was running. The firmware would have a crash handler that writes a structured dump to a reserved RAM region, and the J-Link script would read that region after detecting the fault.

For the test orchestration, I'd write a Python script that:
1. Calls the J-Link script to program and run the device
2. Monitors the test progress via RTT or a UART log
3. If the test passes, moves to the next test case
4. If the test fails or crashes, captures the crash dump, saves it with a timestamp and test case ID, and resets the device for the next test

The tricky part is making this robust for unattended operation. I'd add watchdog timeouts — if the device doesn't respond within a certain time, the script assumes a hang and captures whatever state is available. I'd also make sure the J-Link connection is reliable, since a lost connection in the middle of a test run can corrupt the results.

For Zephyr specifically, I'd use the built-in crash handlers and the `CONFIG_THREAD_ANALYZER` or `CONFIG_DEBUG_THREAD_INFO` options to get thread state in the crash dump. The firmware crash handler would be instrumented to save the thread ID, stack pointer, and a backtrace to a known memory location, which the J-Link script can read after a fault.

**Possible follow-ups:**
- How would you handle a test case that requires the device to be in a specific state before the test starts?
- What would you do if the crash dump is corrupted or incomplete?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and a senior engineer on your team strongly disagrees with your approach to grounding — you've designed a split ground plane to isolate the analog sensor section from the digital section, but the senior engineer argues that a solid ground plane is better and that split planes cause more problems than they solve. The disagreement is becoming heated, and the review is stalled. How would you handle this situation?

**Answer:** First, I'd acknowledge that this is a legitimate technical debate — both approaches have merit, and the right answer depends on the specific design. Split ground planes were common practice years ago, but modern thinking often favors solid ground planes with careful component placement and routing, because splits can create return path discontinuities that cause more EMI problems than they solve. The senior engineer's concern is valid.

I'd de-escalate the situation by separating the technical discussion from the personal disagreement. I'd say something like, "You're raising a good point — let's look at the actual data for this design rather than debating general principles." Then I'd suggest we evaluate the specific factors that matter for this board:
- What's the noise sensitivity of the analog section? What's the signal-to-noise ratio requirement?
- What are the frequencies involved? A 24-bit ADC sampling at low frequency has different needs than a high-speed ADC.
- Where are the return currents flowing? Can we route the digital traces so their return currents don't cross the analog section?
- What does the layout actually look like — can we achieve the isolation with component placement and routing alone?

I'd propose we do a quick analysis — maybe a signal integrity simulation or a review of the return current paths — before making a final decision. If the review can't be resolved in the meeting, I'd suggest we table it, have both approaches documented with their trade-offs, and bring in a third opinion from another senior engineer or a signal integrity specialist. The key is to make the decision based on engineering analysis, not on who argues more persuasively.

If we ultimately go with the senior engineer's approach, I'd make sure the decision is documented with the reasoning, so it's clear it was a technical decision, not a concession. If we go with my approach, I'd do the same. Either way, the goal is to keep the design review productive and maintain a working relationship.

**Possible follow-ups:**
- What if the senior engineer continues to challenge your decisions in future reviews, even after this issue is resolved?
- How would you handle a situation where you believe the senior engineer's approach is technically wrong, not just different?