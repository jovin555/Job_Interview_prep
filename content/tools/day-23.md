# tools — Day 23

## Q1: How would you approach setting up a multi-channel design in Altium Designer for a medical device that has four identical analog sensor front-end channels, each with its own ADC and signal conditioning, while keeping the design maintainable and the schematic readable?

**Answer:** I'd use Altium's multi-channel design capability, which is specifically built for this scenario. The approach starts with designing one channel as a complete, standalone schematic sheet — including the signal conditioning, ADC, local decoupling, and any channel-specific filtering. This single channel becomes the "child" sheet in a hierarchical design.

The parent sheet would instantiate that child sheet four times using the Repeat command, like `Repeat(Channel, 1, 4)`. Altium automatically generates unique designators for components in each channel instance (e.g., R1_1, R1_2, R1_3, R1_4), which is critical for BOM generation and assembly.

For the net naming, I'd use the `Channel_` prefix or the `Repeat` net labeling convention so that each channel's nets are properly differentiated. The key decision is what gets shared across channels versus what stays local. Power rails, reference voltages, and the digital interface to the microcontroller would be global nets; the analog signal path, local filtering, and ADC conversion would be channel-specific.

One important consideration is how the ADC outputs connect back to the processor. If each channel has its own SPI or I2C interface, I'd bring those out as bused signals. If they share a bus with chip selects, I'd make sure the channel addressing is clear in the schematic. I'd also add a channel identifier net or a unique address strap per channel to make firmware debugging easier.

For maintainability, I'd put the channel-specific component parameters — like gain-setting resistor values or filter cutoff components — in a top-level variant or parameter set, so that if the analog front-end needs tuning, the change happens in one place rather than across four identical copies. I'd also run a multi-channel-aware ERC to catch cross-channel connectivity issues before layout.

**Possible follow-ups:**
- How would you handle the PCB layout for these repeated channels — would you use a room-based layout approach?
- What happens when one channel needs a different component value than the others — how do you manage that in the multi-channel framework?

---

## Q2: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This is a classic intermittent failure that points to a timing or signal-integrity issue that's temperature-dependent. My approach would be systematic, starting with capturing the failure rather than guessing at the cause.

First, I'd set up the logic analyzer to capture all four SPI signals — SCK, MOSI, MISO, and the chip select — simultaneously, with a sample rate at least 4-5 times the SPI clock frequency. I'd trigger on the chip select edge or on a specific data pattern that precedes the failure. Since the failure is intermittent and temperature-related, I'd want to capture a long window — ideally using deep memory or streaming capture — so I can see the entire transaction that fails.

The key is to capture both the failing transaction and several successful ones before it, so I can compare them. I'd look for several specific things:

1. **Timing margin degradation**: As temperature rises, driver output impedance and trace impedance change. I'd check setup/hold times on the MISO line relative to SCK edges. If the slave's data is changing too close to the sampling edge, that's a classic temperature-dependent timing failure.

2. **Signal integrity issues**: I'd look at the captured waveform for ringing, overshoot, or slow edges on MISO — though a logic analyzer only shows digital levels, so I'd correlate with an oscilloscope if I see marginal timing.

3. **Chip select behavior**: Sometimes the issue isn't the data but the chip select — if it's glitching or not asserting cleanly at temperature, the slave may not respond correctly.

4. **Clock integrity**: I'd check that SCK is clean and has the expected frequency and duty cycle. A marginal oscillator or a clock that's being affected by thermal drift could cause the slave to miss bits.

Once I've identified the likely failure mode from the capture, I'd verify with an oscilloscope using proper probing techniques — a short ground spring, not a long ground lead — to measure the actual analog characteristics of the marginal signal. I'd also use a thermal chamber or a heat gun (carefully, in a controlled way) to accelerate the failure and confirm the temperature correlation.

If the issue is timing margin, the fix might be adjusting the SPI clock phase/polarity settings, reducing the clock frequency, or adding a small series resistor to damp ringing. If it's a chip select issue, I might need to adjust the timing between CS assertion and the first clock edge. The important thing is to have captured the actual failure before changing anything.

