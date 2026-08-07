# protocols — Day 17

## Q1: How would you approach designing a USB 2.0 device that needs to support both isochronous transfers for real-time sensor streaming and bulk transfers for reliable data logging, without one starving the other?

**Answer:** The first step is to understand the bandwidth budget and the host controller's scheduling behavior. USB 2.0 allocates the bus in 1 ms frames (or 125 µs microframes for high-speed devices), and isochronous endpoints get guaranteed bandwidth during the frame, while bulk transfers only use whatever remains. So the key risk is that heavy isochronous traffic can starve bulk transfers, or conversely, that bulk traffic can delay isochronous service if the endpoint descriptors aren't configured properly.

I would start by calculating the worst-case bandwidth for both endpoints. For isochronous streaming, that means the packet size times the number of packets per frame, plus protocol overhead. For bulk, I'd look at the maximum sustained throughput needed for logging. The sum of both, plus overhead for control transfers, must stay comfortably below the 480 Mbps theoretical maximum — realistically, below about 80% of practical throughput, which is lower than the theoretical number due to protocol overhead and host scheduling inefficiencies.

On the firmware side, I'd use separate endpoint FIFOs sized appropriately for each transfer type, and I'd implement a scheduling policy in the device firmware that prioritizes isochronous packet preparation so the endpoint always has data ready when the host polls it. For bulk transfers, I'd use a double-buffering scheme so the application can keep filling one buffer while the other is being transmitted. If the host is particularly busy, the isochronous endpoint will still get its guaranteed slots, and bulk will just slow down — which is acceptable for logging but not for real-time data.

I'd also consider whether the isochronous stream can tolerate occasional dropped packets. If the application can accept a small, bounded loss rate, I can reduce the isochronous bandwidth reservation and leave more room for bulk. If it cannot tolerate any loss, I need to be more conservative in the bandwidth calculation and possibly reduce the streaming rate or packet size.

**Possible follow-ups:**
- How would you handle the case where the host controller doesn't provide the full isochronous bandwidth you reserved during enumeration?
- What happens to your isochronous stream if the host enters a suspend state — how would you design the resume behavior?

---

## Q2: You're debugging a system where an RS-485 network works reliably at 9600 baud but experiences intermittent corruption at 115200 baud. The cable run is approximately 150 meters with 12 nodes. How would you approach this?

**Answer:** This is a classic signal-integrity problem that manifests at higher bit rates. The first thing I'd check is whether the system was ever designed for 115200 baud over that cable length. At 9600 baud, the bit time is about 104 µs, which gives plenty of margin for reflections and slow edges. At 115200 baud, the bit time drops to about 8.7 µs, and now the cable's electrical length becomes significant relative to the bit time.

I'd start by examining the physical layer. For a 150-meter run, I'd verify that proper termination is in place — typically 120 Ω at both ends of the bus, matching the characteristic impedance of the cable. I'd also check for stub lengths at each node; at 115200 baud, stubs longer than about 0.3 meters can cause reflections that corrupt the signal. If nodes are connected with long pigtails, that's a likely culprit.

Next, I'd look at the transceiver's slew rate. Many RS-485 transceivers have a limited slew rate that's fine for low baud rates but produces non-ideal waveforms at higher speeds. I'd check whether the transceivers are rated for the higher data rate — some "low-power" or "slow-slew" transceivers are explicitly limited to lower speeds. If they're not rated for 115200, that's the answer.

I'd also check the fail-safe biasing. At higher baud rates, the line spends less time in each state, and if the bias resistors are too weak, noise can pull the line into the undefined region between logic levels. I'd verify the bias network provides adequate noise margin at the higher speed.

Finally, I'd use a scope to look at the actual waveforms at the farthest node — checking for ringing, overshoot, and whether the signal crosses the receiver's threshold cleanly. If the waveform shows reflections, I'd adjust termination or reduce stub lengths. If the edges are too slow, I'd consider a transceiver with faster slew rate or accept that the physical layer needs to be redesigned for the higher baud rate.

**Possible follow-ups:**
- How would you determine whether the issue is reflections versus inadequate drive strength?
- What would you change if the cable run were 500 meters instead of 150 meters?

---

## Q3: How would you approach implementing a deterministic scheduling scheme for a mixed-protocol medical device that uses I2C for sensor reads, SPI for high-speed data logging, and UART for a user interface, all on a single microcontroller running Zephyr RTOS?

**Answer:** The core challenge is ensuring that each protocol gets the service it needs without one starving the others, while also meeting any real-time deadlines. I'd start by characterizing the timing requirements for each interface: the I2C sensor reads might need to happen at a fixed rate (say every 10 ms), the SPI logging might have a minimum throughput requirement, and the UART interface might have latency constraints for user feedback.

In Zephyr, I'd structure this using threads with appropriate priorities and a combination of interrupt-driven and DMA-based transfers. The key is to avoid blocking operations in high-priority contexts. For example, I2C transactions should be asynchronous — the thread initiates the transfer and waits on a semaphore or uses a callback, rather than busy-waiting. This allows the scheduler to run other threads while the I2C controller is clocking out data.

