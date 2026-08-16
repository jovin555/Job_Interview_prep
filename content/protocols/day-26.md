# protocols — Day 26

## Q1: How would you approach designing a communication architecture for a medical device where a central controller needs to communicate with multiple sensor modules, some requiring deterministic real-time response and others generating high-volume data, while keeping the system modular and testable?

**Answer:** I'd start by separating the requirements rather than trying to find one protocol that does everything. First, I'd categorize each sensor by its actual constraints: latency bounds, data volume, update rate, and criticality. For deterministic real-time sensors, I'd look at protocols with built-in prioritization or scheduled access—CAN-FD is often a good fit because message arbitration is handled in hardware and priority is inherent to the protocol. For high-volume data, I'd consider whether that data truly needs to share the same bus or whether a dedicated high-speed link (like SPI or USB) makes more sense. A common mistake is forcing everything onto one bus for simplicity, which creates coupling between different timing domains.

For modularity, I'd define a clean abstraction layer between the application and the transport—each sensor module gets a logical interface with standardized read/write/configure operations, and the underlying protocol implementation is swappable. This also makes testing easier: you can test the application logic against simulated sensor modules without real hardware, and test each protocol implementation against a protocol conformance harness. I'd also design the system so that a failure in one sensor module—say, a bus hang or a malformed message—doesn't take down communication with other modules. That might mean per-module fault isolation, timeouts, and a defined recovery sequence.

**Possible follow-ups:** How would you decide whether to use a single bus or multiple buses? What role would an RTOS play in managing the different timing requirements?

---

## Q2: You're debugging a system where a UART link between a microcontroller and a wireless module works reliably at 9600 baud but produces frequent framing errors at 115200 baud. The link is approximately 10 centimeters on the same PCB. How would you approach this?

**Answer:** Since the trace is short and on the same PCB, I'd first question whether signal integrity is the primary suspect—at 115200 baud over 10 cm, that's unlikely to be a transmission-line issue. I'd focus on the clock accuracy and baud rate tolerance. At 9600 baud, the timing margin is much more forgiving; at 115200, the bit period shrinks by a factor of 12, so the same absolute clock error becomes a much larger fraction of a bit period. I'd check the actual clock source: if the microcontroller is using an internal RC oscillator, its accuracy might be specified at ±1–3% or worse over temperature and voltage, and that could exceed the UART's tolerance for framing errors.

I'd measure the actual baud rate on a scope or logic analyzer—both the microcontroller's TX and the wireless module's TX—to see the real frequency error. I'd also check whether the wireless module has its own crystal or uses a less accurate internal oscillator. If the error is borderline, I'd look at whether the UART peripheral supports oversampling modes or baud rate adjustment to center the sampling point. I'd also verify the voltage levels: if the wireless module runs at a different I/O voltage and the interface relies on level shifting, marginal rise/fall times could contribute to sampling errors at higher baud rates. Finally, I'd check for any clock configuration issues—for example, if the UART clock divider rounds poorly at 115200, the actual generated baud rate might be off by more than expected.

**Possible follow-ups:** How would you determine the maximum acceptable clock error for a given baud rate? What if the problem only appears at temperature extremes?

---

## Q3: How would you approach implementing end-to-end data integrity protection for a CAN-FD message carrying a safety-critical payload, beyond what the controller's built-in CRC provides?

**Answer:** The CAN-FD controller's CRC protects against bit errors during transmission on the bus, but it doesn't protect against several other failure modes: the message being routed to the wrong node, the data being misinterpreted due to a software bug, or a stale message being delivered after a timeout. For end-to-end protection, I'd add an application-layer integrity mechanism that covers the entire data path from the sensor's internal state to the consuming application.

I'd start with a message counter or sequence number to detect missing or duplicated messages, and a timestamp or freshness indicator to detect stale data. For the payload itself, I'd add a CRC or checksum computed over the full message content—including the message ID, sequence number, and payload—so that any corruption or misrouting is detected. The choice of CRC polynomial depends on the criticality and the expected error patterns; a 16-bit CRC is often reasonable, but for higher assurance, a longer CRC or even a cryptographic hash might be justified if the threat model includes intentional tampering.

