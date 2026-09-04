# debugging-failure-analysis — Day 45

## Q1: How would you approach a failure investigation where a medical device's analog measurement channel produces accurate readings during bench testing, but the readings become noisy and unstable when the device is connected to the clinical network via its Ethernet port — even though the network traffic is minimal?

**Answer:** This is a classic conducted susceptibility or ground-loop problem. My first step would be to characterize the noise signature — I'd capture the analog channel output on an oscilloscope while the Ethernet link is active and compare it to the baseline. I'd look at the noise frequency content: if it's correlated with Ethernet packet activity (even minimal traffic has periodic link pulses and keepalives), that points to coupling from the Ethernet PHY or transformer.

Next, I'd check the grounding topology. A common issue is that the Ethernet cable's shield or the network ground creates a ground loop with the device's chassis ground, causing current to flow through the PCB ground plane and modulate the analog reference. I'd measure the voltage difference between the device ground and the network ground — anything more than a few hundred millivolts is suspicious.

I'd also examine the physical layout: where does the Ethernet transformer sit relative to the analog front-end? Is there a ground plane split or a bridge that allows return currents from the Ethernet side to flow under the analog circuitry? I'd look at whether the analog reference and the ADC's ground connection are in the path of any Ethernet return current.

The fix often falls into one of several categories: improving the ground topology (single-point grounding or proper isolation), adding common-mode filtering on the Ethernet side, or moving the analog reference to a cleaner point in the power distribution. I'd also verify that the Ethernet transformer's center tap is properly decoupled and that the PHY's power supply isn't coupling noise back onto a shared rail.

**Possible follow-ups:** How would you determine whether the noise is common-mode or differential-mode? What measurements would you take to confirm a ground loop before making design changes?

---

## Q2: How would you approach debugging a medical device where a firmware update appears to have introduced a new intermittent failure — the device occasionally resets during normal operation, and the resets began only after the update was deployed to the field?

**Answer:** The first thing I'd do is resist the assumption that the firmware change itself is the root cause. Firmware updates often change timing, power consumption patterns, or peripheral usage in ways that expose latent hardware marginalities. I'd start by comparing the new firmware's behavior to the old version — specifically looking at what changed: clock configuration, peripheral initialization order, power management settings, or interrupt priorities.

I'd review the watchdog configuration first, since resets often trigger watchdog timeouts. If the watchdog is expiring, the question becomes whether the firmware is genuinely stuck (a software bug) or whether something is preventing the watchdog from being serviced — for example, a longer-than-expected interrupt service routine or a peripheral hanging the bus.

I'd also look at power consumption profiles. If the new firmware enables additional peripherals or changes the duty cycle, the power supply might be operating closer to its limit, making it more susceptible to transient dips. I'd measure the supply rails during the exact operations that are new or changed in the update.

Another angle is memory layout. A firmware update often shifts code and data addresses. If there's a marginal timing issue on the flash interface or a subtle stack overflow that was previously masked by the old memory layout, the new binary could expose it. I'd check whether the reset is a hardware reset (brown-out, watchdog) or a software reset by examining the reset cause register.

Finally, I'd want to correlate the resets with specific user actions or device states. If the resets cluster around a particular feature that was modified, that narrows the investigation significantly. I'd also check whether the update changed any timing parameters that could interact with hardware margins — for example, I2C clock speed or ADC sampling rate.

**Possible follow-ups:** How would you determine whether the reset is caused by a watchdog timeout, a brown-out, or a software-initiated reset? What role would the reset cause register play in your investigation?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit overheats, but only when the device is placed on a specific type of conductive surface (like a metal cart)? The charger IC is not damaged, and the device charges normally on a non-conductive surface.

**Answer:** This pattern — failure only on a conductive surface — strongly suggests a thermal management or heat dissipation issue rather than an electrical fault. The charger IC itself isn't damaged, which tells me the overheating is likely a case of localized heat buildup exceeding the component's thermal limits, not an electrical overstress event.

My first step would be to measure the actual temperatures. I'd use a thermal camera to map the heat distribution on the device when placed on the conductive surface versus a non-conductive one. I'd also place thermocouples at critical points: the charger IC case, the PCB near the charging circuit, the battery, and the enclosure surface. The key question is whether the conductive surface is acting as a heat sink (drawing heat away from one area) or as a heat source (reflecting or trapping heat).

A common mechanism here is that the metal surface provides a low-thermal-resistance path that changes the heat flow pattern. If the device's enclosure has a thermal pad or a heat-spreading feature that normally dissipates heat through the bottom, a conductive surface might create a hot spot by conducting heat back into a specific component. Alternatively, if the metal cart is in a warm environment or has its own heat sources, it could be raising the ambient temperature locally.

