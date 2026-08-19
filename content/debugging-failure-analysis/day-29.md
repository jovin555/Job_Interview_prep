# debugging-failure-analysis — Day 29

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a classic case where the stack trace is telling us *where* the fault manifests, but not necessarily *why*. When the memory copy operation itself checks out — valid pointers, correct lengths — I'd broaden the investigation beyond the copy routine itself.

First, I'd verify the stack trace is actually reliable. In deeply embedded systems, a corrupted stack pointer or a fault that occurred during an interrupt can produce misleading backtraces. I'd check whether the fault occurred in thread mode or handler mode, and whether the stack pointer at the time of the fault was valid. If the stack was corrupted, the "memory copy" we see might just be where the corrupted stack happened to point.

Assuming the trace is accurate, I'd look at what's happening *around* the copy. Is the copy operation itself the problem, or is it copying data that's in an unexpected state? For example, if the copy is copying a structure that contains a pointer, and that pointer is invalid, the copy might be fine but the data being copied is corrupted. I'd examine the data being copied — is it consistent with what's expected? Could there be a race condition where another task or interrupt is modifying the source data while the copy is in progress?

I'd also check the memory map. Is the copy crossing a boundary between memory regions with different wait states or bus widths? On some microcontrollers, copying across certain boundaries can trigger bus faults if the memory controller isn't configured correctly. Similarly, if the copy is using DMA, I'd check for DMA descriptor corruption or alignment issues.

Finally, I'd look at the broader system state at the time of the fault. What was the device doing? Was it in a low-power mode? Was a peripheral active? Were interrupts disabled or enabled? The fault might be a symptom of a deeper issue — for example, a voltage droop during a high-current operation causing a flash read to fail, or a clock glitch causing a bus transaction to complete incorrectly.

**Possible follow-ups:**
- How would you determine whether the stack trace is reliable before trusting it?
- What specific instrumentation would you add to the firmware to capture more context around the fault?

---

## Q2: How would you approach debugging a medical device where the failure occurs only when the device is connected to a specific accessory cable, but never when using the test harness on the bench?

**Answer:** The key here is that the accessory cable is the differentiator, so I'd start by characterizing that cable as thoroughly as possible. The fact that the test harness works fine tells me the device itself is probably functional — the issue is in the interaction between the device and this specific cable.

First, I'd do a detailed electrical characterization of the cable. I'd measure continuity on every pin, check for intermittent connections (especially at the connector ends where strain relief might be poor), and measure resistance and capacitance on each line. I'd also check for shorts between pins — a subtle short between two signal lines that only manifests under certain conditions (like when the device drives both lines simultaneously) could explain the intermittent nature.

Next, I'd look at the cable's pinout versus what the device expects. Is this cable wired to the same pinout as the test harness? Could there be a swapped pair, or a pin that's tied to ground or VCC that the harness leaves floating? I'd also check whether the cable has any active components — some cables include level shifters, ESD protection, or identification resistors that could affect signaling.

I'd also consider the cable's length and construction. A longer cable with higher capacitance could cause signal integrity issues — slower edges, more ringing, or crosstalk between adjacent lines. If the device's firmware has tight timing requirements, the additional propagation delay or signal degradation could push things out of spec.

I'd then reproduce the failure with the suspect cable and probe the signals at both ends — at the device connector and at the far end of the cable. Comparing the waveforms against the test harness would show me exactly where the signal degrades. I'd also check whether the cable's shield or drain wire is connected correctly, since a floating shield can turn the cable into an antenna.

Finally, I'd check the mechanical side. Is the cable's connector fully seating? Could there be a bent pin or a connector shell that's not grounding properly? Sometimes a cable that "works" on the bench but fails in the field is a mechanical issue that only shows up when the cable is stressed or positioned differently.

**Possible follow-ups:**
- What if the cable passes all electrical tests — how would you proceed?
- How would you determine whether the issue is signal integrity versus a firmware timing issue that the cable's characteristics expose?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a classic interoperability issue, and the first thing I'd do is characterize both chargers electrically. The "specific model" charger likely differs from the shipping charger in some measurable way — output voltage, current capability, ripple, or negotiation behavior.

I'd start by measuring the suspect charger's output under load. Many USB chargers have different profiles — some provide 5V at 500mA, others negotiate higher currents via USB BC 1.2 or USB-PD. If the suspect charger is advertising a higher current capability than the device expects, the charging circuit might be trying to draw more current than it should. I'd also check the charger's output voltage under load — a charger with poor regulation might sag under load, causing the charging circuit to compensate by drawing more current.

I'd also look at the charger's inrush behavior. Some chargers have a slow ramp-up or a "soft start" that can interact badly with the device's input capacitance. If the device's charging circuit has a large bulk capacitor, the charger might see it as a near-short at power-on and current-limit in a way that causes excessive current draw.

Next, I'd examine the device's charging circuit itself. Does it have input overvoltage protection? Some USB chargers produce voltage spikes or transients when they're unplugged or when the load changes suddenly. If the device's protection circuit is responding to these transients in an unexpected way — for example, by partially enabling a crowbar circuit — that could explain the excessive current.

