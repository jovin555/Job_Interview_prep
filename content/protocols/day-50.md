# protocols — Day 50

## Q1: How would you approach designing a communication architecture for a medical device where one sensor module requires deterministic, low-latency response for closed-loop control, while another module generates high-volume telemetry that can tolerate delay, and both need to coexist on the same physical network?

**Answer:** I'd start by quantifying the requirements on both sides before committing to a bus topology. For the closed-loop sensor, I need to know the worst-case acceptable latency, the jitter tolerance, and whether the control loop is truly closed-loop (meaning a missed or late message could cause a safety issue) or just time-sensitive. For the telemetry module, I need the sustained data rate, burst characteristics, and how much delay is actually tolerable.

With those numbers in hand, I'd evaluate whether a shared bus is even the right choice. CAN-FD is often attractive here because it provides message prioritization through arbitration — a safety-critical message with a lower identifier wins arbitration over lower-priority telemetry, giving bounded latency for the critical path. The key is that CAN's arbitration is non-destructive and deterministic, so as long as I've done the worst-case bus loading analysis, I can guarantee the critical message gets through.

However, I'd also consider whether the two functions should be physically separated. If the closed-loop sensor needs, say, sub-millisecond response and the telemetry is saturating the bus, the cleaner architecture might be a dedicated point-to-point link (SPI or a dedicated UART) for the control path, with the telemetry on a separate bus. This avoids the complexity of priority inversion, message filtering, and the subtle timing interactions that come with sharing a medium.

If a shared bus is necessary, I'd design the protocol layer carefully: the closed-loop sensor gets a fixed, high-priority slot or message ID, the telemetry is sent in lower-priority messages that yield during arbitration, and I'd implement a scheduling scheme where telemetry transmissions are gated to prevent them from ever flooding the bus during critical control periods. I'd also add monitoring to detect when the bus is approaching saturation so the system can degrade gracefully — for example, by reducing telemetry rate before the control path is affected.

**Possible follow-ups:** How would you verify that the worst-case latency for the critical message is actually met under full bus load? What happens if a third module is added later that also needs deterministic communication?

---

## Q2: You're debugging a system where a UART link between a microcontroller and a wireless module occasionally drops the first few bytes of a transmission after the system has been idle for several minutes. The link uses hardware flow control (RTS/CTS). How would you approach this?

**Answer:** This pattern — first bytes lost after a long idle period — points me toward a few specific suspects. The first thing I'd look at is the sleep/wake behavior of both devices. After several minutes of idle, one or both sides may have entered a low-power state where the clock source changes (e.g., switching from an external crystal to an internal RC oscillator) or where the UART peripheral is powered down. When the link wakes, the baud rate may be slightly off until the clock stabilizes, causing the receiver to sample the first few bits incorrectly.

I'd also examine the flow control handshaking sequence. With RTS/CTS, the transmitter should assert RTS and wait for CTS before sending. If the wireless module's firmware has a delay between when it asserts CTS and when its UART receiver is actually ready — perhaps because it's waking from sleep — the first bytes can be sent into a receiver that isn't listening yet. This is a classic race condition that only appears after long idle periods because the module has had time to enter a deeper sleep state.

My debugging approach would be: first, capture the traffic with a logic analyzer or oscilloscope on both the TX/RX lines and the RTS/CTS lines simultaneously. I'd look at the timing relationship between CTS assertion and the first data byte. If CTS goes high and data starts immediately, but the module's UART isn't enabled until later, that confirms the handshake timing issue. I'd also check whether the microcontroller's UART is disabling its receiver during sleep and whether the first-byte loss correlates with any clock source switching.

The fix would depend on the root cause. If it's a wake-up timing issue, I'd add a small delay between CTS assertion and data transmission, or have the transmitter send a "wake-up" byte or break condition that the receiver can use to synchronize. If it's a clock stability issue, I'd ensure the UART clock source is stable before enabling the transmitter, or add a preamble pattern that the receiver can use to re-synchronize its sampling point.

**Possible follow-ups:** How would you distinguish between a clock accuracy problem and a wake-up timing problem in this scenario? What role does the idle-line state play in UART communication, and how would you verify it's correct?

---

## Q3: How would you approach calculating the maximum bus capacitance for an I2C bus operating at 400 kHz with multiple devices, and what happens if you exceed that limit?

**Answer:** The I2C specification defines maximum bus capacitance limits for each mode: 400 pF for standard-mode (100 kHz) and fast-mode (400 kHz). This capacitance includes the trace capacitance, the pin capacitance of every device on the bus, and any connector or cable capacitance. The limit exists because the pull-up resistors and the bus capacitance form an RC time constant that determines how fast the bus lines can rise from low to high — I2C uses open-drain drivers, so the rise time is passive and depends entirely on this RC network.

To calculate the total capacitance, I'd sum the input capacitance of each device (from datasheets, typically 5–10 pF per pin), add the trace capacitance (roughly 1–2 pF per centimeter on a standard PCB, depending on stack-up and trace width), and include any connector or cable capacitance. If I'm designing with margin, I'd want to stay well under the 400 pF limit — realistically targeting 200–300 pF — because the limit is a maximum, not a target.

