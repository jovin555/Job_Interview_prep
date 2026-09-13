# space-rad-hard — Day 54

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** The core idea is to treat the two feeds as independent, fault-isolated sources that are combined only after each has passed through its own protection and current-limiting stage, so a fault on one branch cannot propagate to the other or to the common load.

I'd start by giving each 28V input its own front-end: reverse-polarity protection, transient/surge clamping, and an inrush-limiting element (a hot-swap controller or a pass FET with a controlled slew of the gate, plus a sense resistor for current monitoring). The hot-swap controller is what lets you plug into a live bus without a large inrush that would sag the bus — it ramps the FET on slowly and trips if the current exceeds a programmed limit for longer than a blanking window.

For fault isolation, each feed gets its own latching overcurrent protection. A single-event latch-up in a downstream load looks electrically like a sudden low-impedance short, so the protection has to be fast enough to limit the fault current before it drags the bus down, but slow enough not to nuisance-trip on legitimate inrush. That's the classic trade-off: set the current limit above worst-case inrush but below the level that would disturb the bus, and use a timed blanking window so the inrush spike is ignored while a sustained fault still trips.

To combine the two feeds without one back-feeding the other, I'd use ORing — either ideal-diode controllers or ORing FETs — so each branch can only source current, never sink it. That way, if one feed shorts or its protection trips, the other continues to supply the load. If the load itself is the fault, the ORing still lets the healthy feed try to supply it, so the load-side protection has to be coordinated with the feed-side protection.

For hot-swap, the key is that the act of inserting or removing a feed must not glitch the common rail. That means the hot-swap controller on the incoming feed ramps up into the already-live rail, and the ORing prevents any reverse current during the transition. I'd also add bus voltage monitoring and a controlled hand-off so the system knows which feed is active.

Throughout, I'd be thinking about derating and single points of failure: no single component should be able to take down both feeds, and every protection element should be evaluated for how it behaves under radiation (a latch-up in the protection FET itself would be ironic). Where a part has no radiation data, I'd either qualify it or add redundancy around it.

**Possible follow-ups:**
- How would you coordinate the trip thresholds between the feed-side and load-side protection so you don't get cascading trips or a fault that neither catches?
- If the hot-swap controller itself is a COTS part with no radiation data, how would you decide whether it's acceptable in this role?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are two separate margins that have to be managed together, and the interaction is where a lot of designs get into trouble.

Derating is about reducing the electrical, thermal, and mechanical stress on a part below its rated maximum so that it has margin for the full mission life. Typical practice is to derate voltage, current, power, and junction temperature by some percentage — the exact numbers depend on the program's derating standard, but the principle is that a part running at 80% of its ratings has more margin against parametric drift, transients, and wear-out than one running at 100%. For a space board, I'd apply derating to every part, including the passives: capacitor voltage ratings, resistor power ratings, inductor saturation current, and connector current per pin.

The interaction with radiation is that radiation effects eat into the same margin derating is supposed to preserve. Total ionizing dose causes parametric shifts — threshold voltage drift, leakage current increase, gain degradation — so a part that starts with 20% margin might have none left after the dose accumulates. That means the derating budget has to account for the end-of-life, post-irradiation parameters, not the beginning-of-life datasheet numbers. If a part's radiation data shows it drifts 10% over the mission dose, that drift has to come out of the derating margin, not be added on top of it.

For part selection, I'd work in tiers. First choice is a part with qualified radiation data — either a rad-hard part or a COTS part with published test results — because then I can derate against known post-irradiation behavior. If no such part exists, I have to decide whether to qualify it myself (test it, or bound the risk analytically) or design around it. A part with no radiation data isn't automatically disqualified, but it has to be treated as an unknown: I'd derate it more aggressively, add margin for parametric drift, and consider whether a fault in that part is tolerable or needs redundancy.

The other interaction is single-event effects. Derating doesn't help with SEU or SEL — a latch-up can happen at any voltage — so those need their own mitigation (current limiting, TMR, scrubbing) regardless of how much electrical margin the part has. Derating and SEE mitigation are complementary, not substitutes.

Finally, I'd document the derating rationale and the radiation assumptions together, because they're really one margin analysis. If the radiation environment is uncertain, the derating has to be conservative enough to cover the uncertainty.

**Possible follow-ups:**
- How would you handle a part where the radiation data exists but only at a different dose rate than your mission?
- Where does derating stop being useful and redundancy have to take over?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different things: TMR on the digital side protects against upsets in the digital logic, but it does nothing for a fault that originates in the analog front-end. If the sensor, amplifier, or ADC produces a wrong value, TMR on the downstream digital logic will faithfully process and vote on that wrong value — it can't detect that the input itself was bad. So "the digital side has TMR" is not coverage for the analog side; it's coverage for a different failure mode.

The real question is what failure modes the analog chain has and whether they're tolerable. Single-event transients on the amplifier or ADC reference can produce a momentary wrong reading; a single-ended chain has no way to detect that, so the control loop acts on it. If the measurement is time-sensitive and can't simply be retried, that's a real risk. Similarly, a stuck or drifted sensor produces a persistently wrong value that looks perfectly valid to the digital side.

