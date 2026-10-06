# hardware-design — Day 77

## Q1: How would you approach selecting a shunt resistor value and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?

**Answer:** I'd start by treating shunt value selection as a trade-off between signal amplitude and power dissipation, then pick the amplifier topology to match the common-mode conditions the shunt will actually see.

For the shunt: the sense voltage needs to be large enough that the amplifier's offset voltage and input-referred noise don't dominate the error budget, but small enough that I²R loss stays acceptable. At 1A full scale, a 100 mΩ shunt gives 100 mV full-scale sense voltage and dissipates 100 mW at full current — that's usually a reasonable starting point for a 1A load, though I'd check the thermal derating of the package and the temperature coefficient of the shunt material. A 10 mΩ shunt would dissipate only 10 mW but produce just 10 mV full scale, which makes a 1 mV offset already 10% of full scale — too much for a ±2% requirement unless I use a very low-offset amplifier. So the shunt value and the amplifier's offset spec have to be chosen together, not independently.

For topology: because the current is bidirectional and the shunt sits at some common-mode voltage relative to ground, I'd consider three options. A high-side shunt with a dedicated current-sense amplifier (or a difference amplifier built around a precision op-amp) keeps the shunt referenced to the supply rail, which is usually the safer place for a motor driver because a fault to ground on the load side doesn't corrupt the measurement. A low-side shunt is simpler and cheaper but breaks the ground reference of the motor, which can cause issues if the motor's return path is also used for anything else. For bidirectional sensing, I need an amplifier whose output can swing both above and below a mid-scale reference — either a current-sense amp with a VREF pin, or a difference amplifier with a level-shifting reference input.

For accuracy over temperature, I'd budget the error contributions: shunt tolerance and tempco, amplifier offset voltage and its drift, gain error and gain drift, and CMRR error from the common-mode voltage the shunt sees. If the common-mode voltage is large (say the shunt sits at 12V), CMRR becomes a first-order term — a 1% CMRR error at 12V common mode translates to a significant input-referred error. I'd pick an amplifier with CMRR specified over the full temperature range, not just at 25°C, and verify the offset drift spec is tight enough that the ±2% budget holds across 0–50°C or whatever the operating range is.

Finally, I'd lay out the shunt with a Kelvin (four-terminal) connection so the sense traces don't carry the load current, and route the sense pair as a tight differential pair back to the amplifier to reject magnetic pickup.

**Possible follow-ups:**
- How would you verify the CMRR of the current-sense amplifier on the bench, given that the common-mode voltage in your application is not a clean DC?
- If the motor driver uses PWM and the current has significant ripple, how would that affect your choice of amplifier bandwidth and your shunt layout?

## Q2: How would you approach designing a hardware-based power-on self-test for a medical device's analog signal chain, and what would you want it to verify independently of firmware?

**Answer:** The purpose of a hardware POST is to give the system a way to confirm that the analog signal chain is actually functional before trusting any measurement that comes out of it — and to do so in a way that doesn't depend on the same firmware and ADC path that the measurement itself relies on. If the only check is "read the ADC and see if the value is in range," a stuck ADC, a shorted input, or a dead reference can all produce plausible-looking in-range values.

I'd structure the POST around a few independent checks:

First, verify the reference. A precision voltage reference is the anchor of every ADC conversion, so I'd want a way to confirm it's within tolerance. One approach is to compare it against a second, independent reference — either a lower-grade but still specified reference, or a ratiometric check against a known divider off a different rail. If the two disagree beyond a threshold, the reference is suspect. This check should not go through the ADC if possible, or if it does, it should be cross-checked against a comparator with its own threshold.

Second, verify the signal chain gain and offset. I'd inject a known stimulus — either a precision voltage derived from the reference through a matched resistor divider, or a current injected into the front-end from a calibrated source — at a point in the chain where I can observe the response. By measuring the chain's output at two known input levels, I can confirm both offset and gain are within tolerance. The key is that the stimulus itself must be trustworthy, so it should be derived from the reference or from a separate calibrated source, not from the same DAC or PWM that the normal signal path uses.

Third, verify the ADC's own integrity. A common technique is to use a known test pattern or a built-in self-test mode if the ADC supports it, or to compare the ADC's reading of a known voltage against a comparator threshold. Some ADCs have a "test input" pin that can be switched to an internal reference or a known divider — that's ideal because it exercises the ADC's internal sampling network without relying on the external front-end.

Fourth, verify the power rails. Rail monitors — either comparators or supervisory ICs — should confirm each rail is within its specified window before the system allows measurements to be trusted. This is independent of the ADC and firmware.

The overall principle is redundancy and independence: each check should be able to fail on its own, and the failure should be detectable without relying on the subsystem being tested. The POST should also be designed so that a failure produces a safe state — the device either refuses to operate or flags the condition clearly — rather than silently producing measurements that look valid.

