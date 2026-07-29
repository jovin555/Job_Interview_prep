# space-rad-hard — Day 8

## Q1: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is inherently vulnerable in radiation environments because it uses open-drain lines with weak pull-ups and a stateful protocol that can hang if a slave device holds SCL or SDA low after an upset. My approach would start with the physical layer: use radiation-tolerant bus buffers or isolators (e.g., I²C hot-swap buffers with built-in stuck-bus recovery) to segment the bus so a fault on one segment doesn't bring down the entire system. Each segment should have its own pull-up resistors, sized for the capacitive load of that segment only.

For the protocol layer, I would implement a watchdog timer on the master that monitors bus activity. If SCL or SDA remains low longer than the maximum expected clock stretch time, the master should toggle the bus lines through a GPIO-controlled switch or cycle power to the offending segment. Each slave transaction should include a CRC or checksum, and the master should retry failed transactions with a back-off strategy. I'd also consider using a redundant I²C bus with a second controller; the firmware can switch buses if the primary bus experiences persistent errors.

For the sensor nodes themselves, I would use radiation-tolerant I²C devices where available, or add external protection like series resistors (to limit latch-up current) and Schottky clamps on the bus lines. The firmware should periodically reset the bus state machine (by generating nine clock pulses on SCL while SDA is high) to recover from stuck states without a full power cycle.

**Possible follow-ups:** How would you handle the case where a slave device's internal register state gets corrupted but the I²C interface itself still works? What trade-offs would you consider between using a single shared bus versus multiple dedicated point-to-point connections?

---

## Q2: You are reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The immediate concern is that a COTS linear regulator with no radiation characterization could fail in several ways under total ionizing dose: the bandgap reference may drift, causing the output voltage to shift outside the FPGA's tolerance; the pass transistor's gain may degrade, increasing dropout voltage or reducing current capability; or the regulator could suffer single-event transients that cause voltage spikes on the 1.2V rail, potentially corrupting FPGA logic or causing latch-up.

The fact that the FPGA's tolerance (±5%) is wider than the regulator's specified tolerance (±2%) gives some margin, but that margin assumes the regulator stays within its datasheet limits — which it won't under radiation. I would first check whether a radiation-characterized equivalent exists (e.g., a QML-qualified linear regulator from a trusted manufacturer). If not, I would consider using a radiation-tolerant DC-DC converter instead, even though it adds complexity and ripple, because converters are more likely to have some radiation data available.

If a linear regulator is the only option, I would recommend radiation testing of the specific part at the expected dose rate and total dose for the mission. I'd also add output voltage monitoring via an ADC with a threshold that triggers a system reset or graceful shutdown if the voltage drifts outside the FPGA's tolerance. A secondary LDO or a precision shunt regulator could provide additional post-regulation if the primary regulator's output drifts high.

**Possible follow-ups:** How would you design the output voltage monitoring circuit to be itself radiation-tolerant? What if the mission total dose is only 10 krad — would you still require testing, or would you accept the risk?

---

## Q3: How would you approach implementing a fault-tolerant bootloader for a microcontroller in a space-deployed system, given that a corrupted bootloader could render the system unrecoverable?

**Answer:** The bootloader is the most critical piece of firmware because if it's corrupted, the system may not be able to load or update its application code. My approach would use a multi-stage boot strategy with hardware-enforced fallback.

First, I'd store the bootloader in radiation-hardened or at least radiation-characterized non-volatile memory (e.g., MRAM or a qualified serial flash) with ECC protection. The bootloader itself should be small and simple — minimal initialization, just enough to validate and load the application. I'd use a two-bank flash architecture: bank A holds the primary bootloader, bank B holds a golden copy. On reset, a small hardware state machine or a separate watchdog timer checks a "boot valid" flag; if the primary bootloader fails its CRC check, the hardware forces boot from the golden copy.

The bootloader should verify the application image using a cryptographic hash (e.g., SHA-256) before jumping to it. If the hash fails, it should attempt to load a backup application image from a separate memory region. If both application images are corrupted, the bootloader should enter a recovery mode that listens on a dedicated communication interface (e.g., a UART or CAN bus) for a new image, using a simple protocol that doesn't rely on the main application.

I'd also implement a "safe boot" pin or command that forces the system into recovery mode regardless of the bootloader state, so ground operators can recover the system even if the bootloader's decision logic is compromised. The bootloader should be stored in write-protected memory after initial programming, with write access only possible through a dedicated hardware sequence (e.g., a specific GPIO pattern or a physical jumper).