**Possible follow-ups:**
- How would you distinguish between a setup-time violation and a hold-time violation from the logic analyzer capture?
- What if the logic analyzer shows the SPI transaction completing correctly, but the firmware still doesn't get the data — where would you look next?

---

## Q3: How would you approach setting up a Segger J-Link debugger for automated firmware testing on a Zephyr RTOS-based medical device, where you need to program the device, run a test sequence, and capture crash dumps without manual intervention?

**Answer:** I'd approach this by building a scripted test harness around the J-Link's command-line interface and scripting capabilities, integrated with the Zephyr build system.

The foundation is the J-Link Commander (JLinkExe on Linux, JLink.exe on Windows) and its scripting language. I'd create a command script that handles the programming step: connecting to the target via SWD or JTAG, halting the core, loading the firmware image (typically the `.hex` or `.elf` file produced by the Zephyr build), verifying the flash contents, and then resetting and starting execution.

For the test sequence itself, I'd use a combination of approaches. The J-Link script can handle basic operations, but for more complex test logic — like sending commands over UART, checking GPIO states, or verifying sensor readings — I'd write a Python script that drives the J-Link via pylink (the official SEGGER Python library) or by shelling out to JLinkExe. The Python script would orchestrate the whole flow: program the device, run the test, monitor for results, and handle failures.

For crash dump capture, the key is configuring the J-Link to halt the CPU on a hard fault and then extract the register state and memory contents. I'd set up the J-Link to use the vector catch feature to halt on HardFault, then use the J-Link's memory read commands to dump the stack, the CPU registers, and the relevant Zephyr kernel structures. For a Zephyr system, I'd also want to capture the current thread's stack contents and the kernel's thread list to understand what was running at the time of the fault.

The automation flow would look like this:

1. Build the firmware with debug symbols and a known test configuration.
2. Use JLinkExe to flash the device and start execution.
3. Run the test sequence — either by sending commands over a virtual COM port or by having the firmware execute a built-in self-test.
4. Monitor for completion or failure — I'd use a watchdog or timeout mechanism to detect hangs.
5. If a crash occurs, the J-Link halts the CPU, and the script extracts the crash dump to a file.
6. The script then resets the device and runs the next test case.

For CI integration, I'd wrap this in a script that returns appropriate exit codes and produces artifacts — the crash dump, test logs, and pass/fail summary — that can be archived. I'd also make sure the J-Link is configured with the correct target device and interface speed, and that the SWD connection is reliable for long test runs.

One important detail for medical devices: I'd separate the test harness from the production firmware build. The test build would include additional instrumentation — like a test mode that exercises specific code paths — but the production build would be clean. This avoids the risk of test code accidentally shipping.

**Possible follow-ups:**
- How would you handle the case where the device is unresponsive and the J-Link can't halt the CPU — what's your recovery procedure?
- How would you integrate this into a CI pipeline that runs nightly on multiple test stations?

---

## Q4: How would you approach setting up a constraint management system in Cadence Allegro for a mixed-signal PCB that has both high-speed digital interfaces (USB 2.0, SPI at 20 MHz) and sensitive analog sensor inputs?

**Answer:** Setting up a constraint management system for a mixed-signal board is about creating a hierarchy of rules that reflect the different electrical requirements of each signal class, and then making sure those rules are enforced throughout the design flow.

I'd start by defining the net classes in the Constraint Manager. The high-speed digital interfaces — USB 2.0 and SPI — would get their own classes with specific electrical constraints. For USB 2.0, that means differential pair constraints: 90-ohm differential impedance, controlled length matching within the pair, and a maximum total trace length. For SPI at 20 MHz, I'd set up single-ended impedance targets (typically 50 ohms) and length matching for the clock and data lines to control skew.

The analog sensor inputs would be a separate class with different priorities. Here, the constraints are less about impedance matching and more about isolation and noise control. I'd set up spacing rules that keep analog traces away from digital traces — for example, a larger clearance between analog nets and any net that switches at high frequency. I'd also define rules for guarding analog traces, like requiring ground pour on adjacent layers.

