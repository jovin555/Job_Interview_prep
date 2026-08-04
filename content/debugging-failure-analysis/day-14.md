# debugging-failure-analysis — Day 14

## Q1: How would you approach a failure investigation where a medical device's analog front-end produces accurate readings on the bench, but shows a consistent offset error when connected to the patient cable — and the offset varies between different cable samples?

**Answer:** This pattern — accurate on the bench but offset with patient cables — points to something about the cable interface itself rather than the core analog chain. I'd start by characterizing the offset systematically across multiple cable samples to understand the distribution: is it always positive, always negative, or does it vary in sign? That immediately hints at the mechanism. A consistent direction suggests a systematic issue like a reference or bias path problem; varying direction suggests something like contact resistance or shield integrity.

Next, I'd examine the cable's construction and the connector interface. Common culprits in medical devices include: high-resistance connections in the cable (corrosion, cold solder joints, or worn contacts), shield termination issues that create ground loops or common-mode voltage shifts, or conductor resistance that matters when the sensor is a bridge or requires excitation current. For a bridge-type sensor, even a few ohms of extra resistance in the excitation or sense lines creates a measurable offset.

I'd also check whether the offset correlates with cable length, connector plating, or how tightly the connector is seated. A simple test is to measure the cable's pin-to-pin resistance and compare against specification, and to wiggle the cable while monitoring the reading to catch intermittent contact issues. I'd also verify the connector's mating force and whether the ground path through the cable is shared with the signal return — a common mistake is having signal and power share a return path that isn't adequately sized.

If the offset is consistent across all cables, I'd look at the input bias currents of the amplifier and whether the cable's capacitance interacts with the front-end's input impedance, potentially creating a voltage divider effect. Finally, I'd review the front-end's input protection network — some protection circuits have leakage paths that become significant when the source impedance changes.

**Possible follow-ups:** How would you determine whether the offset is caused by the cable's series resistance versus a ground potential difference between the device and the sensor? What measurements would you take to distinguish between these?

---

## Q2: How would you approach a failure investigation where a medical device's firmware occasionally writes corrupted data to its non-volatile memory, and the corruption is only detected when the device is powered on after being off for an extended period?

**Answer:** This is a classic power-cycling failure mode, and the "only detected after being off for an extended period" detail is a strong clue. I'd start by examining the power-down sequence — specifically, what happens to the supply rails when the device loses power. If the main rail decays slowly while the memory's supply rail collapses faster (or vice versa), the memory can be in an undefined state during the transition, and a write or erase operation that was in progress can complete with marginal supply voltage, producing corrupted data.

I'd also look at the reset and power-monitoring circuitry. If the microcontroller doesn't have a proper brown-out detector, or if the reset threshold is set too low, the firmware can continue executing during the power-down transient and attempt a write with insufficient voltage. The "extended period off" aspect suggests the corruption might be happening at power-down rather than power-up — the data looks fine immediately after the write, but the corruption occurs during the final moments of power loss.

Another angle is the memory's write timing. If the firmware writes to flash or EEPROM and the power fails mid-write, the memory can be left in a partially programmed state. Many devices have a write-in-progress flag or a status register that should be checked, but if the power loss happens between the check and the actual write, corruption can occur. I'd also examine whether the firmware uses a write-completion verification step and whether it handles the case where verification fails.

I'd also consider the possibility of a slow discharge path — for example, a capacitor on the supply rail that keeps the memory powered longer than the microcontroller, or vice versa. This creates a window where one device is active while the other is not, and if the microcontroller attempts a write during this window, the memory might not respond correctly.

The investigation would involve: capturing the power-down waveform with an oscilloscope (both rails and the reset line), reviewing the firmware's power-down handling and write sequences, checking the brown-out detector configuration, and potentially adding fault injection — cutting power at various points during a write cycle to reproduce the corruption.

**Possible follow-ups:** What specific measurements would you take on the power rails during power-down to identify the failure window? How would you design a fault-injection test to reproduce this corruption in a controlled way?

---

## Q3: How would you approach a situation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is an EMI/EMC interaction problem, and the correlation with the paging system is a valuable clue. I'd approach this in stages: first, characterize the failure precisely, then identify the coupling mechanism, and finally implement and verify a mitigation.

The first step is to confirm the correlation and understand the failure mode. Is the device's receiver desensitized, is the transmitter failing to start, or is the data corrupted in transit? I'd want to know whether the paging system operates at a frequency close to the device's communication band, or whether it's a broadband interference source. I'd also check whether the paging system's transmissions are continuous or pulsed — pulsed interference can cause different failure modes than continuous.

Next, I'd investigate the coupling path. There are several possibilities: radiated coupling directly into the device's antenna or RF front-end, conducted coupling through the power supply or patient cables, or coupling into the device's microcontroller causing firmware malfunction. I'd use near-field probes to scan the device while the paging system is active (or while simulating its signal) to identify where the interference enters. I'd also check whether the device's shielding and grounding are adequate — a common issue is a shield that's grounded at only one point, creating an antenna at certain frequencies.

I'd also examine the device's RF front-end design: the receiver's selectivity, the LNA's linearity, and whether there are any spurious response frequencies that align with the paging system. A spectrum analyzer measurement of the device's response to the paging signal would show whether the interference is in-band or out-of-band.