For the scheduling scheme itself, I'd consider a few approaches. One is a fixed-priority preemptive scheme where the most time-critical traffic (likely the I2C sensor reads) runs at the highest priority, with the SPI logging at medium priority, and UART at the lowest. The risk here is that if the I2C traffic is frequent and long, it could starve the SPI logging. So I'd need to verify worst-case blocking times.

Another approach is a time-triggered or time-sliced scheme, where each protocol gets a dedicated time slot in a repeating cycle. This provides deterministic behavior but can waste bandwidth if a protocol doesn't need its full slot. A hybrid approach often works best: use a time-triggered schedule for the periodic sensor reads and logging, and handle UART asynchronously with interrupts since it's event-driven.

I'd also consider using DMA where available — for SPI logging, DMA can move data without CPU intervention, freeing the core for other tasks. For UART, DMA or interrupt-driven reception with a ring buffer avoids dropped characters. The key is to measure actual timing — I'd instrument the system with timestamped trace events to verify that worst-case latencies meet requirements, and adjust priorities or buffer sizes if they don't.

**Possible follow-ups:**
- How would you handle the case where an I2C sensor occasionally clock-stretches for longer than expected, delaying other traffic?
- What tools or methods would you use to verify that your scheduling meets all timing requirements?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single I2C bus at 400 kHz to connect five sensors, a real-time clock, and an EEPROM, all on a 30-centimeter PCB with long traces. The engineer argues that the bus capacitance is within the 400 pF limit. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that the engineer has done the right first step — checking the bus capacitance against the I2C specification limit. But I'd guide the team to look beyond just the raw capacitance number, because there are several other factors that determine whether this design will be reliable in practice.

First, I'd ask about the actual capacitance budget. Seven devices on a 30 cm PCB with long traces — I'd want to see the calculation broken down: trace capacitance per centimeter, input capacitance per device, and any connector or protection components. If they're near the 400 pF limit, that's already a concern because the limit assumes ideal conditions. I'd also ask about the pull-up resistor values — at 400 kHz, the rise time requirement is 300 ns maximum, and the pull-up resistors must be small enough to charge the bus capacitance within that window. If the capacitance is near the limit, the pull-ups might need to be quite small, which increases current draw — a concern for a battery-powered device.

Second, I'd raise the issue of noise margin and signal integrity. With long traces on a 30 cm PCB, there's potential for crosstalk between the I2C lines and other signals, especially if the traces run parallel for significant distances. At 400 kHz, the edges are fast enough that reflections and ringing can occur, particularly if the traces aren't properly impedance-controlled or if there are discontinuities at vias or connectors.

Third, I'd ask about fault tolerance. With seven devices on one bus, a single device holding SDA or SCL low — due to a firmware bug or hardware failure — takes down the entire bus. I'd ask what happens if one sensor fails: does the whole system stop? Is there a way to isolate a faulty device? This is especially important in a medical device where reliability is critical.

Finally, I'd ask whether the engineer has considered the alternative of splitting the bus — perhaps using two I2C buses with fewer devices each, or using a multiplexer like a TCA9548A to isolate segments. This adds complexity but improves reliability and simplifies debugging. I'd frame the discussion as: the capacitance check is necessary but not sufficient — we need to look at the whole picture of signal integrity, fault tolerance, and testability before committing to this architecture.

**Possible follow-ups:**
- How would you decide between one bus with a multiplexer versus two separate I2C peripherals?
- What specific measurements would you want to see from a prototype before approving the design?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to address the immediate situation: the compliance test failure needs to be understood and fixed. I'd start by convening a focused root-cause analysis with the engineer and the relevant team members — not to assign blame, but to understand exactly what went wrong. I'd want to know: was the protocol implemented incorrectly from the start, or did it work in initial testing and fail only under specific compliance test conditions? The answer changes the response.

Once the technical issue is understood, I'd work with the team to develop a fix and a verification plan. The fix needs to be validated not just against the specific test that failed, but against the full protocol specification and all related requirements — a quick patch that fixes the immediate failure but introduces a different compliance issue would be worse. I'd also want to understand the scope: does this error affect other parts of the system, or is it isolated to this one protocol implementation?

After the immediate crisis is handled, I'd shift to the process question: how did this get through design review, code review, and earlier testing without being caught? I'd lead a blameless post-mortem to identify gaps in the process. Was the protocol specification ambiguous? Were the test cases inadequate? Was there pressure to skip certain verification steps? The goal is to strengthen the process so this doesn't recur.

For the junior engineer specifically, I'd approach this as a coaching opportunity. I'd have a private conversation to understand their perspective — did they misunderstand the spec, did they not have the right tools, did they feel they couldn't ask for help? I'd provide constructive feedback focused on the technical gap and the process, not on them as a person. I'd also make sure they're involved in the fix and the post-mortem, so they learn from the experience rather than feeling isolated by it.

Finally, I'd communicate transparently with stakeholders about the delay — the schedule impact is real, and the team needs to work together to mitigate it. The key is to balance accountability with support: the engineer needs to understand the seriousness of the error, but also needs to feel supported in fixing it and growing from the experience.

**Possible follow-ups:**
- How would you handle the situation if the junior engineer becomes defensive or tries to shift blame?
- What specific changes to the development process would you propose to prevent similar issues in the future?