**Possible follow-ups:**
- How would you decide which checks are worth the board area and cost, versus which ones can be covered by a manufacturing test instead?
- If the POST runs at every power-on, how would you keep it from adding excessive startup time or wearing out any components?

## Q3: How would you approach debugging a circuit where a switching regulator's output is stable at room temperature but shows increased ripple and occasional dropout as the ambient temperature rises, even though the load current is unchanged?

**Answer:** Temperature-dependent behavior in a switching regulator usually points to a parameter that shifts with temperature — either in the regulator IC itself, in a passive component, or in the feedback network. I'd approach it systematically, starting with the components most likely to have strong temperature coefficients.

First, I'd characterize the failure more precisely. Is the ripple increasing gradually with temperature, or is there a threshold where it suddenly gets worse? Does the dropout correlate with a specific temperature, or is it gradual? Is the dropout a complete loss of regulation, or a momentary dip? I'd use a thermal chamber or a heat gun with a thermocouple to map the behavior against temperature, and I'd monitor both the output voltage and the switch node waveform to see what's actually changing.

Second, I'd look at the feedback network. If the feedback divider uses resistors with poor tempco — or if the divider is loading the reference in a way that shifts with temperature — the output voltage setpoint can drift. A drift in setpoint can push the regulator into a region where its loop gain or phase margin is different, which can manifest as increased ripple or instability. I'd check the divider resistors' tempco specs and consider whether a different resistor technology (thin-film vs thick-film) would be more stable.

Third, I'd look at the output capacitor. Many capacitor dielectrics — especially Class II ceramics like X5R and X7R — lose significant capacitance at temperature extremes, and their ESR can change as well. If the output cap's effective capacitance drops at high temperature, the ripple will increase and the loop compensation may no longer be adequate. I'd check the cap's temperature derating curve and consider whether the design margin was sufficient. If the cap is a tantalum or aluminum electrolytic, ESR typically increases at low temperature and can change at high temperature too — worth checking.

Fourth, I'd look at the inductor. Ferrite materials have temperature-dependent saturation behavior, and the inductor's DC resistance increases with temperature. If the inductor is operating near saturation at room temperature, it may saturate more easily at high temperature, causing ripple current to increase and the regulator to lose regulation intermittently. I'd check the inductor's saturation current rating at the maximum operating temperature, not just at 25°C.

Fifth, I'd look at the regulator IC itself. Some regulators have internal thermal shutdown or current-limit behavior that can engage at elevated temperatures even if the junction temperature is below the shutdown threshold. I'd check the IC's thermal derating and whether the dropout correlates with the IC's junction temperature rather than ambient. If the IC is in a package with poor thermal performance, or if the layout doesn't provide adequate copper for heat spreading, the junction temperature could be much higher than ambient.

Finally, I'd consider whether the issue is actually a loop stability problem that's temperature-dependent. The error amplifier's transconductance, the compensation network's component values, and the output capacitor's ESR all shift with temperature. If the phase margin was marginal at room temperature, it could become inadequate at high temperature. I'd measure the loop response — either with a network analyzer or by injecting a small signal and observing the transient response — at both temperature extremes to see if the margin is changing.

The debugging approach is to isolate which component or parameter is responsible by substitution or by measurement, rather than guessing. I'd start with the most likely candidates — output cap derating and inductor saturation — because they're common and easy to check.

**Possible follow-ups:**
- If you find that the output capacitor's derating is the root cause, how would you decide between changing the capacitor technology and changing the compensation network?
- How would you verify that the fix is robust across the full temperature range without running a full thermal chamber test for every unit?

## Q4: How would you approach selecting a crystal for a microcontroller that must maintain timing accuracy over a wide temperature range, and what would you verify on the bench?

**Answer:** Crystal selection for a wide-temperature application is really about matching the crystal's frequency stability, the oscillator circuit's load capacitance, and the microcontroller's internal oscillator requirements — and then verifying that the combination has adequate margin across the full temperature range.

The first decision is crystal type. A standard AT-cut crystal has a frequency-temperature curve that's roughly parabolic, with a turnover point that can be specified. For a wide temperature range, I'd look for a crystal whose turnover temperature is centered in the operating range, or I'd consider a TCXO or an OCXO if the accuracy requirement is tight enough that a plain crystal won't hold it. For most microcontroller applications, a plain crystal with a specified stability of ±20 to ±50 ppm over the temperature range is adequate, but I'd check the requirement first.

The second decision is load capacitance. The crystal's specified load capacitance (CL) must match the oscillator circuit's effective load capacitance, which is the series combination of the two load caps plus any stray capacitance. If the load capacitance is wrong, the crystal will oscillate at a frequency offset from its nominal, and the offset will vary with temperature because the crystal's motional parameters shift. I'd calculate the effective load capacitance from the schematic and layout, including stray capacitance, and choose the load caps to match the crystal's CL. I'd also check the crystal's pullability — how much the frequency shifts per pF of load capacitance error — because a high-pullability crystal will be more sensitive to layout and component tolerances.

