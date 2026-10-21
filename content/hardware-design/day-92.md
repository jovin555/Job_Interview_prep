# hardware-design — Day 92

## Q1: How would you approach selecting the feedback resistor values for a transimpedance amplifier front-end, and what trade-offs would drive the choice between a high-value and a low-value feedback resistor?

**Answer:** The transimpedance amplifier converts a photodiode's current into a voltage, with the transimpedance gain set primarily by the feedback resistor Rf (Vout ≈ Iin × Rf for an ideal op-amp). The choice of Rf is a multi-way trade-off, not a single calculation.

Start from the signal level: the required output swing divided by the expected photocurrent range gives a first-cut Rf. But then you have to check what that value does to bandwidth, noise, and stability.

**Bandwidth:** the closed-loop bandwidth of a TIA is approximately the op-amp's gain-bandwidth product divided by the noise gain, and the feedback capacitor Cf (stray plus intentional) forms a pole with Rf. A large Rf with a photodiode's junction capacitance at the inverting input creates a pole that can erode phase margin and cause peaking or oscillation. So a high Rf buys sensitivity but costs bandwidth and stability margin — you often need a Cf sized to compensate, which then limits bandwidth further.

**Noise:** the Johnson noise of Rf appears as a current noise of √(4kT/Rf), so a larger Rf actually *reduces* the resistor's own current-noise contribution — good for low-light measurements. But the op-amp's input voltage noise gets converted to current noise through the total input capacitance, and that term grows with source capacitance and with the feedback network impedance. So the noise optimum depends on whether the dominant term is the resistor's thermal noise or the op-amp's voltage noise shaped by the input capacitance.

**Offset and bias current:** a large Rf multiplies the op-amp's input bias current into a DC offset (Ib × Rf), which can saturate the output for a FET-input op-amp with even modest bias current. This often pushes you toward a CMOS or JFET input device when Rf is large.

**Practical limits:** very high Rf values (tens of MΩ) bring layout leakage, contamination sensitivity, and stray capacitance problems — the feedback node becomes a humidity and flux-residue sensor. Guarding, cleaning, and sometimes a T-network or a lower Rf with a second gain stage become preferable.

So my approach: size Rf from the required sensitivity, then check bandwidth against the photodiode capacitance, verify the noise budget term by term, confirm bias-current offset is acceptable, and only then pick the op-amp that can support that Rf with adequate phase margin. If the numbers don't close, consider a T-network to get high effective gain with a more moderate physical resistor, or split the gain across two stages.

**Possible follow-ups:** How would you compensate the TIA to guarantee stability across the full range of photodiode capacitance you might see in production? What layout precautions would you take around the inverting input node when Rf is very large?

## Q2: How would you approach choosing between a voltage-mode and a current-mode control architecture for a buck converter that must supply a fast-transient digital load while also feeding a sensitive analog rail through a downstream LDO?

**Answer:** The two architectures differ in what they sense and how they respond, and the presence of a downstream LDO changes the calculus.

**Current-mode control** senses the inductor current (directly or via the switch current) and uses it as the inner loop. Benefits: the inductor is effectively removed from the control loop, so the power stage behaves closer to a single-pole system, compensation is simpler, and cycle-by-cycle current limiting comes almost for free. Line feedforward is inherent — input voltage changes are corrected quickly. The downside is noise sensitivity on the current-sense signal, the need for slope compensation above 50% duty cycle to avoid subharmonic oscillation, and a minimum on-time that can limit duty-cycle range at high switching frequency.

**Voltage-mode control** uses only the output voltage error. It's quieter — no current-sense signal to pick up switching noise — and handles wide duty-cycle ranges and very low duty cycles more gracefully. But it has a double pole from the LC output filter, requiring a more elaborate Type III compensation network, and it responds to line transients more slowly because it has to wait for the output to move before correcting.

For a **fast-transient digital load**, current-mode's faster line response and simpler compensation are attractive, and the cycle-by-cycle current limit is a real safety benefit. The fast load steps are handled by the output capacitor and the inner current loop's quick reaction.