**Possible follow-ups:** How would you handle the case where a firmware update is interrupted mid-write, leaving both application images partially corrupted? What metrics would you monitor to detect that a bootloader corruption has occurred?

---

## Q4: Imagine you are leading a team designing a radiation-hardened control board for a satellite payload. During a design review, a junior engineer presents a plan to use a single, large FPGA for all digital processing, with TMR applied only to the critical state machines. The engineer argues that applying TMR to the entire design would exceed the FPGA's logic capacity and that the non-critical logic (e.g., configuration registers, housekeeping interfaces) is "safe enough" without redundancy. How would you handle this disagreement?

**Answer:** I would first acknowledge the engineer's practical concern about logic capacity — it's a real constraint, and blindly applying TMR everywhere is not always the right answer. However, I would challenge the assumption that "non-critical" logic is safe without redundancy, because in a radiation environment, a single upset in a configuration register could cause a housekeeping interface to send incorrect telemetry, which might lead ground operators to make wrong decisions about the satellite's health. Similarly, an upset in a seemingly non-critical state machine could propagate to critical logic through shared resources like memory buses or interrupt lines.

My approach would be to work with the engineer to perform a systematic failure modes and effects analysis (FMEA) on the entire design, not just the obviously critical parts. We would identify every flip-flop, register, and state machine, and classify each by the severity of a single upset: does it cause loss of mission, degradation of performance, or no effect? For items classified as "no effect" (e.g., status LEDs that are purely informational), TMR is unnecessary. But for anything that could cause incorrect data to be transmitted, incorrect control signals, or system lock-up, we need mitigation.

For the capacity problem, I would explore alternatives to full TMR: using Hamming-coded registers instead of triplicated ones, implementing error detection and correction (EDAC) on memory blocks, or using radiation-hardened by design (RHBD) FPGA cells that are inherently more tolerant. I might also suggest partitioning the design across two smaller FPGAs if the single FPGA is truly too small, which adds the benefit of physical separation for fault isolation.

Finally, I would emphasize that the cost of a single undetected upset in "non-critical" logic could be a multi-million-dollar mission failure, and that the engineering effort to add TMR or EDAC is small compared to that risk. I'd ask the engineer to present a risk assessment with specific upset scenarios and their consequences, so we can make a data-driven decision rather than a subjective one.

**Possible follow-ups:** How would you handle the situation if the engineer still disagrees after your discussion, and the schedule is tight? What if the FPGA vendor provides a TMR tool that automatically triplicates the design — would you trust it without manual review?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code?

**Answer:** A SEFI is one of the most challenging faults to test because it can manifest in many ways — the microcontroller might halt, enter an infinite loop, corrupt its program counter, or disable its clock. The test plan needs to cover both detection and recovery, and it must be performed under representative radiation conditions.

First, I would define the recovery mechanism in the design: typically a combination of a watchdog timer (preferably a windowed watchdog with a separate clock source) and a voltage supervisor that can assert a hardware reset. The test plan would verify that these recovery circuits work correctly under normal conditions, then under simulated fault conditions.

For the radiation testing phase, I would work with a test facility that can provide heavy-ion or proton beams with sufficient linear energy transfer (LET) to induce SEFIs. The test setup would include:
- A current monitor on the microcontroller's power rail to detect latch-up events
- A logic analyzer or oscilloscope capturing the watchdog output, reset line, and a "heartbeat" GPIO from the microcontroller
- A host computer that logs the system's state and automatically detects when the microcontroller stops responding

The test procedure would expose the microcontroller to the beam while it runs a simple test program that toggles a heartbeat pin and periodically sends status messages over a UART. The host computer would measure the time between heartbeats and flag any gap longer than the watchdog timeout period. If the watchdog triggers a reset, the host should see the microcontroller re-initialize and resume normal operation. We would repeat this across multiple beam runs at different LET values and angles to characterize the SEFI cross-section.

Beyond radiation testing, I would also perform fault injection testing on the bench: using a debugger to corrupt the program counter, stack pointer, or key registers, and verifying that the watchdog catches the fault and the system recovers cleanly. I would also test corner cases like a SEFI occurring during a firmware update, or during a critical sensor readout, to ensure the recovery doesn't leave the system in an inconsistent state.

**Possible follow-ups:** How would you determine the acceptable recovery time for your system — is a watchdog timeout of 1 second acceptable, or do you need faster recovery? How would you test the case where the SEFI corrupts the watchdog timer itself?