How I'd evaluate it depends on the criticality of the measurement. If a wrong reading for one sample cycle is tolerable — the control loop has enough inertia, or the measurement is averaged over many samples — then a single-ended chain might be acceptable with some filtering and plausibility checks. If a wrong reading can cause a dangerous action, then the analog side needs its own integrity mechanism.

Options for that include: a second, independent measurement path (a redundant sensor or a second ADC channel) so the two can be compared; a plausibility check against a model or against other correlated measurements; a ratiometric or differential measurement that rejects common-mode transients; or a sample-and-hold with a hold capacitor that limits how fast a transient can corrupt the reading. The point is that the analog side needs its own detection, not just a digital vote downstream.

I'd also push back on the framing that TMR "covers" anything. TMR is a mitigation for a specific failure mode (transient upsets in logic), and it has its own limits — it doesn't help if the voter itself is upset, or if the fault is common-mode across all three copies. So the right conversation is failure-mode-by-failure-mode: what can go wrong in the analog chain, what can go wrong in the digital chain, and what mitigation addresses each.

**Possible follow-ups:**
- If you add a second analog path for comparison, how do you decide which one is right when they disagree?
- How would you handle a common-mode fault that affects both analog paths at once?

## Q4: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, and single-event upsets (SEUs) can corrupt individual messages?

**Answer:** The starting point is to assume that any individual message can be corrupted, and design the protocol so that corruption is detected and recovered from rather than silently accepted.

At the physical layer, I'd choose a bus that has inherent robustness — differential signaling for common-mode noise rejection, and a topology that doesn't let one node's fault take down the whole bus. For a multi-drop bus, that means thinking about what happens if a node's transceiver latches up or drives the bus permanently: the bus needs to be able to isolate a misbehaving node, either through series protection or through a star/hub topology where the controller can disable a branch.

At the protocol layer, every message needs integrity checking. A CRC is the baseline — it catches random bit corruption with high probability. But CRC alone doesn't tell you whether a message is fresh or a replay, so I'd add a sequence number or a timestamp so the controller can detect a message that's been delayed or duplicated. For critical data, I'd consider message authentication or at least a node ID plus sequence number so a corrupted header can't be mistaken for a different node's message.

For recovery, the protocol needs retransmission with a bounded retry count, and the controller needs to distinguish "no message received" from "message received but corrupt." A node that stops responding entirely is a different failure than a node sending corrupt data, and they may need different responses — the first might be a node failure, the second might be a transient upset that a retry fixes.

I'd also think about the bus arbitration and timing. If the bus uses a shared medium, an upset in one node's arbitration logic could cause it to monopolize the bus or to transmit at the wrong time. A time-triggered or controller-scheduled protocol is more deterministic than a contention-based one, which makes it easier to bound the behavior under fault.

Finally, I'd consider whether the bus itself needs redundancy. A single bus is a single point of failure; if the mission can't tolerate losing the bus, a second bus (or a ring topology with the ability to route around a break) is worth the cost. The trade-off is complexity and mass versus the probability of a bus-level fault.

**Possible follow-ups:**
- How would you handle a node that is alive but sending plausible-looking but wrong data?
- What's the trade-off between a time-triggered protocol and a contention-based one in a radiation environment?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing is to separate the technical question from the interpersonal one. The engineer has done real work, and that deserves respect — the goal isn't to win the argument, it's to get to the right answer. So I'd start by making sure I understand their reasoning, not just their conclusion. Often an under-margined proposal comes from a different set of assumptions — maybe they're using a different radiation environment, or they've bounded the risk in a way I haven't considered. Asking "walk me through how you got here" is more productive than "this is wrong."

Once I understand their reasoning, I'd make the disagreement concrete and testable. Instead of arguing in the abstract about "margin," I'd frame it as: here's the failure mode I'm worried about, here's the condition under which it occurs, and here's what I think happens to the design. That turns it into a question we can both evaluate — do we agree on the failure mode? Do we agree on the conditions? If we disagree on the facts, we can go find the data (a datasheet, a test result, a calculation). If we agree on the facts but disagree on whether the risk is acceptable, that's a different conversation, and it's one where the program's risk tolerance and the mission's criticality should decide, not seniority.

I'd also be open to being wrong. If the engineer has a bound I haven't considered, or if the failure mode I'm worried about is actually covered by something else in the design, I should update. The point of the review is to find the right answer, and a good review makes everyone's reasoning better.

If we still disagree after that, I'd escalate the decision to the right level — not as "I'm overruling you," but as "here's the risk, here's the cost of mitigating it, and here's who should decide whether to accept it." In a regulated environment, that decision often has to be documented, because the risk acceptance has to be traceable. And I'd make sure the engineer understands that the decision is about the risk, not about their competence.

Throughout, I'd keep the tone collaborative. Design reviews work best when people feel safe raising concerns and safe being challenged. If the review becomes adversarial, people stop raising real issues, and that's how problems get missed.

**Possible follow-ups:**
- What if the engineer is right and you're wrong — how do you make sure you're not just deferring to seniority?
- How would you document a risk acceptance decision so it's defensible later?