For the **sensitive analog rail through an LDO**, what matters most is the spectral content of the ripple the LDO has to reject. The LDO's PSRR rolls off with frequency, so switching ripple at the fundamental and its harmonics is only partially attenuated. Here the choice is less about control mode and more about switching frequency, ripple amplitude, and whether the LDO's PSRR at that frequency is adequate. Current-mode's tighter, more predictable ripple can actually be easier to filter, but the current-sense noise can couple into the output if not carefully laid out.

My approach: default to current-mode for the fast digital load because of transient response and built-in current limit, verify slope compensation and minimum on-time at the operating points, and then treat the analog rail as a separate problem — check the LDO's PSRR at the switching frequency, add an LC or ferrite post-filter if needed, and confirm the residual ripple meets the analog noise budget. If the duty cycle range is extreme or the current-sense noise proves hard to manage, voltage-mode with a well-designed Type III compensator is a legitimate alternative.

**Possible follow-ups:** How would you verify on the bench that the LDO is actually rejecting the switching ripple as the datasheet PSRR curve suggests? What would make you add a feed-forward capacitor across the upper feedback resistor, and what risk does it introduce?

## Q3: How would you approach debugging a circuit where a device works correctly on the bench but fails intermittently once it's installed in its enclosure, and the failure correlates with the device being handled or moved?

**Answer:** This is a classic intermittent-mechanical-coupling problem, and the correlation with handling is the most valuable clue — it points toward something that changes with physical state rather than a pure electrical design flaw.

First, I'd try to make the failure reproducible and observable. That means instrumenting the device so I can see what's happening when it fails: logging key rails, the fault output, and any error flags, and ideally capturing a trigger on the failure event. If the failure is a reset or a communication dropout, I'd set up a scope or logic analyzer with a trigger on the anomalous condition and then physically perturb the device — tap it, flex the enclosure, tilt it — to provoke the fault while capturing data.

Then I'd work through the likely mechanisms systematically:

- **Intermittent connections:** connector seating, board-to-board headers, flex cables, and press-fit or crimped terminals are prime suspects. Handling changes the mechanical stress on these. I'd check for partially seated connectors, damaged latch features, and cold or cracked solder joints — particularly on larger components, connectors, and anything with thermal mass that could have a marginal joint from reflow.
- **Mechanical stress on components:** a cracked MLCC, a flexed PCB stressing a BGA or QFN, or a component pressed against the enclosure can produce intermittent opens or shorts. Flexing the board while monitoring is a good test.
- **Grounding and shielding changes:** once enclosed, the device's grounding topology changes — the enclosure may become part of the ground path or an antenna. A shield that's only intermittently contacting the chassis ground can cause exactly this kind of handling-correlated fault. I'd check shield fingers, gaskets, and chassis-ground bonding points.
- **Clearance and creepage:** a wire or component that's fine on the bench but touches the enclosure or another net when the assembly is closed up.
- **Thermal or vibration secondary effects:** handling also changes temperature and vibration, so I'd separate "moved" from "warmed up" by testing each independently.

I'd also compare a known-good unit against a failing one under the same perturbation, and if possible use a bare board in the enclosure versus out, to isolate whether the enclosure itself is part of the mechanism.

The key discipline is to change one variable at a time and to keep the instrumentation in place until the mechanism is understood — chasing an intermittent fault by swapping parts without a captured signature tends to produce false fixes.

**Possible follow-ups:** How would you design a test fixture to reliably reproduce a handling-sensitive fault? If you suspect a cold solder joint but can't see it visually, what non-destructive techniques would you use to localize it?

## Q4: How would you approach selecting the input filter for a switching regulator, and how would you decide whether a simple capacitor is enough versus needing an LC or π-filter?

**Answer:** The input filter has two jobs: keep the regulator's switching current ripple from polluting the upstream supply and the rest of the board, and keep upstream noise from disturbing the regulator. How much filtering you need depends on the ripple current amplitude, the switching frequency, and — critically — the impedance the filter presents to the converter.

**Start with the ripple current.** A buck converter draws a pulsed current at the input, with amplitude roughly the load current during the on-time. That ripple flows through the input capacitor, and the resulting voltage ripple is the ripple current times the capacitor's impedance at the switching frequency. A single ceramic capacitor close to the switch node often handles this adequately if its ESR and ESL are low and it's placed tightly. So the first question is whether a well-placed input capacitor already meets the conducted-emission and ripple targets.

