# debugging-failure-analysis — Day 26

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a classic case where the stack trace is telling us *where* the fault manifests, but not necessarily *why*. The first principle is to distrust the stack trace as the root cause location — memory corruption often manifests at the point of use, not the point of corruption. I'd approach this systematically:

1. **Reproduce and capture the full fault context.** I'd want the fault status registers (CFSR, HFSR, BFAR, MMFSR on ARM Cortex-M) — these tell us whether it's a bus fault, usage fault, or memory management fault, and often give the faulting address. The stack trace alone isn't enough.

2. **Look for memory corruption sources.** Since the copy operation itself is valid, something is likely corrupting memory elsewhere — a buffer overflow, a dangling pointer, a DMA writing to the wrong address, or a stack overflow in another context. I'd examine:
   - Whether the memory regions involved are adjacent to other buffers that could overflow
   - Whether any DMA channels could be writing into the affected region
   - Whether the copy operation itself could be interrupted by an ISR that also accesses the same memory
   - Whether the stack pointer was valid at the time of the fault

3. **Check for race conditions.** If the copy operation is in the main loop but an ISR also accesses the same memory region, you can get corruption that's timing-dependent. I'd look at whether the fault correlates with specific interrupt activity.

4. **Use hardware watchpoints.** If I can reproduce the fault, I'd set a data watchpoint on the memory region being copied to catch the first write that corrupts it — this often reveals the true culprit much faster than code inspection.

5. **Examine the memory map.** I'd verify that the linker script places buffers and variables where expected, and that there's no overlap between heap, stack, and static data regions.

The key insight is that a valid-looking copy operation with corrupted data means the corruption happened *before* the copy — the investigation needs to move upstream to find who wrote the bad data.

**Possible follow-ups:**
- How would you determine whether this is a stack overflow versus heap corruption, and what tools would you use?
- If the fault only occurs after several hours of operation, how would you accelerate reproduction?

---

## Q2: How would you approach debugging a medical device where the failure occurs only when the device is connected to a specific accessory cable, but never when using the test harness on the bench?

**Answer:** This points to something specific about that cable — its electrical characteristics, pinout, or construction. I'd approach this in stages:

1. **Characterize the cable versus the test harness.** I'd measure:
   - Pin-to-pin continuity and resistance
   - Insulation resistance between pins and to shield
   - Capacitance between conductors
   - Whether the cable has any internal components (ferrites, resistors, ESD protection) that the test harness lacks
   - Shield termination — is the shield connected at both ends, one end, or floating?

2. **Check the connector interface.** A subtle issue could be in the connector itself — a slightly different mating depth, a pin that doesn't fully seat, or a shell that makes intermittent contact. I'd inspect the connector on the device side for damage or contamination.

3. **Look at what signals the cable carries.** If it's a power cable, I'd check for voltage drop under load, or whether the cable introduces inductance that causes instability in a power supply. If it's a data cable, I'd look at signal integrity — the cable's impedance, length, and termination could cause marginal timing.

4. **Compare the electrical environment.** The test harness might provide a cleaner ground reference or better shielding. The accessory cable might introduce a ground loop, common-mode noise, or a different return path that affects the device's operation.

5. **Test with the cable in stages.** If possible, I'd use a break-out or extension to probe signals while the device is connected to the accessory cable — this lets me see what's actually happening on the bus or power rail during the failure.

6. **Consider ESD or transient events.** The cable might act as an antenna, coupling in noise that the test harness doesn't. I'd check whether the failure correlates with any environmental activity.

The systematic approach is to treat the cable as a component with its own electrical characteristics, not just a passive wire — measure it, compare it to the known-good harness, and isolate which electrical parameter is causing the problem.

**Possible follow-ups:**
- If the cable measures electrically identical to the test harness, what would you investigate next?
- How would you determine whether the issue is in the cable itself or in the connector on the device side?

---

## Q3: How would you approach a failure investigation where a medical device's power supply exhibits a periodic voltage dip on a 3.3V rail — the dip is about 200mV and lasts for roughly 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently?

**Answer:** The periodicity is the key clue here — something is drawing current every 100ms. I'd approach this systematically:

1. **Identify what happens every 100ms.** This is the first question. It could be a sensor sampling interval, a wireless beacon, an LED blink, a display refresh, or a communication poll. I'd correlate the dip with firmware activity by:
   - Monitoring a GPIO toggle that marks the suspected event
   - Using a logic analyzer to capture the event timing alongside the power rail
   - Checking the firmware's periodic task schedule

