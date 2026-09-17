# space-rad-hard — Day 58

## Q1: How would you approach designing a radiation-tolerant power distribution architecture for a payload with redundant 28V bus feeds, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd start by treating the two feeds as independent sources that are only combined at the point of load, never tied together upstream. Each feed gets its own ORing element — either an ideal-diode controller or a latching relay with current-sense — so that a fault on one feed can be isolated without dragging the other down. The key architectural decision is where to place the current-limiting function: per-feed, per-load, or both. Per-feed protection alone won't stop a single latched load from pulling the whole rail down, so I'd add per-load current limiting or eFuses with latch-off behavior, sized so that a single load's latch-up trip threshold is well below the feed's total capacity.

For hot-swap, the concern is inrush into bulk capacitance when a card is inserted or a load is enabled. I'd use a hot-swap controller with programmable slew-rate control on the pass FET, plus a dV/dt-limited gate drive so the inrush stays within the feed's transient budget. The controller also needs to distinguish a legitimate inrush from a real overcurrent — usually by combining a fast trip threshold with a slower timed threshold, so a brief capacitive surge doesn't trip the breaker but a sustained fault does.

On the radiation side, the ORing and hot-swap controllers themselves are part of the threat surface. A single-event transient on the gate-drive logic could momentarily turn off a pass FET, causing a rail glitch; a single-event latch-up in the controller could hold the FET off permanently. I'd look for parts with demonstrated SET immunity on the control path, or add a supervisory layer — a small rad-tolerant supervisor that can re-enable a feed after a timeout if the controller has latched. The architecture should degrade gracefully: losing one feed should leave the payload running on the other with reduced margin, not dead.

**Possible follow-ups:**
- How would you decide between a latching relay and a solid-state ORing element for the feed isolation, given the radiation environment?
- If the hot-swap controller itself latches up, how would your supervisory layer detect that and recover without causing a bus disturbance?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being honest about what the part actually has to do. A voltage supervisor is a small, slow, low-power analog function — it doesn't need to be fast, and it doesn't need to be precise. That changes the qualification calculus compared to, say, an ADC or an FPGA. The main radiation concerns are TID-induced threshold drift (which could cause the supervisor to trip at the wrong voltage late in mission), SETs on the comparator output (which could cause a spurious reset), and SEL (which could hold the output in a wrong state).

For TID, I'd want at least a rough dose characterization — either from the manufacturer, from published test data on a similar process node, or from a low-cost cobalt-60 test at the expected mission dose plus margin. If the part is a mature bipolar or CMOS process with a well-understood behavior, the drift is often predictable enough to bound. For SETs, the output is usually a slow logic signal, so a short transient on the comparator is less likely to propagate — but I'd still add an RC filter or a digital glitch filter on the reset line, and I'd make sure the reset assertion is asymmetric: fast to assert, slow to release, so a transient doesn't cause a premature release.

For SEL, if the part is CMOS and the process isn't known to be latch-up immune, I'd either add current limiting on its supply or choose a part with a known latch-up threshold above the mission LET. If I can't get that data, I'd consider a discrete supervisor built from rad-tolerant components — a comparator with a known-good input stage, a reference, and a resistor divider — where I control every element and can derate and test each one. The trade-off is board area and complexity versus confidence in the part's behavior.

**Possible follow-ups:**
- How would you structure a low-cost radiation test campaign for a supervisor you can't get manufacturer data on?
- What would make you decide to build a discrete supervisor instead of qualifying a commercial one?

## Q3: How would you approach designing a latch-up protection scheme for a mixed-signal board where the sensitive analog front-end and the digital processing section share a common 3.3V rail, and a single-event latch-up in either section could drag the whole rail down?

**Answer:** The first thing I'd do is question the shared rail. If the analog front-end and the digital section have different current profiles and different latch-up sensitivities, sharing a rail means a latch in either one can take down both. The cleanest architecture is to split the rail at the point of regulation: a dedicated analog 3.3V regulator and a dedicated digital 3.3V regulator, each with its own current limiting and its own latch-up detection. That way a latch in the digital section doesn't corrupt the analog supply, and vice versa.

