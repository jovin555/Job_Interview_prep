# high-speed-digital-fpga — Day 16

## Q1: How would you approach designing a write-leveling calibration routine for a DDR3 memory interface in an FPGA, and what are the key challenges you would need to address?

**Answer:** Write leveling compensates for the skew between the clock (CK) and the data strobe (DQS) signals that arises from the fly-by topology used in DDR3 routing. In a fly-by topology, the clock and address/command signals daisy-chain from one memory device to the next, while the data signals route point-to-point, creating a timing offset that increases with each device on the chain.

My approach would start by understanding the JEDEC-specified write-leveling procedure: the controller drives DQS low and then issues a continuous stream of rising clock edges while the memory device samples DQS on each clock edge. The memory returns the sampled value on the DQ bus, allowing the controller to determine whether DQS is arriving before or after the clock edge at that particular device.

The key challenge is implementing the feedback loop correctly. The controller must adjust the DQS delay in small, controlled increments—typically 1/8 or 1/16 of a clock period per step—and monitor the DQ feedback to find the transition point where the sampled value flips. This requires a state machine that can:
- Drive DQS to a known state
- Issue the leveling command sequence
- Read back the DQ response
- Adjust the per-byte-lane delay element
- Repeat until the optimal delay is found

A critical subtlety is that write leveling must be performed per byte lane, not per device, because each byte lane has its own DQS and DQ signals. The delays will differ between byte lanes even on the same device due to routing differences.

Another challenge is handling the case where the initial DQS delay is so far off that the transition point is ambiguous—for example, if DQS is delayed by nearly a full clock period, the feedback might appear stable when it shouldn't be. I would implement a search algorithm that sweeps the full delay range and identifies the correct transition, rather than stopping at the first edge found.

Finally, I would verify the results by running a known data pattern through the interface after leveling is complete, and I would build in margin analysis—checking that the chosen delay point sits in the middle of the valid window, not near the edges.

**Possible follow-ups:** How would you handle write leveling when the memory controller IP you're using doesn't expose the per-byte-lane delay controls? What happens if the leveling routine completes but the interface still has marginal timing—how would you diagnose whether the issue is in the leveling or elsewhere in the write path?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design functions correctly at room temperature and fails only when the board is heated to its maximum specified operating temperature?

**Answer:** This is a classic temperature-dependent failure that typically points to timing margin degradation rather than a functional logic error. As temperature rises, transistor switching speeds slow down, which increases propagation delays and reduces setup/hold margins. The fact that the design works at room temperature but fails when hot suggests the design is operating close to its timing limits even under nominal conditions.

My debugging approach would be systematic:

First, I would try to characterize the failure precisely. What exactly fails—does the design stop producing correct outputs, does it produce intermittent errors, or does it lock up entirely? The failure signature often points to the root cause. For example, intermittent data corruption suggests a setup/hold violation on a data path, while a complete lockup might indicate a clocking issue or a state machine entering an illegal state.

Next, I would examine the timing reports from the place-and-route tools, specifically looking at the worst negative slack (WNS) and total negative slack (TNS) across all timing corners. If the design closes timing with very little margin (say, less than 100-200 ps), that's a strong indicator that temperature-induced delay variation could push paths over the edge. I would also check whether the design was constrained correctly—missing or incorrect constraints can cause the tools to optimize paths that don't actually matter while leaving critical paths unoptimized.

I would then look at the clock distribution. Temperature changes affect PLL/DLL behavior, and a marginal clock tree can cause failures that look like logic errors. I would verify that the clock is clean at temperature using an oscilloscope or by reading the PLL lock status and any jitter monitoring features the FPGA provides.

If the timing reports show marginal slack, I would consider several mitigations:
- Re-running place-and-route with more aggressive optimization settings or different seeds
- Adding pipeline stages to break up long combinational paths
- Adjusting I/O timing constraints if the failure is at the pins
- Using the FPGA's built-in delay elements or I/O serializer/deserializer features to add margin

I would also check the power supply. At elevated temperature, supply voltages can droop, especially if the regulator has thermal derating. A marginal power supply can cause timing failures that look like temperature-induced logic errors. I would verify all supply rails at temperature, both at the regulator output and at the FPGA power pins, looking for excessive ripple or droop.

Finally, I would consider whether the failure is related to configuration memory. Some FPGAs have configuration cells that are more sensitive to temperature, particularly at higher voltages. If the design uses partial reconfiguration or if the bitstream was generated with marginal configuration settings, this could manifest as a temperature-dependent failure.

