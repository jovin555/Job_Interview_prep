# tools — Day 26

## Q1: How would you approach setting up a differential pair routing constraint in Cadence Allegro for a CAN-FD bus running at 5 Mbps on a mixed-signal medical device PCB?

**Answer:** For CAN-FD at 5 Mbps, the signal integrity requirements are more demanding than classic CAN at 500 kbps, but they're still well within the realm of controlled impedance design rather than the tight skew tolerances you'd see with USB 2.0 or Gigabit Ethernet. My approach would start with understanding the transceiver's driver characteristics and the receiver's input thresholds from the datasheets, then determining the target differential impedance — typically 120 ohms for CAN, matching the characteristic impedance of the twisted-pair cable the bus is designed around.

In Allegro's constraint manager, I'd set up a physical constraint set for the differential pair defining the line width, gap, and impedance target. The key here is that the PCB trace impedance needs to match the cable and transceiver impedance to minimize reflections at the connector interface. I'd work with the board stackup to calculate what trace geometry achieves 120 ohms differential — this often means wider traces and larger gaps than you'd use for USB, which is fine because the routing density is usually lower.

For the spacing rules, I'd set the differential pair-to-pair spacing to at least 3-5 times the dielectric height to minimize crosstalk, and I'd also set a minimum clearance to other nets, particularly to the analog sensor traces on the same board. CAN-FD at 5 Mbps has fast edge rates, so the return current path matters — I'd ensure there's a solid ground reference beneath the pair and avoid routing over splits in the ground plane.

For verification, I'd use Allegro's impedance analysis to check that the actual routed geometry meets the target, and I'd also review the length matching between the P and N traces — at 5 Mbps with typical edge rates, keeping them within a few hundred mils is usually sufficient, but I'd check the transceiver's skew tolerance to be sure. Finally, I'd add the impedance requirement to the fabrication notes and verify the board house's impedance coupon results on the first article.

**Possible follow-ups:**
- How would your approach change if the CAN-FD bus also needed to pass through a board-to-board connector?
- What would you do if the board stackup couldn't achieve 120 ohms differential with reasonable trace widths?

---

## Q2: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at 320 MHz is coming from a 40 MHz clock's 8th harmonic or from a switching regulator's switching frequency harmonic?

**Answer:** The first step is to identify all potential sources that could produce energy at 320 MHz. A 40 MHz clock's 8th harmonic is an obvious candidate, but I'd also need to consider switching regulators — for example, a 2 MHz switcher's 160th harmonic, or a 1.6 MHz switcher's 200th harmonic. The key is to systematically narrow down which source is dominant.

I'd start by measuring the fundamental frequencies of all the clocks and switching regulators on the board using a near-field probe connected to the spectrum analyzer. I'd set the analyzer to a wide span, say 0-500 MHz, and identify the fundamental peaks. Once I know the exact frequencies, I can calculate which harmonics land at 320 MHz.

Next, I'd use the near-field probe to physically locate where the 320 MHz energy is strongest on the board. If the hot spot is directly over the 40 MHz clock trace or its associated IC, that's strong evidence it's the clock harmonic. If it's over the switching regulator's inductor or the trace between the switcher and its output capacitor, that points to the regulator.

To confirm, I'd use a differential measurement technique: I'd measure the 320 MHz amplitude with the clock running and the regulator disabled (if possible), then swap — regulator running and clock disabled. This is the most definitive test. If I can't disable either source, I'd look at the harmonic structure: clock harmonics tend to have a consistent amplitude roll-off pattern (roughly 1/n or 1/n² depending on the edge rate), while switching regulator harmonics can have a more irregular pattern due to the control loop's modulation.

I'd also check whether the 320 MHz peak has sidebands. Switching regulators often produce sidebands around their harmonics due to the switching frequency modulation or control loop ripple, whereas clock harmonics are typically cleaner. Finally, I'd use a time-domain measurement with an oscilloscope triggered on the clock to see if the 320 MHz signal is coherent with the clock edge — if it is, that confirms the clock as the source.

**Possible follow-ups:**
- How would you distinguish between a harmonic and a resonance if both sources are active?
- What if the near-field probe shows the hot spot is at a via or connector rather than at either source?

---

## Q3: How would you approach setting up a Zephyr RTOS project to support runtime calibration of an analog sensor front-end, where the calibration coefficients need to be stored in flash and survive firmware updates?

**Answer:** This is a common requirement for medical devices where sensor drift or part-to-part variation needs to be compensated. The key design constraint is separating the calibration data from the firmware image so that a firmware update doesn't overwrite the calibration values.

I'd start by partitioning the flash memory into at least three regions: the bootloader, the application firmware, and a dedicated calibration data area. In Zephyr, this is typically done through the devicetree and the flash partition map. I'd define a fixed-size partition for calibration data, separate from the application slot, and I'd use Zephyr's flash driver API to read and write to that partition.

For the calibration data structure, I'd define a versioned struct that includes a magic number, a version field, a CRC or checksum, and the actual calibration coefficients. The version field is critical — if the firmware changes the calibration algorithm or the number of coefficients, the structure can change, and the firmware needs to detect that the stored data is incompatible and either migrate it or trigger a recalibration.

For the runtime aspect, I'd create a calibration manager module that loads the coefficients from flash at boot, validates the CRC, and exposes them to the sensor driver via a simple API. The sensor driver would apply the coefficients in its conversion routine. When a calibration procedure is run — for example, during manufacturing or a field calibration — the manager would write the new coefficients to flash using a write-then-verify sequence to ensure the data is actually programmed correctly.

