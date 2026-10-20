# protocols — Day 91

## Q1: How would you approach debugging a CAN-FD network where a node occasionally goes bus-off and stays off until the controller is reset, even though the bus itself appears healthy afterward?

**Answer:** Bus-off is the CAN controller's terminal error state — the transmit error counter (TEC) has exceeded 255, so the controller has removed itself from the bus. The fact that it stays off until reset tells me the firmware isn't implementing automatic bus-off recovery, which is the first thing to check: many controllers can be configured to recover automatically after 128 occurrences of 11 recessive bits, but if that's disabled (or the application never re-initializes the controller), the node is dead until power-cycled. So I'd separate two problems: why did it reach bus-off, and why didn't it recover.

For the "why bus-off" side, I'd look at what drives TEC up: transmit errors, which usually mean the node isn't seeing acknowledgements or is losing arbitration repeatedly in a way that suggests a physical-layer problem, or it's transmitting into a bus where no other node is listening. I'd check for a marginal transceiver, a missing or wrong termination, a stub that's too long for the data-phase bit rate, or a common-mode offset that only appears under certain load conditions. I'd also check whether the node's bit timing is correct for the configured data-phase rate — a sample-point mismatch that's marginal at one temperature or supply voltage can produce intermittent errors that only occasionally accumulate to bus-off. A CAN analyzer that logs error frames and the error counters over time is essential here; watching TEC/REC trend before the event usually tells you whether it's a persistent physical issue or a burst.

For the "why no recovery" side, I'd confirm the recovery policy is intentional and documented. In a medical device, silently auto-recovering from bus-off can be the wrong behavior if the node is a safety-critical sensor — you may want the node to recover but flag the event, increment a diagnostic counter, and possibly degrade gracefully rather than pretend nothing happened. So the fix isn't just "enable auto-recovery"; it's deciding what the system should do when a node has been off the bus, and making that decision explicit in the requirements and the risk analysis.

**Possible follow-ups:**
- How would you distinguish a physical-layer cause of bus-off from a firmware/bit-timing cause using only bus analyzer traces?
- If the node is safety-critical, what would "graceful degradation" look like after a bus-off event, and how would you verify it?

## Q2: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** The core risk in half-duplex RS-485 is bus contention: if two drivers are enabled at once, you get a short but potentially damaging current path and corrupted data; if the driver is disabled too early, the last bits get truncated; if the receiver is enabled too late, you miss the start of the response. So the design has to treat the DE/RE timing as a first-class timing budget, not an afterthought.

On the hardware side, I'd pick a transceiver with well-characterized enable/disable times and, ideally, a receiver that fails safe (outputs a defined logic level) when the bus is undriven. I'd also make sure the DE and RE pins are driven by a GPIO with known, low-latency behavior — not something routed through an I/O expander over I2C, which would add unpredictable latency. If the MCU has a hardware DE control (some UART peripherals can assert DE automatically on transmit), that's usually more reliable than firmware toggling a GPIO in an interrupt, because it removes software jitter from the critical path.

On the firmware side, I'd structure the driver so that "transmit complete" is detected from the UART's transmit-complete flag (not the transmit-empty flag — empty means the shift register is still draining), and only then disable the driver. For the receive side, I'd enable the receiver before the expected response window and leave it enabled through the turnaround, then disable it if the protocol calls for it. I'd measure the actual turnaround with a scope: DE high to first bit, last bit to DE low, and the gap before the responder starts driving. If the budget is tight, I'd consider raising the baud rate only if the cable and termination support it, or shortening the protocol's inter-frame gap rather than shaving the electrical margins.

The thing I'd emphasize in a design review is that the turnaround budget has to include worst-case transceiver propagation delay, cable propagation delay (roughly 5 ns/m, so a 200 m run is about 1 µs each way), and firmware interrupt latency — and that the budget should be verified on the bench with a scope, not assumed from datasheet typicals.

**Possible follow-ups:**
- How would you verify the DE/RE timing margin across temperature and supply variation, not just at room temperature?
- What failure mode would you expect if the receiver is left enabled while the local node is transmitting, and how would you detect it?

## Q3: How would you approach selecting between USB 2.0 interrupt transfers and isochronous transfers for a medical device that streams real-time sensor data to a host computer, with a requirement that no data be lost?

**Answer:** The requirement "no data lost" is the deciding factor, and it points away from isochronous. Isochronous transfers reserve bandwidth and guarantee timing, but they have no retry mechanism — if a packet is corrupted or the host misses its service interval, the data is simply gone. That's fine for audio or video where a dropped frame is imperceptible, but for a medical sensor stream it's usually unacceptable unless the application can tolerate gaps and the risk analysis says so.