The third decision is drive level. The crystal's drive level specification is the maximum power it can dissipate without damage or excessive aging. The oscillator circuit's drive level depends on the supply voltage, the feedback resistor, and the crystal's ESR. I'd check that the drive level is within the crystal's rating, with margin, and that it's not so low that the oscillator has marginal startup. Some microcontrollers have programmable drive strength, which helps match the drive level to the crystal.

The fourth decision is ESR and startup margin. The crystal's ESR must be within the oscillator's specified maximum ESR for reliable startup. I'd check the crystal's ESR at the temperature extremes, because ESR typically increases at low temperature. If the ESR is close to the oscillator's limit, startup may be unreliable at cold temperatures. I'd also check the negative resistance of the oscillator circuit — the margin between the oscillator's negative resistance and the crystal's ESR — and aim for a margin of at least 3× to 5× for reliable startup.

On the bench, I'd verify several things. First, I'd measure the actual oscillation frequency at room temperature and at the temperature extremes, using a frequency counter with adequate resolution. I'd compare the measured frequency against the crystal's specified tolerance and the load capacitance calculation. Second, I'd measure the startup time and verify that the oscillator starts reliably at the cold extreme, since that's where ESR is highest and startup margin is lowest. I'd do multiple startup trials — at least 10 or 20 — to catch marginal behavior. Third, I'd measure the drive level, either by measuring the voltage across the crystal and calculating power, or by using a current probe. Fourth, I'd check the oscillator's output waveform for adequate amplitude and clean edges, and verify that the microcontroller's clock input is within its specified range. Fifth, I'd check for frequency pulling from nearby signals or from the layout — a crystal is a high-impedance node and can be sensitive to capacitive coupling.

If the application requires tighter accuracy than a plain crystal can provide, I'd consider a TCXO, which includes temperature compensation and can hold ±2.5 ppm or better over a wide range. The trade-off is cost, board area, and power consumption.

**Possible follow-ups:**
- How would you measure the oscillator's negative resistance on the bench, and what margin would you consider adequate?
- If the crystal's ESR at cold temperature is marginal, what design changes would you consider to improve startup margin?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the reliability engineer argues that your chosen connector for the patient cable is not rated for the number of mating cycles the device will see over its lifetime, and proposes a more expensive, higher-cycle connector. You believe the current connector is adequate because the cable is intended to be connected once and left in place, but the reliability engineer is concerned about field replacement. How would you handle this disagreement?

**Answer:** This is a disagreement about assumptions, not just about component specs, so the first thing I'd do is make the assumptions explicit and see where they diverge.

The reliability engineer's concern is legitimate: if the connector is ever disconnected and reconnected in the field — for cleaning, for cable replacement, for troubleshooting — then the mating cycle count matters, and a connector rated for a low number of cycles could fail prematurely. My assumption was that the cable is connected once and left in place, but that assumption needs to be validated against the actual use case, not just my understanding of it.

I'd start by gathering the facts. What is the connector's actual mating cycle rating? What is the expected number of mating cycles over the device's lifetime, based on the use case and the maintenance plan? If the device is used in a hospital environment, the cable might be disconnected for cleaning or replacement more often than in a home environment. I'd check the use environment and the maintenance procedures, and I'd talk to the clinical or field service team if possible to understand how the device is actually used.

If the facts support my assumption — the connector is genuinely connected once and left in place, and the mating cycle count is well within the rating — then I'd present that evidence to the reliability engineer and ask whether there's a specific scenario they're concerned about that I haven't considered. If there is, we'd evaluate it together. If the facts don't support my assumption — if the connector is likely to be mated more often than I thought — then the reliability engineer is right and we need a higher-cycle connector, or we need to change the design or the maintenance procedure to reduce mating cycles.

If the disagreement persists, I'd escalate to a design review or a risk assessment. In a medical device context, this is exactly the kind of issue that should be captured in the risk management file — the probability and severity of a connector failure, and the mitigation. If the reliability engineer believes the risk is higher than I do, that's a risk management decision, not just an engineering preference. I'd want the decision documented, with the rationale, so that it's traceable and reviewable.

I'd also consider whether there's a middle ground. Maybe the current connector is adequate for the expected use, but a higher-cycle connector is available at a modest cost increase. If the cost difference is small relative to the risk reduction, it might be worth taking the more robust option even if the analysis says the current one is adequate — because the analysis is based on assumptions that could be wrong. On the other hand, if the cost difference is significant and the analysis is solid, I'd want to understand why the reliability engineer is concerned before agreeing to the change.

The key is to treat it as a shared problem — we both want the device to be reliable — rather than as a win-lose argument. I'd focus on the data and the use case, and I'd be willing to change my position if the evidence supports it.

**Possible follow-ups:**
- How would you document this decision in the design history file so that it's traceable if the connector ever becomes an issue in the field?
- If the reliability engineer's concern is based on a general principle rather than a specific scenario, how would you decide whether to accept the more expensive connector as a risk mitigation?