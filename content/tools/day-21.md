# tools — Day 21

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** I'd structure this around Zephyr's Kconfig and devicetree overlay system, which is designed exactly for this kind of variant management. The core approach is to keep a single application source tree and use build-time configuration to select between production and development variants.

First, I'd define the production configuration as the baseline in the application's `prj.conf` and base devicetree. This ensures that a plain `west build` produces the release artifact. Then I'd create a development overlay — something like `boards/my_board_dev.overlay` — that swaps the sensor node's compatible string to point to a mock driver, and a `prj_dev.conf` that enables logging, shell, and other debug features.

For the mock sensor, I'd implement it as a separate driver that conforms to the same sensor driver API as the real device. The devicetree overlay changes the `compatible` property on the sensor node, so the devicetree-generated code pulls in the mock driver instead of the real one. The application code itself never changes — it just calls the standard sensor API.

The build invocation becomes something like:
```
west build -b my_board -- -DOVERLAY_CONFIG=prj_dev.conf -DDTC_OVERLAY_FILE=boards/my_board_dev.overlay
```

I'd also use Kconfig `select` statements carefully so that enabling the development configuration automatically pulls in the debug features, reducing the chance of someone building a dev image with production settings. For CI, I'd set up two build jobs — one for each configuration — so both are verified continuously.

**Possible follow-ups:**
- How would you ensure that the mock sensor driver can't accidentally end up in a production build?
- How would you handle a case where the development build needs a different flash partition layout for things like a shell or logging storage?

---

## Q2: How would you approach using a logic analyzer to debug an I2C bus where the slave device occasionally stops responding after several hours of operation, but only when the system is under load — for example, when a motor is running in a medical device?

**Answer:** This is a classic intermittent failure that points to either a timing violation, a power integrity issue, or a firmware state-machine problem. I'd approach it in stages.

First, I'd set up the logic analyzer to capture the I2C bus continuously with a deep buffer, triggering on the first NACK or the first timeout. I'd decode the protocol in the analyzer software so I can see the full transaction sequence — address byte, register, data, and the ACK/NACK position. The key is to capture not just the failing transaction but the several seconds of traffic leading up to it, because the root cause is often a corrupted prior transaction that left the slave in a bad state.

Second, I'd correlate the I2C captures with the motor activity. I'd use a second analog channel on the logic analyzer to monitor the motor driver's enable signal or current sense, so I can see whether the failure always happens during motor operation or specifically at motor start/stop transients. If the failure correlates with motor activity, I'd suspect ground bounce or supply droop affecting the I2C logic levels.

Third, I'd look at the timing margins in the captured waveforms. I2C has specific setup and hold time requirements, and under marginal conditions — like a slightly drooping supply or increased noise — the slave might miss a setup time that was previously marginal. I'd measure the actual rise times, setup times, and hold times in the capture and compare them against the slave's datasheet specifications.

If the timing looks clean, I'd then suspect the slave's internal state machine. Some I2C slaves have errata where they can hang if they receive an incomplete transaction — for example, a start condition followed by a stop without a full byte. I'd look for any unusual bus activity before the failure, like a spurious start/stop from a firmware bug or a glitch on SDA/SCL from the motor noise.

Finally, I'd add a hardware fix in parallel — like a ferrite bead on the motor supply or improved decoupling — and re-run the test to see if the failure rate changes. This helps confirm whether it's a power integrity issue versus a firmware issue.

**Possible follow-ups:**
- What specific timing parameters would you measure on the I2C bus to check for marginal violations?
- How would you distinguish between a slave that's hung internally versus one that's being held in reset or power-cycled?

---

## Q3: How would you approach setting up a component library management strategy in Altium Designer for a medical device project that needs to maintain strict revision control and regulatory traceability?

**Answer:** For a medical device, the component library isn't just a design convenience — it's part of the design history file (DHF) and needs to be traceable. I'd approach this with a few key principles.

First, I'd establish a single source of truth for components. In Altium, that means using a managed library system — either Altium 365 or an on-premise Altium Vault — rather than scattered schematic libraries and PCB footprint libraries. Every component gets a unique item ID, and the schematic symbol, PCB footprint, and 3D model are all linked to that single managed item.

Second, I'd enforce a strict review and approval workflow. A component can't be used in a design until it's been through a formal review process — symbol checked against the datasheet, footprint verified against the manufacturer's recommended land pattern, and the 3D model validated for mechanical interference. The approval is recorded in the vault, so there's an audit trail of who reviewed what and when.

Third, I'd tie each component to its sourcing and compliance data. For medical devices, this means storing things like the manufacturer part number, the RoHS/REACH status, and any conflict mineral declarations. Altium's supplier links can pull this in, but I'd also maintain a controlled BOM export that captures the approved manufacturer and part number for each component.

For revision control, I'd use Altium 365's versioning so that every change to a library component creates a new revision with a history. The design file references the specific revision of each component, so if a component changes — say, a footprint correction — the design history shows exactly which revision was used in which design release.