For mitigation, the approach depends on the coupling path. If it's radiated, I'd consider adding filtering, improving shielding, or changing the antenna's location or orientation. If it's conducted, I'd add common-mode chokes or ferrite beads on the affected cables. If it's a receiver selectivity issue, I might need to add a SAW filter or improve the front-end's linearity. I'd also consider firmware-level mitigation — for example, retry logic that's robust to brief interference windows, or a channel-hopping scheme that avoids the paging frequency.

Finally, I'd verify the fix by testing in the actual clinical environment, or by simulating the paging signal in the lab with a signal generator and reproducing the failure condition.

**Possible follow-ups:** How would you determine whether the interference is coupling through the antenna versus through the power or data cables? What specific measurements would you take to distinguish between these paths?

---

## Q4: How would you approach debugging a medical device where the firmware occasionally enters an infinite loop in an interrupt service routine, and the loop appears to be caused by a hardware condition that the firmware doesn't handle — specifically, a peripheral flag that remains set despite the firmware clearing it?

**Answer:** This is a classic firmware-hardware interaction problem, and the key is to understand why the flag isn't clearing. I'd start by reviewing the peripheral's datasheet to understand the flag-clearing mechanism — some peripherals require a specific sequence (read the status register, then write to a clear register), while others clear automatically when the data is read. A common mistake is clearing the wrong bit, or clearing a flag that's actually a "sticky" status bit that requires a different clearing method.

Next, I'd examine the timing. If the flag is set by a hardware event that occurs faster than the firmware can clear it, the flag can remain set and re-trigger the interrupt. For example, if a data-ready flag is set by a peripheral that's continuously producing data, and the firmware's interrupt handler takes too long to service it, the flag can be set again before the handler finishes. This creates a situation where the flag appears to never clear.

I'd also consider the possibility of a race condition between the hardware setting the flag and the firmware clearing it. If the flag is set by an edge-triggered event and the firmware clears it just before the event occurs, the flag can be set again immediately after the clear, causing the interrupt to fire again. This is a classic "interrupt storm" scenario.

Another angle is the interrupt priority and nesting configuration. If the peripheral's interrupt is set to a priority that allows nesting, and a higher-priority interrupt preempts the handler mid-way through the flag-clearing sequence, the flag can be left in an inconsistent state. I'd review the interrupt priority assignments and whether the handler disables interrupts during the critical section.

From a hardware perspective, I'd verify that the peripheral's clock is stable and that the flag is actually being set by the expected source. I'd use a logic analyzer or oscilloscope to capture the flag signal and the firmware's clear operation to see if they're in sync. I'd also check whether the peripheral's supply voltage is within specification — a marginal supply can cause the peripheral to behave erratically.

The systematic approach would be: reproduce the failure (possibly with fault injection to force the condition), capture the state of the peripheral's registers when the loop occurs, review the firmware's interrupt handler and flag-clearing sequence, and then determine whether the fix is in firmware (e.g., a more robust clearing sequence, or a timeout in the handler) or in hardware (e.g., a pull-up resistor on a signal line, or a different peripheral configuration).

**Possible follow-ups:** How would you design a firmware-level safeguard to prevent an infinite loop in an interrupt handler, even if the hardware misbehaves? What would you put in place to ensure the device fails safely in a medical context?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure analysis, especially in medical devices where the pressure to resolve issues quickly is high. I'd approach it by acknowledging the value of their experience while maintaining the integrity of the investigation process.

First, I'd have a private conversation with the senior engineer to understand their reasoning fully. It's possible they have insights from their experience that aren't immediately obvious, and I want to give them a fair hearing. I'd ask them to walk me through their hypothesis and the evidence they see supporting it. I'd also ask what evidence would convince them their hypothesis is wrong — this is a key question because it reframes the discussion from "I'm right" to "what would prove this?"

Next, I'd propose a structured approach that tests their hypothesis alongside other candidates. Rather than implementing a fix immediately, I'd suggest designing experiments or data collection that would either support or refute their theory. This respects their expertise while ensuring we don't jump to a fix based on incomplete evidence. In a medical device context, implementing an unverified fix can be worse than no fix at all — it can mask the real problem and create a false sense of security.

I'd also emphasize the importance of documenting the investigation process, especially for regulatory compliance. In medical devices, the root-cause investigation needs to be traceable — we need to show that we considered multiple hypotheses and systematically eliminated them. Jumping to a fix without proper investigation can create compliance issues later.

If the senior engineer continues to push, I'd involve other team members in the discussion to get broader perspectives. I'd also consider whether there's a way to implement their fix as a controlled experiment — for example, applying it to a small sample of units and monitoring the results while continuing the investigation in parallel. This can be a pragmatic compromise that addresses their urgency while maintaining rigor.

Ultimately, my responsibility is to the investigation's integrity and the device's safety. I'd make it clear that the decision isn't about who's right, but about what the evidence shows. I'd frame it as: "Let's test your hypothesis properly. If it's correct, we'll have strong evidence to support the fix. If it's not, we'll have saved ourselves from implementing a fix that doesn't address the real problem."

**Possible follow-ups:** How would you handle the situation if the senior engineer goes around you to a higher manager to push for their fix? What if the evidence later shows their hypothesis was correct — how would you manage the team's perception of your decision-making?