2. **Measure the dip at multiple points.** I'd probe the rail at:
   - The regulator output
   - The load (at the IC that's resetting)
   - At the decoupling capacitors nearest the suspected load
   This tells me whether the dip is a regulator response issue or a distribution/decoupling problem.

3. **Analyze the load transient.** A 200mV dip for 50µs suggests either:
   - The regulator can't respond fast enough to a sudden current step (bandwidth limitation)
   - The decoupling capacitance is insufficient for the transient
   - There's excessive inductance between the regulator and the load
   - The regulator is entering current limit or foldback

4. **Calculate the expected transient.** I'd estimate the current step from the load's datasheet, then calculate what voltage dip to expect given the regulator's bandwidth and the board's decoupling. This tells me whether the observed dip is reasonable or whether something else is going on.

5. **Check the reset threshold.** The device resets "occasionally" — I'd look at the reset IC's threshold and hysteresis. If the dip is marginal (just barely crossing the threshold), small variations in temperature, load, or component tolerance would explain the intermittency.

6. **Look at the regulator's load transient response.** I'd check the datasheet for the expected transient response to a step load. If the regulator's bandwidth is too low for the 100ms periodic load, I'd consider adding bulk capacitance near the load or increasing the regulator's output capacitance.

The key is correlating the periodic event with the dip, then determining whether the dip is a design margin issue (not enough decoupling, regulator too slow) or a fault condition (something drawing excessive current).

**Possible follow-ups:**
- How would you determine whether the fix should be more bulk capacitance, a faster regulator, or a change in firmware timing?
- If the 100ms event is a wireless transmission, how would you approach the interaction between RF current draw and the reset issue?

---

## Q4: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication error is caused by a marginal timing violation or a firmware race condition — the device occasionally fails to complete a sensor read within the required time window, and the error rate increases as the device warms up?

**Answer:** This is a classic cross-functional disagreement where both hypotheses are plausible and the temperature dependence is a critical clue. I'd structure the investigation to gather data that discriminates between the two:

1. **First, establish a shared understanding of the failure.** I'd bring both teams together to agree on:
   - The exact timing requirements of the sensor read (setup/hold times, clock frequency, timeout values)
   - The firmware's expected behavior (interrupt priorities, blocking calls, ISR durations)
   - What "fails to complete within the required time window" means precisely — is it a timeout, a NACK, or a data error?

2. **Instrument the system to capture both domains simultaneously.** I'd want:
   - A logic analyzer on the communication bus (capturing actual timing)
   - Firmware instrumentation (timestamped logs of when the read started, when the ISR fired, when the timeout occurred)
   - Temperature monitoring (to correlate with the warm-up effect)

3. **Analyze the temperature dependence.** This is the most discriminating clue. I'd ask:
   - Does the sensor's timing specification change with temperature? (Some sensors have longer conversion times at temperature extremes)
   - Does the MCU's clock drift with temperature? (Crystal oscillator frequency can shift)
   - Do pull-up resistor values change enough to affect rise times? (Resistor values drift with temperature)
   - Does the firmware's execution time change? (Flash access time can increase at temperature)

4. **Look for marginal timing margins.** If the logic analyzer shows the sensor's clock or data timing is close to the spec limit at room temperature, the warm-up effect could push it over. I'd measure the actual timing margins at both room temperature and at the failure temperature.

5. **Examine the firmware race condition hypothesis.** If the timing on the bus looks fine, I'd look at whether the firmware could be delayed by other tasks or ISRs — a higher-priority interrupt that occasionally runs long, or a blocking call that delays the sensor read start. The temperature dependence could be explained if the firmware's execution time increases (e.g., flash wait states at higher temperature).

6. **Design a discriminating experiment.** For example:
   - If the timing violation hypothesis is correct, adding a small delay before the read should fix it consistently
   - If the race condition hypothesis is correct, changing interrupt priorities or adding a mutex should fix it
   - I'd propose one experiment at a time, with both teams agreeing on the expected outcome for each hypothesis

The goal is to move from opinion-based disagreement to evidence-based conclusion. The temperature dependence is the key clue that should guide the investigation — it narrows down which parameters are likely to be marginal.

**Possible follow-ups:**
- How would you handle the situation if the evidence supports one team's hypothesis but the other team still disagrees?
- What specific measurements would you take to characterize the timing margin as a function of temperature?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and delicate situation. The senior engineer's experience is valuable, but acting on an unconfirmed hypothesis in a medical device context could be dangerous — both for patient safety and for the project timeline if the fix doesn't address the real root cause. I'd approach it this way:

1. **Acknowledge and validate their experience.** I'd start by genuinely engaging with their hypothesis. Their experience with a similar device is a legitimate data point, and dismissing it would damage trust. I'd ask them to walk me through the similarities and differences between the previous device and the current one — this often reveals whether the hypothesis is truly applicable.

2. **Frame the discussion around evidence, not authority.** I'd shift the conversation from "I believe X" to "What evidence would confirm or refute X?" I'd ask: "If your hypothesis is correct, what would we expect to see in the data? What test would give us confidence?" This turns the disagreement into a collaborative investigation.

3. **Propose a parallel path.** I'd suggest we can pursue both tracks simultaneously: implement the fix they're proposing (if it's safe and reversible) while also continuing the investigation to confirm root cause. This respects their urgency while maintaining rigor. However, I'd be clear that the fix won't be released until root cause is confirmed.

4. **Use the regulatory framework as a neutral arbiter.** In medical devices, we have a formal process — the 8D or CAPA process — that requires root cause confirmation before corrective action. I'd frame the need for evidence as a regulatory requirement, not a personal preference. This depersonalizes the disagreement.

5. **If the engineer continues to push:** I'd have a private conversation to understand their underlying concern — are they worried about schedule, do they have additional information they haven't shared, or is there a personal dynamic? Understanding the "why" behind their push helps address the real issue.

6. **Escalate if necessary.** If the engineer is unwilling to follow the evidence-based process and their actions could compromise patient safety or regulatory compliance, I'd escalate to the project sponsor or quality management. This is a last resort, but in a medical device context, the process exists for a reason.

The key is to maintain respect for the engineer's experience while holding the line on evidence-based decision-making. The goal isn't to win an argument — it's to find the actual root cause and implement a fix that's proven to work.

**Possible follow-ups:**
- What if the senior engineer's proposed fix is low-risk and could be implemented quickly — would you allow it while the investigation continues?
- How would you handle this if the senior engineer is also the person who designed the original device?