I'd also check the USB negotiation protocol. If the device uses USB BC 1.2 or USB-PD to determine how much current it can draw, and the suspect charger implements the negotiation differently (or incorrectly), the device might be drawing more current than the charger can safely provide. This is a common failure mode with third-party chargers that don't fully implement the spec.

Finally, I'd look at the thermal behavior. If the suspect charger runs hotter, its output characteristics might change over time — voltage droop, increased ripple, or current limiting kicking in earlier. The excessive current draw might only occur after the charger has warmed up.

**Possible follow-ups:**
- How would you determine whether the issue is in the device's charging circuit or in the charger itself?
- What safety considerations would you factor into this investigation given it's a medical device?

---

## Q4: How would you approach debugging a medical device where the firmware occasionally fails to wake from a low-power sleep mode, and the failure is more frequent when the device has been in sleep for longer periods — the device is supposed to wake on an RTC alarm, but sometimes the RTC interrupt fires and the firmware doesn't resume execution?

**Answer:** The correlation with sleep duration is a strong clue — it suggests something is degrading or drifting over time, or that the device is entering a deeper sleep state than intended. I'd start by verifying what the device is actually doing during sleep.

First, I'd measure the current consumption profile during sleep. If the device is supposed to be in a light sleep mode but is actually entering a deeper mode (or vice versa), that would explain why the RTC interrupt isn't waking it properly. I'd use a current probe or a precision shunt to capture the sleep current waveform and compare it against the expected profile for each sleep mode.

Next, I'd check the RTC itself. Is the RTC actually generating the interrupt? I'd verify that the RTC alarm is set correctly and that the interrupt flag is being set. I'd also check whether the RTC is running from the correct clock source — if the RTC is supposed to run from a 32.768 kHz crystal but is actually running from an internal RC oscillator, the timing could drift, and the alarm might fire at the wrong time or not at all.

I'd also look at the wake-up path. Many microcontrollers require specific conditions to wake from sleep — an interrupt on a specific pin, a specific clock source, or a minimum voltage. If the device's voltage regulator is in a low-power mode during sleep, the RTC interrupt might not have enough voltage to trigger the wake-up properly. I'd check the power supply behavior during the wake-up transition — is there a voltage droop or a slow ramp that prevents the firmware from starting correctly?

The "longer sleep periods" correlation makes me think about the RTC's clock source. If the RTC is running from a crystal, I'd check the crystal's startup behavior. Some crystals have slow startup times, and if the RTC is being powered down and restarted, it might not be stable when the alarm fires. I'd also check whether the RTC's backup domain is properly powered — if the RTC loses power during sleep, it might reset and lose the alarm setting.

Finally, I'd add instrumentation to the firmware to capture the wake-up sequence. I'd log the RTC interrupt flag, the wake-up source, the time since the last wake-up, and the firmware's execution path after the interrupt. This would tell me whether the interrupt is firing but the firmware is getting stuck, or whether the interrupt isn't firing at all.

**Possible follow-ups:**
- How would you distinguish between a hardware issue (RTC not generating the interrupt) and a firmware issue (interrupt fires but the handler doesn't execute)?
- What specific measurements would you take to verify the device is in the intended sleep mode?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. The engineer is becoming frustrated, and the project schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge the engineer's effort and the difficulty of the problem — frustration in this situation is natural, and validating that is important for maintaining morale. Then I'd refocus the investigation from component-level testing to system-level interactions.

The fact that components pass in isolation but the system fails points to an integration issue — something that only manifests when components interact. I'd guide the engineer to shift from "is this component working?" to "how are these components interacting?" This might mean looking at timing relationships, shared resources (power rails, ground, communication buses), or environmental factors (temperature, EMI, load).

I'd ask the engineer to walk me through their debugging process in detail — what they've tested, what they've observed, and what they've concluded. Often, the act of explaining the process reveals assumptions or gaps. I'd also ask what they haven't tested yet — sometimes the most productive question is "what have you ruled out, and how confident are you in that ruling?"

I'd then suggest a structured approach to isolate the interaction. This might involve:
- Adding instrumentation to observe system-level behavior (logic analyzer on the bus, current probe on the power rail, thermal camera for hot spots)
- Creating a minimal reproduction — strip the system down to the fewest components that still exhibit the failure
- Deliberately perturbing variables one at a time (clock speed, supply voltage, temperature) to see what changes the failure behavior

I'd also consider whether the engineer needs a different tool or perspective. Sometimes a fresh set of eyes helps — I might pair them with another engineer for a brainstorming session, or bring in someone with different expertise (e.g., a firmware engineer if the issue seems hardware-related, or vice versa).

Finally, I'd set a time-box for the next investigation phase. If we don't make progress within a defined period, we escalate — either by bringing in additional expertise or by considering design changes that might sidestep the issue. The goal is to keep momentum while being honest about the investigation's status.

**Possible follow-ups:**
- How would you balance giving the engineer ownership of the investigation versus stepping in to take over?
- What would you do if the engineer's frustration is affecting their work quality or the team's dynamics?