**Possible follow-ups:** How would you distinguish between a setup-time failure and a hold-time failure in this scenario? What role would you expect the process corner (slow-slow vs. fast-fast) to play in a temperature-dependent failure?

---

## Q3: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous and have no known frequency relationship, and the data must be transferred without corruption?

**Answer:** This is the most challenging CDC scenario because with no known frequency relationship, you cannot rely on any deterministic timing between the domains. The fundamental options are handshaking, asynchronous FIFO, or a combination approach, and the choice depends on the data rate and latency requirements.

For a multi-bit bus with no frequency relationship, an asynchronous FIFO is the standard solution when data flows continuously or in bursts. The FIFO uses Gray-coded pointers to safely transfer the read and write pointers between clock domains, ensuring that only one bit changes at a time during pointer updates. The data itself is written into dual-port RAM, so the multi-bit data path doesn't cross clock domains directly—only the pointers do.

The key design considerations for the FIFO are:
- **Depth calculation:** The FIFO must be deep enough to absorb the maximum burst size plus the pointer synchronization latency (typically 2-3 cycles per domain). If the write side can produce data faster than the read side consumes it, even temporarily, the FIFO must accommodate the difference.
- **Gray-code pointer synchronization:** The write pointer is synchronized into the read domain using a two-flop synchronizer, and vice versa. The Gray coding ensures that even if the synchronized pointer is sampled during a transition, the value is off by at most one, which is safe for full/empty detection.
- **Full/empty generation:** The full flag is generated in the write domain by comparing the synchronized read pointer with the write pointer; the empty flag is generated in the read domain similarly. This means the flags are conservative—full might be asserted slightly early, and empty might be asserted slightly late—which is safe but can reduce throughput.

If the data rate is low and latency is not critical, a four-phase handshake (request/acknowledge) is simpler and more robust. The source asserts a request, the destination captures the data and asserts acknowledge, the source deasserts request, the destination deasserts acknowledge, and the cycle repeats. Each phase requires synchronization, so the throughput is limited to roughly one transfer every 4-6 destination clock cycles.

For higher throughput with a handshake, I would use a two-phase (edge-based) handshake, which halves the number of synchronization delays but is more complex to implement correctly.

A critical consideration is whether the data bus itself needs protection. If the source holds the data stable until the destination acknowledges, a simple handshake suffices. But if the data changes asynchronously relative to the destination clock, you need to ensure the destination doesn't sample the data while it's transitioning. The handshake protocol inherently provides this protection because the source only changes data after receiving an acknowledge.

I would also consider using a MUX-based synchronizer for narrow buses (2-4 bits) where the data changes infrequently. The source encodes the data into a one-hot or Gray-coded format, and the destination synchronizes each bit with a two-flop synchronizer. This works only if the data is guaranteed stable for multiple destination clock cycles.

Finally, I would verify the CDC design using formal verification tools that check for CDC violations, and I would run simulation with randomized clock phase relationships to stress-test the design. I would also add assertions in simulation to detect any data corruption or lost transfers.

**Possible follow-ups:** How would you choose between an asynchronous FIFO and a handshake for a specific application? What happens if the FIFO overflows or underflows—how would you design the error handling?

---

## Q4: How would you approach implementing a finite state machine (FSM) in an FPGA that must control a multi-step calibration sequence for an analog front-end, where each step requires waiting for an external ADC conversion to complete, and the timing of each conversion is variable (1 µs to 100 µs)?

**Answer:** This is a classic FSM design problem where the challenge is handling variable-duration waits without wasting FPGA resources or introducing timing issues. The key design decision is how to structure the wait states and how to detect completion of each ADC conversion.

My approach would use a hierarchical FSM structure. The top-level FSM manages the overall calibration sequence—each state represents a calibration step (e.g., offset calibration, gain calibration, temperature compensation). Within each state, the FSM initiates the ADC conversion and then waits for the completion signal. The completion signal would be an interrupt or a status bit from the ADC interface logic.

The critical design consideration is how to handle the variable wait time. I would not use a fixed counter because the conversion time varies from 1 µs to 100 µs—a counter sized for the worst case would waste time in the typical case, and a counter sized for the typical case would miss the completion signal in the worst case. Instead, I would use the ADC's completion signal directly as the FSM's next-state condition.

The FSM structure would look like:

```
IDLE → START_CONVERSION → WAIT_FOR_COMPLETE → CHECK_RESULT → NEXT_STEP or ERROR
```

In the `WAIT_FOR_COMPLETE` state, the FSM simply waits for the `conversion_done` signal to assert. This signal comes from the ADC interface logic, which handles the actual timing of the conversion. The FSM doesn't need to know how long the conversion takes—it just waits for the completion event.