I'd also think about how the receiver responds to a detected integrity failure. The safest approach is usually to reject the message and enter a defined safe state, but that needs to be balanced against availability—if the system rejects too aggressively, it might shut down unnecessarily. I'd define a threshold: a single bad message might trigger a retry, while repeated failures escalate to a fault condition. The integrity mechanism should be tested with fault injection—corrupting bits, dropping messages, reordering messages—to verify the detection and response logic works as designed.

**Possible follow-ups:** How would you handle the case where the sequence number and CRC are themselves corrupted in a way that passes the check? How would you integrate this with ISO 14971 risk analysis?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single I2C bus at 400 kHz to connect five sensors, a real-time clock, and an EEPROM, all on a 30-centimeter PCB with long traces. The engineer argues that the bus capacitance is within the 400 pF limit. How would you guide the team to evaluate this approach?

**Answer:** I'd acknowledge that the engineer has done the first-level check—bus capacitance is indeed a key constraint for I2C—but I'd guide the team to look beyond just the raw capacitance number. First, I'd ask whether the 400 pF figure accounts for all sources: each device's pin capacitance, trace capacitance (which for 30 cm of typical PCB trace could be significant), connector capacitance if any, and the input capacitance of any protection circuitry. I'd also ask whether the capacitance calculation includes margin for manufacturing variation and temperature effects.

Then I'd raise the question of signal integrity at 400 kHz with long traces. Even if the total capacitance is within spec, long traces can introduce other issues: ringing, reflections at discontinuities, and crosstalk from adjacent signals. I'd ask whether the layout has been reviewed for trace routing—are the SDA and SCL lines kept together, away from noisy signals? Is there a ground plane underneath?

I'd also raise the practical issue of seven devices on one bus. Even if electrically feasible, there are operational concerns: address conflicts (many sensors have limited address options), bus contention, and the fact that a single stuck device can hang the entire bus. I'd ask whether the engineer has considered the failure modes—what happens if one sensor holds SCL low (clock stretching) indefinitely? Is there a bus recovery mechanism?

Finally, I'd ask about the actual bandwidth needs. At 400 kHz, the theoretical throughput is 50 kbytes/s, but with seven devices sharing the bus, each device's effective bandwidth is much lower. I'd ask the engineer to calculate whether each sensor's data rate requirement is actually met, including protocol overhead, addressing, and any required polling intervals. If the answer is marginal, I'd suggest alternatives: splitting into two buses, using a multiplexer, or considering SPI for the high-bandwidth devices.

**Possible follow-ups:** How would you determine the actual trace capacitance for a 30 cm trace? What would you recommend if the bus capacitance exceeds the limit—what are the options?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** I'd start by separating the immediate technical problem from the process issue. The first priority is to understand the nature of the protocol error—is it a fundamental misunderstanding of the protocol specification, an implementation bug, or a misinterpretation of the requirements? I'd work with the engineer to reproduce the failure, isolate the root cause, and develop a fix. Depending on the severity, I'd assess whether the fix can be done in firmware/software or whether hardware changes are needed—hardware changes would be much more costly at this stage.

Once the immediate issue is addressed, I'd focus on the process gap that allowed the error to go undetected until compliance testing. I'd ask: was there a protocol conformance test plan? Were there design reviews that should have caught this? Was there adequate unit testing or integration testing before the compliance phase? I'd work with the team to understand where the verification process broke down and what checks should be added to catch similar issues earlier in future projects.

For the junior engineer specifically, I'd approach this as a coaching opportunity rather than a blame situation. I'd review the error with them in a constructive way—helping them understand the root cause and the broader context of why the protocol works the way it does. I'd also make sure they understand the regulatory implications: in medical devices, compliance testing is not just a formality; it's the verification that the device meets safety and performance requirements. A protocol error that affects communication with a safety-critical sensor is exactly the kind of issue that compliance testing is designed to catch.

I'd also document the incident—not to assign blame, but to capture the lessons learned. This might include updating the design review checklist, adding specific protocol conformance tests to the verification plan, or establishing a peer review requirement for communication protocol implementations. The goal is to ensure the same class of error doesn't recur, and that the team's processes improve as a result of the experience.

**Possible follow-ups:** How would you communicate this delay to project stakeholders? What specific verification steps would you recommend adding to prevent similar issues in the future?