Finally, I'd set up regular audits of the library against the actual components received from suppliers. This catches issues like a manufacturer changing the package dimensions without changing the part number, which is a real risk in medical devices where a footprint mismatch can cause a field failure.

**Possible follow-ups:**
- How would you handle a situation where a component becomes obsolete and needs to be replaced mid-project?
- What information would you require to be filled in on a component's datasheet before you'd approve it for use?

---

## Q4: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at a specific frequency is coming from a switching regulator's fundamental frequency or from a harmonic of a digital clock, and how would you confirm your hypothesis?

**Answer:** This is a common pre-compliance debugging scenario, and the key is to use both frequency-domain and time-domain information to identify the source.

First, I'd calculate the expected frequencies. If the switching regulator runs at, say, 400 kHz, I'd look for its harmonics at 800 kHz, 1.2 MHz, and so on. If the digital clock is, say, 25 MHz, I'd look for its harmonics at 50 MHz, 75 MHz, 100 MHz, etc. The failure frequency will often be close to one of these — but not exactly, because the actual switching frequency may drift slightly with load.

Second, I'd use the near-field probe to map the spatial distribution of the emission. I'd move the probe across the board while watching the spectrum analyzer at the failure frequency. A switching regulator tends to radiate from the inductor, the switching node, and the input/output loops. A digital clock tends to radiate from the clock trace, the oscillator, and any long parallel traces. The spatial pattern often distinguishes them immediately.

Third, I'd use the time-domain capability of the spectrum analyzer — or a separate oscilloscope — to look at the signal's characteristics. A switching regulator's emission is typically broadband noise with a fundamental and harmonics that change with load. A digital clock's emission is typically a narrowband signal at the clock frequency and its harmonics, with very stable frequency. I'd use the zero-span mode on the spectrum analyzer to see how the amplitude varies over time — if it pulses with the motor or load changes, it's more likely the regulator.

To confirm the hypothesis, I'd do a controlled experiment. If I suspect the switching regulator, I could temporarily change its switching frequency — say, by changing a resistor value — and see if the emission frequency shifts accordingly. If I suspect the clock, I could temporarily disable the clock output or change its frequency and see if the emission disappears or shifts. This is the definitive test.

Finally, I'd check the coupling path. Even if the source is the regulator, the emission might be radiating from a cable or a long trace that's acting as an antenna. I'd use the near-field probe to trace the signal path from the source to the radiating element, because the fix might be at the antenna (e.g., ferrite bead on the cable) rather than at the source.

**Possible follow-ups:**
- How would you distinguish between a harmonic of the clock and a harmonic of the regulator if they happen to coincide at the same frequency?
- What near-field probe characteristics would you look for to ensure you're getting accurate measurements?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the UART protocol than what the hardware actually implements — the firmware is expecting a specific baud rate and data frame format (8 data bits, even parity, 1 stop bit), but the hardware's UART peripheral is configured for a different configuration (8 data bits, no parity, 1 stop bit). The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a classic integration failure waiting to happen, and the first thing I'd do is not assign blame. Both teams are confident, which means there's likely a documentation gap — the interface control document (ICD) or the hardware specification wasn't clear enough, or it was interpreted differently.

My first step would be to call a short, focused meeting with the leads from both teams. I'd bring the actual hardware schematic, the firmware source code, and any interface documentation. The goal is to establish facts, not opinions. I'd ask the firmware lead to show me exactly where the UART configuration is set in the code, and I'd ask the hardware lead to show me the UART peripheral configuration in the schematic or the microcontroller's configuration registers.

If the documentation is ambiguous, I'd acknowledge that immediately — that's often the root cause. If the documentation is clear and one side deviated from it, I'd still avoid blame and focus on the fix.

The critical question is: which configuration is correct for the system? If the hardware is already in fabrication, changing the hardware is likely not feasible in two days. So the question becomes whether the firmware can be changed to match the hardware. If the UART is connected to a specific peripheral — say, a Bluetooth module or a sensor — the peripheral's datasheet will dictate the required configuration. If the peripheral requires 8-E-1, then the firmware needs to change. If the peripheral can accept either, then I'd pick the one that's already implemented in hardware to minimize changes.

I'd then work with the firmware team to estimate the effort to change the configuration. In most cases, this is a one-line change in the UART initialization code, plus a quick regression test. That's very feasible in two days. The bigger risk is if the protocol is more complex — say, the frame format includes a specific CRC or escape sequences that differ between the two versions. In that case, I'd need to assess whether the change is still feasible or whether we need to slip the integration date.

I'd also use this as a trigger to review the ICD process. After the immediate issue is resolved, I'd propose adding a formal interface verification step — a checklist that both teams sign off on before integration testing. This prevents the same class of issue from recurring with other interfaces like SPI, I2C, or CAN.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their configuration is correct because it works on the evaluation board?
- What would you do if the hardware team says the UART configuration is correct because it's what the peripheral's datasheet specifies, but the firmware team says the ICD says otherwise?