For surviving firmware updates, the critical design decision is that the calibration partition is never touched by the firmware update process. I'd configure the update mechanism — whether it's MCUboot or a custom bootloader — to only write to the application partition. I'd also add a safety mechanism: if the calibration data is corrupted or missing, the firmware should fall back to default coefficients and flag a warning rather than failing to boot.

I'd also consider wear leveling if the calibration data is written frequently. Flash has limited write endurance, so if calibration happens often, I'd either use a small circular buffer in the calibration partition or use Zephyr's NVS (Non-Volatile Storage) subsystem, which handles wear leveling and data integrity automatically.

**Possible follow-ups:**
- How would you handle the case where a firmware update changes the calibration data structure?
- What safety considerations would you add for a medical device where incorrect calibration could affect patient safety?

---

## Q4: How would you approach using a Segger J-Link debugger to capture a real-time trace of a Zephyr RTOS-based system's thread scheduling behavior without halting the CPU or modifying the firmware?

**Answer:** The key requirement here is non-intrusive tracing — we don't want to halt the CPU or add instrumentation code that could change the timing behavior we're trying to observe. The J-Link's trace capability, when used with a compatible target MCU that has an Embedded Trace Macrocell (ETM) or similar trace unit, is the right tool for this.

First, I'd verify that the target microcontroller supports trace output and that the specific J-Link model has trace capture capability — the higher-end J-Link models (like the ULTRA+ or PRO) support ETM trace, while the base models typically only support SWO (Serial Wire Output) tracing. If the MCU has a trace pin (TRACEDATA[0:3], TRACECLK), I'd connect those to the J-Link's trace connector.

For thread scheduling behavior specifically, I have two options. The first is using SWO with Zephyr's built-in tracing support — Zephyr has a tracing subsystem that can output thread switch events over SWO, but this requires the tracing feature to be enabled in the firmware configuration, which is a form of instrumentation. The second, more truly non-intrusive option is using ETM trace, which captures the actual instruction execution stream. With ETM, I can reconstruct which code was executing at any given time, and by correlating that with the RTOS kernel's thread context switch code addresses, I can determine when thread switches occurred without any firmware modification.

In practice, I'd use SEGGER's Ozone or J-Scope software to capture the trace. Ozone has an RTOS awareness feature that can decode thread scheduling from the trace data if it knows the RTOS's data structures — it supports Zephyr. I'd configure Ozone with the ELF file so it knows the symbol addresses, then start the trace capture while the system runs normally. After capturing for the desired duration, I'd stop the trace and analyze the timeline to see which threads were running, when context switches occurred, and how long each thread executed.

One important consideration is that ETM trace requires a significant amount of RAM or a large trace buffer to store the captured data, and the trace bandwidth can be limited. For long-duration captures, I might need to use trace streaming to the host PC, which requires a faster J-Link model. I'd also need to be careful about the trace clock configuration — the trace pins need to be properly initialized in the firmware, which is a one-time configuration that doesn't affect runtime behavior.

**Possible follow-ups:**
- How would you correlate the trace data with specific application events, like a sensor reading or a motor command?
- What would you do if the target MCU doesn't have ETM trace support?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is verify the discrepancy myself rather than relying on either team's assertion. I'd pull up the hardware schematic and the sensor datasheet to confirm the actual addressing mode and register map, and I'd look at the firmware source code to see what addressing and registers it's using. This isn't about doubting either team — it's about establishing ground truth before any decisions are made.

Once I've confirmed the mismatch, I'd call a short, focused meeting with the firmware lead and the hardware engineer who designed the sensor interface. I'd present the evidence clearly: here's what the hardware implements, here's what the firmware expects, and here's where they diverge. I'd frame it as a factual issue to solve, not a blame assignment. The goal is to get everyone aligned on the facts before discussing solutions.

Then I'd evaluate the options. The most obvious is to change the firmware to match the hardware — if the hardware is already in fabrication, that's the only viable option for the sensor interface itself. But I'd also check whether the hardware has address pins that could be strapped differently, or whether the sensor supports both 7-bit and 10-bit addressing modes that could be configured via a different register write. If the hardware is already fabricated, the firmware change is almost certainly the answer, but I'd verify the scope of the change — is it just the address, or does the register map differ significantly?

I'd also assess the risk of the firmware change. If the register map is different, the firmware might need to change how it configures the sensor, how it reads data, and how it interprets the data. This could affect calibration, data formatting, and any safety-related thresholds. I'd work with the firmware team to estimate the effort and identify any areas where the change could introduce new bugs.

Given the two-day timeline, I'd also consider a mitigation strategy: if the firmware change is too large to complete and verify in two days, I'd propose a phased approach where the integration testing starts with a limited scope — perhaps testing only the sensor communication path — while the full firmware change is completed in parallel. I'd also ensure that the firmware change goes through proper review and testing, even if it means delaying the full integration test by a day or two. In a medical device context, shipping a known protocol mismatch to testing is not acceptable — the risk of a false pass or a latent bug is too high.

Finally, I'd implement a process improvement to prevent this from happening again. I'd suggest that the hardware and firmware teams share a common interface control document (ICD) that specifies the exact protocol details — addressing mode, register map, timing — and that both teams review it before hardware fabrication and firmware development proceed independently.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct based on the sensor vendor's evaluation board?
- What would you do if the firmware change requires more than two days to implement and verify?