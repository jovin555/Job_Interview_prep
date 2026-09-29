# protocols — Day 70

## Q1: How would you approach designing a multi-drop sensor network where one node needs deterministic, low-latency response for closed-loop control while another node generates bursty high-volume telemetry, and both must share the same physical medium?

**Answer:** The first step is to recognize that "same physical medium" doesn't have to mean "same logical priority class." I'd start by quantifying the two traffic profiles: what is the worst-case latency the control loop can tolerate, what is the jitter budget, and what is the peak burst size and acceptable latency for the telemetry. If the control loop needs sub-millisecond deterministic response, a shared contention-based medium is usually the wrong answer regardless of raw bandwidth, because bandwidth doesn't buy determinism.

From there I'd evaluate three architectural options. First, a single bus with strict priority arbitration — CAN-FD is attractive here because its arbitration is non-destructive and priority-based, so a high-priority control frame wins arbitration deterministically, and the telemetry can be fragmented into lower-priority frames that yield. The trade-off is that CAN-FD's data-phase bit rate and bus length are coupled, and a large telemetry burst can still add queuing delay if it's already mid-transmission when the control frame arrives. Second, a time-triggered schedule — a TDMA-style slot map where the control node gets a guaranteed slot every cycle and telemetry fills the remaining slots. This gives the tightest determinism but requires tight clock synchronization and is less flexible to bursts. Third, physically separate the media — a dedicated point-to-point or small dedicated bus for the control loop, and a separate bus for telemetry. This is often the most robust and simplest to certify, at the cost of extra connectors, cabling, and controller peripherals.

My default recommendation for a medical device would lean toward separation if the control loop is safety-related, because it makes the determinism argument trivial to defend in a risk analysis and removes a whole class of interference failure modes. If separation isn't feasible, I'd go with a priority-based bus plus a bounded worst-case analysis: compute the maximum frame transmission time of the largest telemetry frame, add the arbitration and inter-frame gaps, and verify that the control frame's worst-case queuing delay still fits the budget. I'd also add application-level sequence numbers and freshness timestamps so a stale control command can be rejected rather than acted on.

**Possible follow-ups:**
- How would you verify the worst-case latency claim empirically rather than just analytically?
- If the telemetry source can burst arbitrarily, how would you bound its impact without starving it entirely?

## Q2: You're debugging a CAN-FD network where a node intermittently enters error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter (TEC) exceeded 127, so the controller is still on the bus but can no longer send active error flags — it can only send passive ones. The fact that it recovers on its own tells me the counter is decrementing successfully on subsequent good transmissions, so this is likely a marginal physical-layer or timing issue rather than a hard fault. I'd treat it as a signal-integrity and timing investigation first, protocol second.

Concretely, I'd capture the bus with a CAN analyzer that timestamps error frames and records the error type (bit error, stuff error, CRC error, form error, ACK error). The error type is the biggest clue. Bit errors and stuff errors point to physical-layer problems — reflections from incorrect termination, stub length, or a node whose transceiver is marginal. CRC errors on received frames point to noise or a bit-rate mismatch in the data phase. ACK errors point to a node that isn't acknowledging, which could be a node that's gone bus-off or a wiring break. Form errors often point to a node transmitting with the wrong bit timing.

I'd then correlate the error events with operating conditions: temperature, supply voltage, whether a particular motor or relay is switching, and whether the errors cluster around specific message IDs. A common root cause in CAN-FD specifically is that the data-phase bit rate is set aggressively relative to the actual bus length and transceiver loop delay — the arbitration phase works fine but the data phase has insufficient margin, so errors appear only on longer frames or at temperature extremes. I'd check the sample-point settings and the transceiver's loop delay against the calculated propagation delay for the bus length.

If the physical layer checks out, I'd look at the node's firmware: is it transmitting faster than the bus can drain, causing it to lose arbitration repeatedly and increment TEC? Is there a node that occasionally transmits with a corrupted identifier due to a buffer overrun? I'd also verify that all nodes agree on the bit timing registers — a single node with a slightly different oscillator can cause intermittent errors that only show up when it wins arbitration.

**Possible follow-ups:**
- What's the difference between error-passive and bus-off, and how does recovery differ?
- How would you decide whether to reduce the data-phase bit rate versus shorten the bus?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** The cleanest answer is to add backpressure at a layer where you control both ends, but if the protocol is fixed and can't be changed, you have to work within its constraints. I'd first characterize the problem: is the receiver occasionally slow because of a blocking operation (flash write, radio transmit, ADC conversion), or is it consistently slower than the line rate? Those lead to different fixes.