Another angle is electrical: the conductive surface could be creating a parasitic capacitance or a ground path that changes the switching behavior of the charger. I'd check whether the charger's switching frequency or duty cycle changes when the device is on the metal surface. I'd also verify that the surface isn't creating a short between exposed metal parts of the device or the charger's output.

I'd also review the charger IC's thermal protection behavior. If the IC has thermal regulation (reducing charge current as temperature rises), the overheating might be the IC operating at its thermal limit rather than a fault. The question becomes whether the design adequately dissipates heat under all realistic use conditions — and whether the metal surface scenario was considered in the thermal design verification.

**Possible follow-ups:** What specific measurements would you take to distinguish between a thermal conduction problem and an electrical coupling problem? How would you verify that the charger IC's thermal protection is functioning correctly?

---

## Q4: How would you approach a situation where you're leading a cross-functional failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a situation where the technical investigation is straightforward but the human dynamics require careful handling. My approach would be guided by the principle that the goal is to fix the problem, not to assign blame — and that the investigation's credibility depends on the evidence, not on who made the original decision.

First, I'd make sure the evidence is airtight before discussing findings with anyone. I'd want the root cause analysis to be reproducible and documented — not just a hypothesis, but a demonstrated causal chain. This protects both the investigation and the individual, because it ensures we're acting on facts rather than assumptions.

When it comes to communicating the finding, I'd start by discussing it privately with the senior engineer before presenting it to the broader team. This isn't about softening the message — it's about giving them the opportunity to engage with the evidence, contribute additional context about why the design decision was made (which might reveal constraints we didn't know about), and prepare for the team discussion. It also prevents them from being blindsided, which is both respectful and practically important — a defensive reaction in a group setting can derail the investigation.

In the team presentation, I'd frame the finding in terms of the design decision and its consequences, not the individual. I'd emphasize that design decisions are made with the best available information at the time, and that this finding represents a learning opportunity for the whole team. I'd also make sure the corrective action focuses on process improvements — for example, adding a design review checkpoint or a verification test that would have caught the issue — rather than on individual accountability.

If the senior engineer disagrees with the finding, I'd handle that as a technical disagreement, not a personal one. I'd invite them to present their counter-evidence, and I'd be willing to revisit the analysis if they raise valid points. The investigation's integrity depends on being open to challenge, even when the evidence seems clear.

**Possible follow-ups:** What if the senior engineer refuses to accept the finding and becomes defensive in the team meeting? How would you balance maintaining the investigation's integrity with preserving team relationships?

---

## Q5: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory regions being copied are within their allocated bounds?

**Answer:** This is a particularly frustrating class of bug because the obvious causes — invalid pointers, buffer overflows, out-of-bounds access — have been ruled out. When the stack trace points to a memory copy with valid addresses and valid bounds, I'd broaden the investigation beyond the copy operation itself.

My first step would be to examine what's happening around the copy. A hard fault during a memory copy with valid parameters often means the fault is actually occurring because of a corrupted stack, a misaligned access, or a fault that happens to manifest during the copy but is caused by something earlier. I'd look at the fault status registers — specifically the hard fault status register (HFSR), configurable fault status register (CFSR), and the memory management fault address register (MMFAR) or bus fault address register (BFAR). These tell me whether the fault is a bus error, a memory management fault, a usage fault, or something else.

If the fault is a bus error during the copy, I'd check whether the copy is accessing memory that's been powered down or clock-gated. In a low-power medical device, it's possible that a peripheral's memory or a RAM bank is disabled during certain sleep modes, and the copy is attempting to access it. The address might be "valid" in the sense that it's within the memory map, but the memory might not be accessible at that moment.

Another angle is stack corruption. If the stack pointer has been corrupted by an earlier operation, the fault handler's stack trace might be misleading — the "return address" pointing to the memory copy could be garbage that happens to land in a plausible location. I'd check the stack pointer's value at the time of the fault and compare it to the expected stack depth. I'd also look for signs of stack overflow — for example, checking whether the stack has grown into a protected region or into another memory area.

I'd also consider alignment issues. If the copy operation is using a word-sized access on a misaligned address, that can cause a hard fault on some architectures. The compiler usually handles alignment, but if the copy is operating on a packed struct or a buffer with unusual alignment, this can happen.

Finally, I'd look at whether the copy is being interrupted. If a higher-priority interrupt fires during the copy and that interrupt handler corrupts memory or the stack, the copy might fault when it resumes. I'd examine the interrupt nesting and whether any ISR writes to memory regions that overlap with the copy's source or destination.

**Possible follow-ups:** How would you use the fault status registers to narrow down the type of fault? What role would stack depth monitoring or stack canaries play in your investigation?