# high-speed-digital-fpga — Day 99

## Q1: How would you approach designing the clock domain crossing for a multi-bit control word that is written by a slow serial interface (e.g., 10 MHz SPI) and consumed by a fast logic domain (e.g., 250 MHz), where the word changes infrequently but must never be observed in a partially updated state?

**Answer:** The key insight is that this is a *coherency* problem, not a *throughput* problem — the word changes rarely, so latency is irrelevant, but a torn read (some bits from the old value, some from the new) is unacceptable. The cleanest approach is a handshake-based register: the SPI domain writes the new word into a holding register, then asserts a single-bit "valid" toggle. That toggle is the only signal that crosses domains, and it crosses through a two-flop synchronizer (or a toggle-based pulse synchronizer, since a level signal held for many fast-domain cycles is fine here). The fast domain detects the toggle edge, then captures the entire multi-bit word in one clocked operation — because the data has been stable since well before the toggle was asserted, and will remain stable until the next update, there is no metastability risk on the data bits themselves. The fast domain then acknowledges back with its own toggle, which the SPI domain synchronizes before it is allowed to write the next value. This gives a fully coherent, lossless transfer with no dependence on clock frequency ratios.

Alternatives worth mentioning: a dual-clock FIFO if updates were frequent (overkill here), or Gray coding if the value were a counter (not applicable to an arbitrary control word). I'd also add an assertion in the fast domain that flags if the data bus changes while the valid toggle is not transitioning — that catches a designer who later "optimizes" by writing the data register directly from the SPI clock.

**Possible follow-ups:**
- What happens if the SPI domain writes a new value before the fast domain has acknowledged the previous one — how do you prevent that, and what's the trade-off versus allowing overwrite?
- How would your answer change if the control word were 128 bits wide and updated every few microseconds?

## Q2: How would you approach debugging an FPGA design where the timing analysis reports that all constraints are met, but the design fails in hardware only when the device is operated at the maximum specified junction temperature?

**Answer:** A clean timing report at max junction temperature that still fails in hardware points to something the static timing analysis (STA) model doesn't capture. I'd work through the possibilities systematically. First, confirm the STA was actually run at the worst-case corner for the *actual* junction temperature — many flows default to a commercial-grade corner, and if the part is industrial or the board runs hot, the derating may be insufficient. Second, check whether the failing behavior correlates with a specific interface rather than internal logic: at high temperature, I/O timing budgets shift (driver strength and receiver thresholds drift), so a source-synchronous interface with marginal setup/hold margin can fail even though the internal fabric timing is clean. Third, look at clocking — PLL lock range, jitter, and duty cycle all degrade with temperature, and a clock that's marginal at 25 °C can push a path over the edge at 85 °C or beyond. Fourth, consider power integrity: leakage current rises steeply with temperature, so the core rail may droop more at hot, and a marginal PDN can cause functional failures that look like timing.

My debugging sequence would be: reproduce with a controlled thermal chamber and a known-good board, then instrument with an on-chip logic analyzer or a debug core to see *which* signal fails first. If it's an interface, I'd sweep the I/O delay taps (IDELAY/ODELAY) at temperature to see if the eye has closed. If it's internal, I'd re-run STA with the correct thermal derating and look for paths with small positive slack that could flip sign under a more accurate model. The fix is usually either tightening the constraint corner, adding margin to the interface timing, or improving the thermal/PDN design — but the diagnosis has to come before the fix.

**Possible follow-ups:**
- How would you distinguish a genuine silicon timing failure from a board-level thermal issue (e.g., a connector or solder joint) using only lab equipment?
- What would you change in the design flow to catch this class of failure before first silicon?

## Q3: How would you approach mitigating via stub effects on a high-speed serial channel that must transition between the top and bottom layers of a thick backplane?

**Answer:** A via that passes through a thick backplane but is only used to connect two inner layers leaves an unused portion — the stub — that acts as an open-circuited transmission line. At multi-gigabit rates, that stub resonates and creates a notch in the channel's insertion loss that can close the eye at the resonant frequency. The mitigation options, roughly in order of preference:

1. **Back-drilling** — drill out the unused stub after plating, leaving only a short residual. This is the most effective and is standard practice for thick backplanes at high data rates. The residual stub length is a manufacturing tolerance you have to budget for.
2. **Blind/buried vias** — if the stack-up allows, use vias that only span the layers they need to connect, eliminating the stub entirely. More expensive fabrication, but the cleanest result.
3. **Via-in-pad with filled and capped vias** — helps with routing density and can reduce stub length if the via is placed to minimize the unused portion.
4. **Counter-drilling / controlled-depth drilling** — a variant of back-drilling that removes the stub from the opposite side.
5. **Active or passive equalization** — if the stub can't be eliminated, pre-emphasis/CTLE/DFE in the transceiver can compensate for the notch, but this burns margin and should be a last resort.