If splitting isn't possible — say, because of board area or a single-point ground requirement — then I'd add per-section current limiting on the shared rail. Each section gets an eFuse or a current-sense amplifier with a latch-off threshold set above its normal peak but below the rail's total capacity. When a latch occurs, the affected section's current limit trips, isolating it from the rail, and the other section keeps running. The supervisor then decides whether to retry the latched section or leave it off.

The detection side matters as much as the protection. A latch-up is a sudden, sustained current increase — not a transient. I'd use a current-sense amplifier with a comparator that distinguishes a fast transient (ignore) from a sustained overcurrent (trip). The trip threshold needs to be above the worst-case inrush and above the normal load step, but below the rail's collapse point. On the radiation side, the current-sense amplifier and the comparator themselves need to be tolerant of SETs — a transient on the sense signal could cause a false trip, so I'd add filtering and possibly a digital debounce in the supervisor.

**Possible follow-ups:**
- How would you set the latch-off threshold and the retry policy so that a legitimate load step doesn't trip the protection?
- If the analog front-end latches and you isolate it, how do you keep the digital section's control loop stable while the analog input is missing?

## Q4: You're reviewing a design where a junior engineer has proposed using a single commercial LDO with no radiation data to post-regulate a critical analog rail, arguing that the upstream DC-DC is already rad-tolerant so "the LDO doesn't matter." How would you evaluate this argument?

**Answer:** The argument has a kernel of truth — the upstream converter being rad-tolerant does remove some of the risk — but it misses the fact that the LDO is a separate silicon device with its own radiation response. The DC-DC being tolerant doesn't protect the LDO from TID-induced reference drift, SETs on its pass transistor, or SEL in its control loop. In fact, an LDO is often more exposed than a DC-DC because it's a linear pass element with no switching margin to hide behind — a drift in its reference directly translates to output voltage drift.

I'd walk through the specific failure modes. TID: the LDO's bandgap reference can drift with dose, and the error amplifier's offset can shift. Over a multi-year mission, that could push the analog rail out of the ADC's reference tolerance. SETs: a transient on the pass transistor's gate drive could cause a momentary output spike or droop — on a precision analog rail, that's a direct measurement error. SEL: if the LDO's process isn't latch-up immune, a heavy ion could latch it, and depending on the topology, that could either crowbar the rail or hold the output at a wrong voltage.

The right response isn't necessarily to reject the LDO — it's to ask what evidence exists. Has the manufacturer published TID data? Is there a similar part on a qualified process with known behavior? Can we test a sample at the mission dose? If none of that is available, I'd ask the engineer to either find a rad-tolerant alternative, or add mitigation: a downstream clamp to bound the output, a current limit to survive a latch, and a supervisory ADC channel to detect drift and flag it. The point is to make the risk explicit and decide it deliberately, not to assume the upstream part covers it.

**Possible follow-ups:**
- If the LDO has no radiation data but the analog rail has a calibration routine, does that change your assessment?
- How would you structure a low-cost test to bound the LDO's TID drift if the manufacturer won't provide data?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work — that deserves acknowledgment before any critique. I'd start by asking them to walk me through their reasoning: what failure modes they considered, what data they used, what assumptions they made. Often the gap isn't in their analysis but in a boundary condition they didn't know to consider — a radiation effect they haven't encountered, a derating rule they haven't applied, a test method they haven't seen. If I can surface that as a question rather than a correction, the conversation stays collaborative.

If the gap is real and the engineer pushes back, I'd move to evidence. Can we bound the risk with a test? Can we find published data on a similar part? Can we add a mitigation that's cheap enough to make the argument moot? The goal isn't to win the argument — it's to make the design safe. If the engineer's approach can be made safe with a small addition, that's often better than forcing a redesign, because it preserves their ownership and their momentum.

If the disagreement persists and the risk is genuinely unacceptable, I'd escalate the decision to the review board or the project lead, but I'd do it transparently — tell the engineer I'm doing it, explain why, and frame it as a risk-acceptance decision that's above both our pay grades. The worst outcome is a review that becomes adversarial and leaves the engineer disengaged. The second-worst is a design that ships with an unacknowledged risk. I'd rather have a slightly uncomfortable review that produces a safe design than a smooth one that doesn't.

**Possible follow-ups:**
- How would you handle it if the engineer's manager disagreed with your assessment and backed the engineer?
- What would you do if the under-margined design had already been built and tested, and rework would delay the schedule?