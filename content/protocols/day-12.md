# protocols — Day 12

## Q1: How would you approach designing a power management scheme for a battery-powered medical device that must maintain a real-time communication link while also meeting strict leakage current requirements during patient contact?

**Answer:** This is a classic tension in medical IoT design—you need continuous connectivity for monitoring, but patient safety and battery life impose conflicting constraints. I'd start by separating the problem into three domains: the patient-connected front end, the communication subsystem, and the power architecture that bridges them.

For the patient-connected portion, IEC 60601's leakage current limits (typically 10 µA for BF-type applied parts) mean the sensor front end must be galvanically isolated from the communication and processing stages. I'd use an isolated DC-DC converter with low coupling capacitance (ideally under 20 pF) and an isolated communication interface—either a digital isolator for I2C/SPI or an isolated UART. The key is keeping the isolation barrier between the patient side and anything that touches the outside world.

For the communication link itself, I'd design a duty-cycled scheme where the radio or wired interface wakes periodically to transmit buffered data, rather than maintaining a continuous stream. The duty cycle would be driven by clinical requirements—what's the maximum acceptable latency for an alarm condition versus routine telemetry? For a respiratory monitoring device, for example, waveform data might need near-real-time updates, but derived metrics like trend data could be batched.

On the power side, I'd use a hierarchical approach: a low-quiescent-current LDO for the always-on domain (real-time clock, wake-up logic, leakage monitoring), and switched regulators for the high-current subsystems (radio, processor, sensor front end) that can be powered down between transmissions. The firmware should have explicit power states—active, standby, sleep—with measured current budgets for each. I'd also include a fuel gauge with coulomb counting to track state of charge, since voltage-based estimation is unreliable with the pulsed loads of radio transmission.

Finally, I'd verify the design against both regulatory and battery-life requirements early—measuring leakage current with the isolation barrier in place, and characterizing the duty-cycled current profile over a simulated 7-day patient-worn scenario. The trade-off between communication latency and battery life should be a documented design decision, reviewed with clinical stakeholders, not an afterthought.

**Possible follow-ups:** How would you handle the case where the wireless link is lost and data needs to be buffered locally? What isolation technology would you choose for the communication interface, and why?

---

## Q2: You're debugging a system where a sensor on an I2C bus occasionally fails to acknowledge its address after the system has been running for several hours. The failure clears on reset. How would you approach this?

**Answer:** This pattern—intermittent failure after extended operation, cleared by reset—points to a few classic root causes. I'd approach it systematically rather than guessing.

First, I'd instrument the bus to capture the failure in action. A logic analyzer with deep memory, or a second microcontroller configured as a bus monitor, can record the exact sequence of events leading up to the missing ACK. I'd want to see whether the sensor is actually pulling SDA low for the ACK bit, whether clock stretching is involved, and whether the failure correlates with specific bus activity patterns.

The most common culprits in my experience are: (1) a marginal power supply that droops under load, causing the sensor's internal logic to brown out; (2) a bus capacitance issue where rise times become marginal at elevated temperatures; (3) clock stretching that the master isn't handling correctly; or (4) a firmware bug where the sensor's I2C state machine gets stuck if a transaction is interrupted mid-frame.

For the power hypothesis, I'd add a scope probe on the sensor's VDD pin and look for droop during bus activity—especially if other peripherals are switching simultaneously. For the bus timing hypothesis, I'd check rise times against the I2C spec for the operating mode, and consider whether the pull-up resistors are adequately sized for the total bus capacitance at the operating temperature.

For the clock stretching issue, I'd verify the master's driver actually supports it and has a timeout. Some sensors stretch the clock while they process data, and if the master has a fixed timeout that's too short, it can abort the transaction mid-way, leaving the sensor in an undefined state.

For the firmware state machine hypothesis, I'd review the sensor's I2C interrupt handler for any path where a partial transaction could leave the peripheral in a busy state. A common bug is not clearing the interrupt flag or not handling NACK conditions gracefully.

The reset-clears-it symptom is a strong clue: it suggests the sensor's internal state is corrupted, not that the bus itself is broken. I'd focus on what could corrupt that state—a glitch on the clock line, a missed interrupt, or a power glitch. I'd also check whether the sensor has a watchdog or a way to recover from a stuck state without a full reset.

**Possible follow-ups:** How would you add fault tolerance to the firmware to recover from this condition without a manual reset? What would you look for in the sensor's datasheet to narrow down the likely cause?

---

## Q3: How would you approach implementing a firmware update mechanism for a medical device that communicates over CAN-FD, where the update must be robust against power loss and communication errors?

**Answer:** Firmware updates on medical devices are safety-critical—a failed update can brick the device or leave it in an undefined state. I'd design the mechanism with three priorities: atomicity, verifiability, and recoverability.

For atomicity, I'd use a dual-bank flash architecture. The device boots from bank A, and the new firmware is written to bank B. Only after the entire image is received, verified, and validated does the bootloader switch the active bank. If power is lost mid-update, the device simply boots from the old, known-good image. This is the most robust approach and worth the extra flash cost.

For the communication protocol itself, I'd use a block-based transfer with sequence numbers, CRC-32 or better per block, and an application-level checksum over the entire image. CAN-FD's larger payload (up to 64 bytes) is well-suited to this—I'd use a fixed block size, say 32 or 64 bytes of payload per frame, with a header containing the block index and a trailer with the CRC. The receiver sends an ACK per block, and the sender retransmits on NACK or timeout. I'd also include a "resume" capability so an interrupted update can restart from the last acknowledged block rather than from the beginning.