I'd model the channel in a 3D field solver (or use the fab's via model) with the actual stack-up and stub length, then run a channel simulation with the transceiver's IBIS-AMI model to confirm the eye is acceptable across corners. The decision between back-drilling and blind vias is a cost/yield trade-off that should be made with the fab early, because it constrains the stack-up.

**Possible follow-ups:**
- How would you budget the residual stub length after back-drilling, and what's the relationship between stub length and the frequency of the first resonance?
- If back-drilling isn't available from your fab, what routing or stack-up changes would you consider to reduce the stub's impact?

## Q4: How would you approach designing a spread-spectrum clocking scheme for a high-speed digital board where several clock sources (processor, FPGA, and a high-speed serial reference) must coexist, and you need to reduce radiated emissions without breaking the serial links?

**Answer:** Spread-spectrum clocking (SSC) reduces peak radiated emissions by modulating the clock frequency slowly (typically 30–33 kHz modulation, down-spread of 0.5–1.5%), which smears the energy across a band instead of concentrating it at the fundamental and its harmonics. The challenge on a mixed board is that SSC is only safe where *both* ends of a link track the same modulation — otherwise the frequency offset between transmitter and receiver eats into the link's margin.

My approach: first, identify which clock domains are self-contained (e.g., the processor's internal clocks, or an FPGA fabric clock that doesn't cross a synchronous interface) — those can be spread freely. Second, for any interface between two devices, either both sides must be driven from the same SSC source (common in PCIe, where the reference clock is distributed with SSC and both endpoints track it), or the interface must be asynchronous and tolerant of the frequency offset. A high-speed serial link with a CDR-based receiver can usually tolerate SSC if the modulation is within the standard's spec, but the receiver's CDR must have enough tracking bandwidth — I'd verify against the transceiver's jitter tolerance spec and run a channel sim with the SSC profile included. Third, for the FPGA's own reference clocks, I'd check whether the PLL/MMCM can track the modulation without losing lock or adding excessive jitter; some PLL configurations have limited tracking range.

The practical layout: spread the clocks that don't cross a synchronous boundary, keep the serial reference clean or use a standard-compliant SSC profile, and verify emissions with a near-field scan before the EMC chamber run. If a link breaks under SSC, the fix is usually to narrow the modulation depth or move the modulation frequency, not to abandon SSC entirely.

**Possible follow-ups:**
- How would you verify that a transceiver's CDR can track a given SSC profile before committing to the design?
- What's the trade-off between down-spread and center-spread modulation, and when would you choose one over the other?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer presents a timing closure report showing all constraints met, but you notice the report was generated with a set of timing exceptions (false paths and multicycle paths) that the engineer added to make the design close. The engineer argues that the exceptions are legitimate because "those paths don't need to meet single-cycle timing." How do you handle this situation?

**Answer:** I'd treat this as a review-quality issue first and a teaching moment second, not as an accusation. The engineer may well be right that some paths are genuinely multicycle or false — but the burden of proof is on the exception, and a timing report that only closes because of exceptions is not evidence of correctness until each exception is justified.

My approach in the review: ask the engineer to walk through each exception one at a time and explain *why* the path is exempt — what's the architectural reason, and what analysis or simulation demonstrates it. For a multicycle path, the justification is that the destination only samples every N cycles and the data is stable for that window; for a false path, it's that the path is structurally never sensitized (e.g., a test-only path, or a configuration that's mutually exclusive). I'd want to see that the exception is documented in the constraint file with a comment, and ideally that there's a corresponding assertion or coverage in simulation that would catch a future change that invalidates the assumption.

If an exception can't be justified, it comes out and the design has to close honestly — which may mean pipelining, retiming, or accepting a lower clock. If it can be justified, I'd still want the exceptions reviewed by a second pair of eyes, because a wrong false path is one of the most dangerous classes of bug: it produces a design that passes STA and fails in the field, often intermittently. I'd also make the point that the goal of the review isn't to "make timing close" — it's to make the design correct, and the report is a means to that end, not the end itself. Framing it that way keeps the conversation collaborative rather than adversarial.

**Possible follow-ups:**
- How would you structure a constraint-review checklist so that timing exceptions get the same scrutiny as the rest of the design?
- What would you do if the engineer pushed back and insisted the exceptions were fine, and you weren't fully convinced either way?