A key consideration is metastability. If the `conversion_done` signal comes from a different clock domain (e.g., the ADC has its own clock), I would synchronize it with a two-flop synchronizer before feeding it to the FSM. This adds 2-3 clock cycles of latency, which is negligible compared to the 1-100 µs conversion time.

I would also add a timeout mechanism. If the ADC fails to complete a conversion within a maximum expected time (say, 200 µs), the FSM should transition to an error state rather than waiting indefinitely. This requires a counter that runs while in the `WAIT_FOR_COMPLETE` state and triggers a timeout if the completion signal doesn't arrive in time.

For the calibration sequence itself, I would consider whether the steps are strictly sequential or whether some steps can be pipelined. For example, if the calibration requires multiple ADC readings at different settings, I could start the next conversion while processing the previous result. This would require a more complex FSM with separate "start" and "process" states, but it could significantly reduce the total calibration time.

Another consideration is whether the FSM should be implemented as a single block or split into multiple interacting FSMs. For a complex calibration sequence with many steps, I would consider a hierarchical approach where a top-level FSM sequences through the major phases, and a lower-level FSM handles the details of each phase. This makes the design easier to understand, verify, and modify.

Finally, I would add debug visibility. I would expose the current FSM state on debug pins or in a status register so that during bring-up, I can observe the calibration sequence and verify that each step completes correctly. I would also add assertion-based verification in simulation to check that the FSM never enters an illegal state and that it always transitions correctly between states.

**Possible follow-ups:** How would you handle the case where the ADC conversion time varies based on the input signal level or the calibration setting? How would you verify that the calibration sequence produces correct results across the full operating range?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the clock distribution for the ADC interface and is presenting the design for review. During the presentation, you notice that the engineer has placed a series resistor in the clock path to "reduce ringing," but the resistor value is significantly higher than the characteristic impedance of the trace, creating a reflection that could cause jitter at the ADC clock input. When you raise this concern, the engineer responds that the resistor "fixed the ringing in simulation" and that the ADC "has a wide jitter tolerance anyway." How do you handle this situation?

**Answer:** This situation requires balancing technical correctness with mentorship and team dynamics. The engineer has made a design choice that addresses a real concern (ringing) but with a solution that introduces a different problem (reflections causing jitter). The engineer's defensive response suggests they may feel their work is being criticized rather than the design being reviewed.

My approach would be to first acknowledge what the engineer got right. They identified a real signal integrity concern—ringing on the clock line—and they took action to address it. That's good engineering instinct. The issue is not the goal but the implementation.

I would then reframe the discussion around the design objective rather than the specific solution. The goal is a clean clock signal at the ADC input with minimal jitter. Ringing is one source of jitter, but reflections from impedance mismatch are another. The series resistor approach can work, but only if the resistor value is chosen correctly relative to the trace impedance and the driver's output impedance.

I would walk through the math together: if the trace impedance is 50 ohms and the driver's output impedance is, say, 10 ohms, then a series resistor of 40 ohms would match the line. But if the resistor is 100 ohms, the reflection coefficient at the resistor-trace junction creates a reflected wave that can cause the clock edge to arrive at the ADC with multiple transitions—which is exactly the kind of jitter that can cause timing violations in the ADC's sampling.

I would also question the simulation results. If the simulation shows the ringing is "fixed," I would ask what the simulation setup was—did it include the ADC's input capacitance? Did it model the driver's output impedance correctly? Did it include the return path? A simulation that doesn't model the full signal path can give misleading results.

Rather than simply overriding the engineer's decision, I would ask them to run additional simulations with different resistor values and with the ADC input model included, and to measure the actual jitter at the ADC clock input in the lab once the board is built. I would also suggest they look at the ADC datasheet to understand the actual jitter tolerance and whether the expected jitter from the reflection is within spec.

If the engineer remains resistant, I would escalate the discussion to the design review as a whole, presenting the technical analysis to the team and letting the group evaluate the trade-offs. This removes the personal confrontation and focuses on the engineering merits.

The key principle is to separate the person from the problem. The engineer's work is not being rejected—the design is being improved. I would make it clear that the review process exists to catch exactly these kinds of issues, and that finding a problem in review is a success, not a failure.

**Possible follow-ups:** How would you handle the situation if the engineer's simulation actually does show that the resistor improves the clock signal, but you still believe the approach is risky? How would you balance the need to maintain the engineer's confidence with the need to ensure the design is correct?