For verifiability, after the image is fully received, the bootloader would compute a SHA-256 hash and compare it against the hash transmitted in the update manifest. Only then would it validate the image's integrity—checking the vector table, stack pointer, and entry point—before marking the new bank as valid.

For recoverability, I'd implement a fallback mechanism: if the new image fails to boot (detected by a watchdog timeout or a boot flag that the application clears after successful initialization), the bootloader automatically reverts to the previous bank. This gives a self-healing behavior that's critical for field reliability.

Finally, I'd consider the regulatory angle. For a medical device, the update mechanism itself should be documented in the design history file, and the update process should be validated—including failure injection testing for power loss at various points, communication errors, and corrupted images.

**Possible follow-ups:** How would you handle the case where the device is in the middle of an update and the battery dies? How would you ensure the update image is authentic and not tampered with?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** This is a classic trade-off between simplicity and reliability, and the right answer depends on the system's requirements. I'd guide the team through a structured evaluation rather than picking a side immediately.

First, I'd clarify the constraints. What are the data rates and update frequencies for each sensor? What's the consequence of a missed or delayed reading? For a medical device, if any sensor provides safety-critical data, the reliability requirements are much higher than for non-critical telemetry.

The software multiplexer approach has real appeal: it saves pins, saves cost, and reduces board complexity. But it introduces a single point of failure—if the multiplexing logic has a bug, all four sensors are affected. It also creates timing challenges: if two sensors need to transmit simultaneously, one has to wait, which could violate latency requirements. And debugging becomes harder because you're dealing with interleaved data streams on a single peripheral.

The four-UART approach is more robust but costs pins, board space, and potentially a larger microcontroller. It also simplifies the firmware—each sensor gets a dedicated driver with its own buffer and state machine, and there's no cross-sensor interference.

I'd frame the decision around three questions: (1) What are the latency and throughput requirements for each sensor, and can the multiplexer meet them under worst-case conditions? (2) What's the failure mode if the multiplexer has a bug—is it a nuisance or a safety issue? (3) What's the development and debug cost of each approach?

If the sensors have modest data rates and the system can tolerate some latency, the multiplexer might be acceptable—but I'd require a detailed timing analysis and a robust protocol with per-sensor framing and error detection. If any sensor is safety-critical or has tight timing requirements, I'd lean toward dedicated UARTs, or at least a hybrid approach where the critical sensor gets its own peripheral and the non-critical ones share.

I'd also raise a middle-ground option: use a UART with DMA and a well-structured protocol layer that can handle multiple logical channels over a single physical link. This is essentially what the junior engineer proposed, but with more rigor around the protocol design. The key is whether the team can commit to the engineering effort required to make it reliable.

Ultimately, I'd ask the team to prototype the multiplexer approach and measure worst-case latency and error rates under realistic conditions. Data beats opinion. If the measurements show it meets requirements with margin, it's a valid choice. If not, the four-UART approach is justified.

**Possible follow-ups:** How would you structure the protocol to ensure that a bug in one sensor's driver can't corrupt data for the others? What testing would you require before accepting the multiplexer approach?

---

## Q5: How would you approach verifying that a mixed-signal PCB design meets its electromagnetic compatibility (EMC) requirements before committing to the full regulatory compliance testing process?

**Answer:** EMC compliance testing is expensive and time-consuming, so the goal is to catch issues as early as possible—ideally at the design stage, then at the bench level, before ever booking a test lab. I'd approach this as a layered verification strategy.

At the design stage, I'd focus on layout and grounding. For a mixed-signal board, the critical decisions are: where to split (or not split) the ground plane, how to route high-speed signals, and how to decouple power. I'd review the stack-up for controlled impedance on high-speed traces, ensure return current paths are continuous under every signal trace, and check that clock lines and other periodic signals are routed away from I/O connectors. I'd also verify that all high-speed signals have proper termination and that the decoupling capacitor placement matches the manufacturer's recommendations for the specific ICs.

For the power distribution, I'd check that switching regulators have proper input and output filtering, and that the switching node is kept small and away from sensitive analog circuitry. I'd also review the grounding of the isolation barrier if the design has one—the return path for the isolation capacitance is a common source of radiated emissions.

At the bench level, I'd do a pre-scan using a near-field probe and a spectrum analyzer. This won't give you the same results as a certified lab, but it can identify dominant emission sources—clock harmonics, switching regulator noise, or cable radiation. I'd probe the board systematically, looking for emissions at the fundamental and harmonics of every clock and data rate in the system. I'd also do a basic immunity check by injecting noise into the power supply and I/O lines to see if the device resets or corrupts data.

For the firmware, I'd verify that the device is in its worst-case emission mode during testing—typically with all peripherals active and the processor running at full speed. I'd also check that any spread-spectrum clocking features are enabled if the design uses them.

Finally, I'd review the design against the relevant EMC standards early—for a medical device, that's typically IEC 60601-1-2, which references CISPR 11 for emissions and IEC 61000-4-x for immunity. I'd identify which tests are most likely to fail based on the design's characteristics—for example, a device with long cables is more susceptible to ESD and surge, while a device with a switching regulator might have conducted emissions issues.

The key is to treat EMC as a design constraint from the start, not a test to be passed at the end. Every layout decision, every connector choice, every filtering component affects the outcome. By the time the board goes to the lab, I'd want to be confident that the design is fundamentally sound, and that the remaining risk is in the details of the specific test setup rather than in the architecture.

**Possible follow-ups:** How would you prioritize which EMC tests to focus on during pre-compliance testing? What would you do if a near-field scan revealed a significant emission at a clock harmonic?