Interrupt transfers, by contrast, are retried by the host controller on error and are scheduled with a bounded latency (the endpoint's polling interval), so they give you reliability plus a predictable worst-case latency, at the cost of lower guaranteed bandwidth than isochronous. For most medical sensor streams — even fairly high-rate ones — interrupt transfers at a suitable interval are the right default, and you size the endpoint's max packet size and interval so the required throughput fits with margin.

The trade-off to walk through explicitly: isochronous gives you a hard timing guarantee but no delivery guarantee; interrupt gives you delivery guarantee and bounded latency but the bandwidth is shared and the host may not always service you at the exact interval under load. If the application genuinely needs both — a hard real-time stream and no loss — the usual answer is to use interrupt transfers and design the host-side buffering and the device-side FIFO so that transient host scheduling jitter doesn't cause overflow, and to make the endpoint interval and packet size part of the timing budget. I'd also flag that "no data lost" should be defined precisely: lost at the USB layer, or lost end-to-end? If end-to-end, you need sequence numbers and application-level acknowledgement regardless of which transfer type you pick.

**Possible follow-ups:**
- How would you size the device-side FIFO and the host polling interval so that host scheduling jitter doesn't cause data loss?
- If the host OS's USB stack adds unpredictable latency, how would you characterize that and feed it back into the design?

## Q4: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** I'd start from the electrical and protocol constraints rather than from a preference, because the "right" topology usually falls out of the cable length, the number of nodes, the data rate, and the failure-tolerance requirements.

A star topology — each sensor on its own cable back to a central hub — gives you the cleanest signal integrity per link, isolates a single cable fault to one sensor, and makes termination and stub-length management trivial because each link is point-to-point. The cost is cable bulk, connector count, and hub complexity, which matters in a medical device where the cable harness has to be routed around a patient and pass bend/flex and cleaning requirements. A daisy-chain (or bus) topology uses far less cable and fewer connectors, but every node sits on a shared medium, so you inherit all the classic multi-drop problems: termination at both ends, stub length limits, common-mode voltage differences between nodes, and the fact that one bad connector or a node that holds the bus dominant can take down the whole segment.

For a medical device I'd weigh: how many sensors, how far apart, what data rate, and what happens if one link fails. If the sensors are few and the reliability requirement is high, star is often worth the cable. If there are many sensors distributed along a patient support structure and the data rate is modest, a properly terminated daisy-chain with short stubs and fail-safe biasing is usually the pragmatic choice — but I'd insist on per-node isolation (series resistors or a protected transceiver) so a single fault doesn't corrupt the bus, and I'd define the behavior when a node stops responding.

I'd also bring the mechanical and clinical constraints into the decision early, because the topology that's electrically cleanest may be the one that's hardest to route, clean, and service — and in a medical device those are requirements too, not afterthoughts.

**Possible follow-ups:**
- How would you protect a daisy-chained bus so that a single node holding the bus dominant doesn't take down the whole segment?
- What would change in your analysis if the sensors were on a disposable patient-contact cable versus a reusable equipment harness?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to stabilize the situation and protect the patient-facing and regulatory commitments, then do the root-cause and process work — in that order, because a compliance failure has a schedule and possibly a submission impact that can't wait for a full post-mortem.

Concretely, I'd convene the relevant people quickly — the junior engineer, the test lead, the regulatory lead, and whoever owns the affected subsystem — to establish exactly what failed, what the standard or test requires, and what the minimum correct fix is. I'd want the failure characterized precisely before anyone starts changing code, because "the protocol is wrong" is usually several distinct defects and the fix has to address the actual nonconformance, not a guess. Then I'd scope the fix, the re-test, and the documentation impact (test reports, traceability, any risk-file updates) and communicate a revised plan to the stakeholders rather than letting the delay surface as a surprise.

On the people side, I'd be deliberate about how I handle the junior engineer. The instinct to assign blame is understandable but counterproductive: the more useful question is why the defect wasn't caught earlier — was there no protocol conformance test, no code review of the protocol layer, no integration test against a reference implementation? If the process had a gap, that's a team and leadership issue, not solely the engineer's. I'd have a private conversation focused on understanding what happened and what support they need, and I'd make clear that the goal is a fix and a stronger process, not a punishment. Publicly, I'd frame it as a process gap the team is closing.

Finally, I'd close the loop: add the missing test or review step that would have caught it, and verify the fix against the actual compliance test rather than a bench approximation. The lesson I'd want the team to take away is that protocol correctness has to be verified against the standard, not just against "it works on the bench."

**Possible follow-ups:**
- How would you decide whether to fix forward in the current build or revert to a known-good protocol implementation, given the schedule pressure?
- What process change would you put in place so protocol conformance is checked before formal compliance testing, without adding so much process that it slows the team down?