If the capacitance exceeds the limit, several things happen. The rise time slows down, which can cause the bus to violate the rise-time specification for fast-mode (300 ns maximum). This can lead to setup time violations at the slave devices, causing intermittent communication errors that are often temperature-dependent and hard to reproduce. In severe cases, the slow rise time can prevent devices from ever seeing a valid logic high, causing the bus to lock up.

There are a few mitigation strategies. First, I can reduce the pull-up resistor value to decrease the RC time constant — but this increases current draw and can violate the output low-level voltage specification (VOL) if the resistor is too small. Second, I can split the bus into segments using a bus buffer or multiplexer, each with its own pull-ups. Third, I can reduce the bus speed to 100 kHz, which has a more relaxed rise-time requirement. Fourth, I can use a level shifter or bus extender that actively drives the high level rather than relying on passive pull-ups. In practice, I'd first try to reduce capacitance by minimizing trace length and choosing devices with lower pin capacitance, then adjust pull-up values within the specification, and only add buffering if necessary.

**Possible follow-ups:** How would you calculate the appropriate pull-up resistor value for a given bus capacitance and speed? What are the trade-offs between using a smaller pull-up resistor versus adding a bus buffer?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single CAN-FD bus for a medical device that carries both a safety-critical control message requiring delivery within 2 ms and high-volume telemetry from multiple sensors. The engineer argues that CAN-FD's higher data rate in the data phase eliminates any bandwidth concerns. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that CAN-FD does offer a significant data-rate advantage in the data phase, but I'd steer the discussion toward the distinction between bandwidth and determinism. The engineer is conflating throughput with latency guarantees. Even if the bus has plenty of aggregate bandwidth, the safety-critical message's delivery time depends on when it can win arbitration, which is affected by the number and priority of other messages on the bus.

I'd guide the team to work through a concrete worst-case analysis. First, we need to identify every message on the bus, its size, its period or trigger condition, and its priority. Then we calculate the worst-case queuing delay for the safety-critical message — the longest time it could wait for higher-priority messages to complete. This includes not just the arbitration phase but also the data phase duration of any higher-priority message that's already in progress. CAN-FD's faster data phase helps reduce the transmission time of each message, which does reduce the blocking time, but it doesn't eliminate the need for the analysis.

I'd also raise the question of error handling. CAN-FD has error frames and retransmission, which means a burst of errors on the bus can cause messages to be retransmitted, adding unpredictable delay. For a safety-critical message with a 2 ms deadline, we need to understand what happens if the bus enters a busy state due to errors. This might require designing the network with error-confinement strategies, such as limiting the number of retransmissions or using a separate, dedicated link for the most critical messages.

Finally, I'd ask the engineer to consider the telemetry side. Even if the telemetry can tolerate delay, if it's high-volume, it could saturate the bus during bursts, causing the safety-critical message to wait longer than the 2 ms budget. The solution might involve rate-limiting the telemetry, using a time-triggered scheduling scheme where the safety-critical message gets a guaranteed slot, or physically separating the traffic onto different buses. The key takeaway I'd want the team to leave with is that CAN-FD's higher data rate is a tool that can help meet timing requirements, but it doesn't replace the need for a rigorous worst-case timing analysis.

**Possible follow-ups:** How would you calculate the worst-case latency for the safety-critical message in this scenario? What role does the arbitration phase bit rate play versus the data phase bit rate in meeting the 2 ms deadline?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** My first priority would be to address the immediate situation: the compliance testing has found a real issue, and we need to understand its safety impact before anything else. I'd work with the engineer and the test team to characterize the failure precisely — what exactly is failing, under what conditions, and what is the potential patient or user harm? This feeds directly into the risk management process. Depending on the severity, we may need to halt testing, issue a stop-shipment if the device is already in the field, or determine that the issue is contained to a specific test scenario.

Once the immediate risk is assessed, I'd shift to root-cause analysis. I'd bring the engineer into the investigation not as a blame exercise but as a learning opportunity. We'd trace through the protocol implementation against the specification, identify where the misunderstanding occurred, and determine whether it was a misinterpretation of the spec, a coding error, or a gap in the design review process. I'd also check whether the test that caught the error was new or whether it existed in previous test phases — if it existed, we need to understand why it didn't catch the issue earlier.

From a process perspective, I'd look at what should have caught this earlier. Was there a peer review of the protocol implementation? Were there unit tests or integration tests that should have exercised this path? Was the protocol specification ambiguous, and if so, does it need clarification? The goal is to identify systemic improvements so the same class of error doesn't recur.

For the schedule impact, I'd work with the project manager to assess the options: can we fix the implementation and retest within the current timeline, or do we need to adjust the schedule? I'd also consider whether there are interim mitigations — for example, a workaround in the protocol usage that reduces the risk while the full fix is developed. Throughout this, I'd keep the junior engineer involved and supported, making it clear that the focus is on the process and the fix, not on assigning blame. A mistake discovered in testing is exactly what the testing process is designed to catch, and the value is in the learning and improvement, not in the delay.

**Possible follow-ups:** How would you balance the need for a thorough root-cause investigation with the pressure to get the device back into compliance testing quickly? What changes to the design review process would you propose to prevent similar issues in the future?