If the receiver is occasionally blocked, the first line of defense is buffering. A ring buffer sized to absorb the worst-case blocking duration at the line rate gives you headroom without changing the protocol. I'd size it by measuring the longest blocking interval and multiplying by the byte rate, then adding margin. If the buffer would be impractically large, the next option is to use the hardware flow control lines if they're physically wired — RTS/CTS is exactly the mechanism for this, and it's worth checking whether the board actually routes them even if the protocol doesn't use them. If they're not wired, a software flow control scheme using XON/XOFF is possible but risky in a binary protocol because the control characters can appear in payload data; it only works if the payload is constrained or escaped.

If neither buffering nor flow control is viable, the remaining option is to slow the transmitter. That means either reducing the baud rate to something the receiver can always keep up with, or having the transmitter insert idle gaps between frames. Idle gaps are a form of implicit flow control — the receiver gets a known recovery window. The trade-off is reduced effective throughput, but for a medical device that's usually acceptable if the alternative is dropped data.

The most robust long-term answer is to add an application-level acknowledgment and retransmission scheme on top of the UART, so that even if bytes are lost, the protocol recovers. That's more work but it's the only approach that's resilient to a receiver that occasionally misses data entirely rather than just being slow.

**Possible follow-ups:**
- How would you size the ring buffer if the blocking interval is variable and unbounded?
- What are the failure modes of XON/XOFF in a binary protocol, and how would you mitigate them?

## Q4: How would you approach debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB?

**Answer:** The fact that it works at 100 kHz but not 400 kHz with identical hardware strongly points to a timing or signal-integrity margin issue rather than a logic bug. At 400 kHz the bus has roughly one-quarter the timing margin, so anything marginal at 100 kHz becomes visible.

I'd start with the physical layer. The first suspect is bus capacitance and pull-up strength. At 400 kHz, the rise time budget is much tighter, and if the pull-ups are sized for 100 kHz (typically higher values to save power), the rise time may exceed the fast-mode specification. I'd measure the actual rise time on SDA and SCL with a scope at the worst-case point on the bus — usually the far end from the master — and compare it against the I2C spec limit. If it's too slow, the fix is lower pull-up values, but that increases power and the low-level sink current, so I'd check that all devices can sink the resulting current.

The second suspect is the effective bus capacitance itself. Long traces, connectors, and the input capacitance of each device add up. If the total exceeds the 400 pF fast-mode limit, the rise time will be too slow regardless of pull-up value. I'd estimate the capacitance from the trace geometry and device datasheets, and if it's close to the limit, consider a bus buffer or a lower-capacitance layout.

The third suspect is clock stretching. If any slave stretches the clock, the master must honor it. At 400 kHz, a slave that stretches for a fixed time may cause the master to time out or mis-sample. I'd check whether the NACKs correlate with a specific slave and whether that slave's datasheet specifies a minimum stretch time.

Finally, I'd look at the master's timing configuration — the setup and hold times, the spike filter, and whether the master is actually running at 400 kHz or something slightly off. A master with a poorly calibrated clock can produce a bus that's technically within spec but has no margin. I'd also check for ground bounce or noise coupling from nearby switching circuitry, since higher bus speed means the edges are faster and more susceptible to crosstalk.

**Possible follow-ups:**
- How would you calculate the maximum allowable pull-up resistance for a given rise time target?
- What's the difference between a NACK caused by a missing device and one caused by a timing violation, and how would you tell them apart on a scope?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to separate the technical problem from the people problem, and to do it in that order. The immediate need is to understand exactly what's wrong, how far the impact reaches, and what the fastest safe path to a fix is. I'd pull together the engineer, the test lead, and whoever owns the compliance submission, and walk through the failure together — not to assign blame, but to get a shared, precise picture of the defect. Compliance failures are often reported as a symptom rather than a root cause, so the first job is to reproduce it in a controlled environment and confirm the actual mechanism.

Once the defect is understood, I'd assess the blast radius. Does the fix require a firmware change only, or does it touch the protocol definition, the interface control document, or the risk analysis? In a regulated environment, a protocol change can ripple into the DHF, the software requirements, and potentially the test plan itself. I'd want the regulatory lead in the room early so we don't fix the code and then discover the documentation is now inconsistent.

On the people side, I'd be deliberate about how the conversation goes. A junior engineer who made a mistake that surfaced late is likely already feeling the weight of it, and the worst outcome is that they shut down or start hiding problems. I'd frame it as a process gap as much as an individual one — if a protocol error could survive code review, unit testing, and integration testing only to appear at compliance, then the review and test process has a hole in it, and that's a team problem to fix. I'd ask what would have caught it earlier and add that check to the process.

For the schedule, I'd be transparent with stakeholders about the delay and the recovery plan rather than trying to absorb it silently. I'd also look for whether the fix can be validated incrementally — a targeted re-test of the affected compliance clause rather than a full re-run — to recover some time. And I'd make sure the engineer is part of the fix, not sidelined from it, because that's how the lesson actually sticks.

**Possible follow-ups:**
- How would you decide whether to fix the protocol or add a workaround at a higher layer?
- What process change would you propose to catch protocol errors before compliance testing?