**When a capacitor isn't enough:** if the ripple voltage at the input is still too high, or if the concern is conducted EMI at the switching frequency and its harmonics, an LC filter adds attenuation that rolls off at 40 dB/decade above resonance. But an LC filter introduces a resonance of its own, and that resonance can interact badly with the converter's input impedance — the classic Middlebrook criterion concern. If the filter's output impedance peaks near the converter's input impedance, you can get instability or ringing. So an LC filter needs damping — a series resistor with the capacitor, or an electrolytic with useful ESR, or a damping network — and the resonant frequency should be placed well below the switching frequency but above the control loop bandwidth.

**π-filter** (capacitor–inductor–capacitor) gives more attenuation and better high-frequency performance because the second capacitor shunts high-frequency content that the inductor's parasitic capacitance would otherwise pass. It's the choice when you need strong attenuation across a broad band, but it costs board area and adds another resonant mode to damp.

**Ferrite bead versus inductor:** a ferrite bead is lossy at high frequency and can be a good choice for damping high-frequency content, but its impedance is nonlinear with DC bias current and it can saturate — so it's not a substitute for a real inductor when you need defined low-frequency attenuation.

My decision process: quantify the ripple current and the required attenuation at the switching frequency and its first few harmonics; check whether a single well-placed ceramic meets it; if not, design an LC with the resonance damped and placed appropriately relative to the loop bandwidth; go to a π-filter only if broadband attenuation is genuinely required. Then verify with a conducted-emissions measurement and a loop-stability check, because the filter changes the converter's input impedance and can affect stability.

**Possible follow-ups:** How would you damp an LC input filter without wasting too much DC power? What bench measurement would reveal that the input filter is interacting with the converter's control loop?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the software lead argues that the device's power-on self-test can be simplified by removing the hardware checks — rail monitors, reference checks — and relying on firmware to verify the system by reading the ADC and checking that values are in range. The software lead argues this reduces component count and board area. You believe the hardware checks are necessary because they verify the analog signal chain independently of the ADC and the firmware. How would you handle this disagreement?

**Answer:** I'd treat this as a question of what the self-test is *for*, and try to get the software lead and the rest of the review team aligned on that before debating component count.

The core issue is independence. A firmware-only self-test that reads the ADC and checks the values are in range cannot detect a fault in the ADC itself, in the reference, or in the firmware that's doing the checking. If the ADC is stuck at a plausible mid-scale value, or the reference has drifted, or the firmware is running with corrupted state, the check can pass while the signal chain is actually broken. That's the whole reason a self-test exists — to catch failures the normal signal path can't see. So the hardware checks aren't redundant with the firmware check; they cover a different failure space.

I'd frame it constructively rather than as "you're wrong." I'd ask: what failure modes are we trying to detect at power-on, and which of those can a firmware-only check actually catch? Then map each failure mode to the check that covers it. That usually makes the gap visible without anyone having to concede a point — the analysis does the work.

On the cost and board-area argument, I'd take it seriously. Rail monitors and reference checks can be small — a comparator or a supervisor IC, a couple of resistors — and the question is whether the area and cost are justified by the failure modes they cover. If the budget is genuinely tight, there may be a middle ground: keep the checks that cover the highest-severity failure modes (for example, verifying the reference against a second, independent reference, or a supervisor that holds the system in reset until rails are valid) and drop the ones that are truly redundant. That's a better outcome than an all-or-nothing argument.

I'd also bring it back to the regulatory and risk-management context: for a medical device, the self-test is part of the risk-control measures, and the justification for each check should trace to a hazard. If we remove a check, we need to show the residual risk is still acceptable — that's a documented decision, not a preference.

Finally, I'd propose a concrete way to settle it: build both versions on a bench, inject the failure modes we care about (stuck ADC, drifted reference, hung firmware), and see which checks catch them. Evidence tends to resolve these disagreements faster than debate, and it keeps the relationship constructive.

**Possible follow-ups:** If the team decides to keep only a subset of the hardware checks, how would you document the rationale so it holds up in a design history file review? How would you verify that the hardware self-test itself fails safe — that a failed check actually prevents the device from operating rather than just logging an error?