The key is the physical constraint sets. I'd create:

- **USB differential pair set**: 90-ohm differential, with specific line width and spacing based on the stackup, plus length matching rules.
- **SPI single-ended set**: 50-ohm controlled impedance, with length matching for the clock to data lines.
- **Analog input set**: wider traces for lower resistance, clearance rules to digital nets, and possibly a rule requiring a ground guard trace around sensitive analog paths.
- **Power net set**: appropriate widths for current carrying capacity, and clearance rules for high-voltage or high-current nets.

For the spacing rules, I'd use the Constraint Manager's region-based or class-to-class spacing. For example, I might set a rule that says analog nets must be at least 10 mils from any digital net, while digital-to-digital spacing can be tighter. This class-to-class spacing is where the real value of the Constraint Manager shows — it catches violations that a simple net-based rule would miss.

I'd also set up the physical layer assignments — which layers are used for what — and the via structures. For the mixed-signal board, I'd want to control which vias are allowed in the analog area versus the digital area, and I'd set up via arrays or specific via structures for the high-speed signals.

Finally, I'd run the constraint validation as part of the design flow, not just at the end. I'd set up the rules so that DRC runs continuously during layout, and I'd review the Constraint Manager's violation report before releasing the design. The goal is to catch issues while the layout is still easy to change, not after fabrication.

**Possible follow-ups:**
- How would you handle the conflict between keeping analog and digital grounds separate versus having a solid ground plane?
- What would you do if the board size constraints make it impossible to meet all the spacing rules — how would you prioritize?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a situation where the technical issue is actually straightforward — the real challenge is managing the human dynamics and the schedule pressure. My approach would be to first establish the facts, then align the teams, and then make a decision based on what's most practical for the project.

The first step is to get the actual documentation in front of everyone. I'd call a meeting with both teams and ask them to bring the hardware schematic, the sensor datasheet, and the firmware source code. The goal is not to assign blame but to establish ground truth. I'd walk through the I2C address configuration on the schematic — checking the address pins on the sensor — and then look at the firmware's I2C initialization code to see what address and register map it's actually using. This should take minutes, not hours, and it removes the "I'm confident I'm right" argument because we're looking at the actual implementation.

Once we've confirmed the mismatch, the next question is: what's the fastest path to a working system? There are typically three options:

1. **Fix the firmware**: If the hardware is already in fabrication and the sensor is fixed on the board, the firmware needs to be updated to use 10-bit addressing and the correct register map. This is usually the fastest fix if the firmware changes are localized.

2. **Fix the hardware**: If the hardware hasn't been fabricated yet, or if the address pins can be strapped differently, we could change the hardware. But with integration testing in two days, this is unlikely to be practical.

3. **Use a workaround**: In some cases, there might be a hardware workaround — like an address translator or a different I2C bus — but this is rare and usually adds complexity.

In most cases, the firmware fix is the right answer. I'd have the firmware team estimate the effort — if it's a matter of changing the address configuration and updating the register map, it might be a day of work. I'd also have them verify the fix on an evaluation board with the same sensor before touching the actual hardware.

The key part of this is the communication. I'd frame this as a process issue, not a people issue. The root cause is likely a communication gap — the hardware team used one datasheet revision, the firmware team used another, or the interface control document wasn't updated. I'd acknowledge that this happens in complex projects and focus on what we need to do to move forward.

I'd also make sure the fix is properly verified. With two days until integration testing, I'd want the firmware fix tested on the bench with the actual hardware, not just on an evaluation board. If that's not possible, I'd at least want a clear test plan for the first day of integration testing that specifically exercises the I2C communication.

Finally, I'd schedule a follow-up to update the interface documentation and add a checklist item for future projects — something like "verify I2C address and register map against the actual hardware before firmware development starts." The goal is to prevent this from happening again, not to punish anyone.

**Possible follow-ups:**
- What if the firmware team insists that the hardware is wrong and refuses to change their code — how would you handle that?
- How would you communicate this delay to management, especially if it impacts the integration testing schedule?