# hardware-design — Day 40

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end and a motor driver, where the motor can draw 1A peaks and the analog section requires a noise floor below 50 µV RMS?

**Answer:** The fundamental challenge here is that you have two loads with directly conflicting requirements: the motor needs high instantaneous current with fast transients, while the analog front-end needs a clean, low-noise supply. I would not try to power both from the same rail without careful separation.

My approach would be a two-tier architecture. First, a main power stage — likely a buck converter — that efficiently converts the battery or input voltage down to an intermediate rail (e.g., 5V or 3.3V) with enough headroom for both loads. This stage handles the bulk power conversion and the motor's current demands. Then, for the analog section, I would add a secondary low-noise LDO powered from that intermediate rail, providing a dedicated, clean supply for the sensitive circuitry.

The key design decisions are: (1) the LDO's PSRR must be adequate at the buck converter's switching frequency and its harmonics — many LDOs have excellent PSRR at DC but degrade significantly above 100 kHz, so I'd check the PSRR curve specifically at the switching frequency; (2) the LDO's output noise density must be low enough across the analog bandwidth of interest; (3) the intermediate rail needs enough bulk capacitance to handle the motor's current transients without drooping below the LDO's dropout voltage — otherwise the LDO output will dip and couple noise into the analog section.

For the motor itself, I would also consider whether it needs its own dedicated supply path or if it can share the intermediate rail with proper decoupling. If the motor current transients are severe, a separate battery tap or a dedicated buck stage for the motor might be warranted. The PCB layout is equally critical: the motor's high-current return path must be separated from the analog ground, ideally with a star-point grounding scheme or a solid ground plane with careful partitioning, so that motor currents don't flow through the analog ground reference.

**Possible follow-ups:**
- How would you determine whether the LDO's PSRR is sufficient, and what happens if it isn't?
- How would you size the bulk capacitance on the intermediate rail to handle the motor's current transients?

---

## Q2: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** A low-frequency periodic disturbance that persists with the input shorted and scales with supply voltage points to something in the power path or the reference path, not the signal path itself. The first thing I'd do is confirm the disturbance is truly periodic and measure its exact frequency — is it fixed, or does it drift? That tells me whether it's a self-generated oscillation or something coupled in from elsewhere.

Next, I'd look at the power supply with a scope in AC-coupled mode, using a low-inductance probe tip, to see if there's a corresponding ripple on the supply rail at the same frequency. If the disturbance appears on the supply, I'd trace it backward: is it coming from the input supply, a switching regulator, or a load elsewhere on the board that's cycling at that rate? A 1–10 Hz period is suspiciously slow — it could be a thermal loop (a regulator or component heating up and cooling down), a battery fuel gauge or monitoring circuit cycling, or even a firmware-driven load that turns on and off periodically.

If the supply looks clean, I'd check the voltage reference. Many precision references have poor load regulation at very low frequencies, or they can oscillate when driving certain capacitive loads. I'd measure the reference output directly with the scope in AC mode. I'd also check the reference's bypass capacitor — an incorrectly sized bypass cap can cause low-frequency instability in some reference ICs.

Another possibility is ground bounce or a ground loop: if there's a low-frequency current flowing through the ground plane (perhaps from a heater, a motor, or a battery charger), it will create a small voltage gradient that appears at the amplifier's output. I'd check the voltage between the analog ground at the front-end and the ground at the power supply entry point.

Finally, I'd consider thermoelectric effects — if there's a temperature gradient across the board, a thermocouple junction at a solder joint or connector can generate a small DC offset that drifts with temperature. This is rare but worth checking if the disturbance frequency matches a thermal time constant.

**Possible follow-ups:**
- How would you distinguish between a power supply issue and a reference issue in this scenario?
- What test equipment would you use to confirm the disturbance is coming from the ground path?

---

## Q3: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor is one of the most critical components in a boost converter because it directly affects efficiency, output ripple, transient response, and the converter's ability to deliver current at the minimum input voltage. I'd start by calculating the required inductance based on the converter's switching frequency and the desired ripple current.

The key parameters are: (1) inductance value, (2) saturation current rating, (3) DC resistance (DCR), and (4) self-resonant frequency (SRF). For the inductance value, I'd target a ripple current of 20–40% of the average input current. At the worst-case condition — minimum input voltage (3.0V) and maximum load (500mA) — the input current will be roughly 5V × 0.5A / (3.0V × efficiency), which is around 0.9–1.0A. So I'd target a ripple current of roughly 200–400 mA peak-to-peak.

The saturation current rating is critical: the inductor must not saturate at the peak current, which is the average input current plus half the ripple current. I'd derate this by at least 20–30% to account for temperature — inductor saturation current decreases as temperature rises. A common mistake is selecting an inductor with a saturation current rating that's only marginally above the calculated peak, which works at room temperature but fails at elevated temperatures.

For DCR, I'd look for the lowest resistance that fits the size constraint, since DCR directly impacts efficiency and causes self-heating. The trade-off is that lower DCR typically means a larger inductor. I'd also check the SRF — the inductor's self-resonant frequency should be well above the switching frequency, typically at least 10× higher, to avoid parasitic capacitance effects.

For the fast current transients, I'd also consider the inductor's core material. Ferrite cores have low losses but can saturate abruptly; powdered iron or composite cores saturate more gracefully. If the load transients are very fast, I might also need to check the inductor's high-frequency behavior — some inductors have significant impedance increase at high frequencies due to winding capacitance, which can affect transient response.

Finally, I'd verify the inductor's temperature rise at maximum load and ensure it stays within the component's rating, and I'd check the recommended layout from the inductor manufacturer — the copper pour and via placement around the inductor can significantly affect its performance.

**Possible follow-ups:**
- How would you calculate the peak current the inductor will see, and how would you derate for temperature?
- What would you check if the boost converter's efficiency is lower than expected at light load?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** A latch circuit for a medical device fault condition needs to satisfy two conflicting requirements: it must be persistent (once triggered, it stays in the fault state even if the triggering condition clears), and it must be resettable only through a deliberate action that ensures the system is safe to restart.

The classic approach is a silicon-controlled rectifier (SCR) or a thyristor-based crowbar, but for a logic-level fault latch, I'd typically use a comparator with positive feedback (hysteresis) or a discrete transistor latch. The comparator approach is cleaner: the comparator's output feeds back to its non-inverting input through a resistor divider, creating a latching action. Once the input crosses the threshold, the output goes high (or low), and the feedback holds it in that state even if the input returns to normal.

The reset mechanism is the critical safety design decision. I would not allow the latch to reset automatically when the fault clears — that could cause the system to cycle on and off repeatedly, which is dangerous in a medical device. Instead, I'd require a deliberate reset action, which could be: (1) a manual reset button that must be physically pressed, (2) a reset signal from a supervisory processor that has verified the fault condition is resolved, or (3) a power-cycle reset where the device must be fully powered down and restarted.

For a medical device, I'd lean toward option (2) or (3), because a manual button can be accidentally pressed, and the system should verify safety before restarting. The reset path should also be designed so that it can't be triggered by noise or a transient — I'd add a debounce or a minimum reset pulse width requirement.

I'd also consider the latch's behavior during power-up. The latch should default to a safe state (fault asserted) when power is first applied, and only clear when a deliberate reset is performed. This requires careful attention to the comparator's power-up behavior — some comparators have undefined outputs during power-up, which could cause the latch to be in the wrong state. I'd add a pull-up or pull-down resistor to define the default state, and possibly a small RC delay to ensure the supply is stable before the latch is enabled.

Finally, I'd add a test point or a status output so the fault state can be observed during manufacturing test and field service, and I'd document the reset procedure clearly in the operator's manual.

**Possible follow-ups:**
- How would you ensure the latch defaults to a safe state during power-up?
- What are the trade-offs between a comparator-based latch and a discrete transistor latch?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a classic safety-critical design disagreement, and my approach would be to focus on the engineering evidence rather than asserting authority. The core question is not whether firmware *can* do the job, but whether it can do the job *reliably under all fault conditions* — and that's a question we can analyze together.

First, I'd acknowledge the firmware lead's valid points: firmware-based protection does save board space and cost, and it does allow more flexible threshold adjustment. Those are real benefits, and I'd want to make sure we're not dismissing them without proper consideration.

Then, I'd reframe the discussion around the safety requirements. The key question is: what happens if the firmware hangs, the ADC fails, or the GPIO is stuck? In a medical device, the protection circuit must be independent of the main processor — this is a fundamental principle of safety-critical design. I'd ask the firmware lead to walk through the failure modes: if the firmware is stuck in an infinite loop, the ADC is reading a wrong value, or the GPIO is latched high, does the protection still work? In most cases, the answer is no.

I'd also bring up the regulatory perspective. For IEC 60601 compliance, the safety mechanism typically needs to be verifiable and testable. A hardware comparator and latch can be tested in isolation — you can apply a fault condition and verify the response. A firmware-based solution requires testing the entire software stack, including the RTOS, the ADC driver, and the application code, and you need to demonstrate that the protection works even when other parts of the system are failing.

Rather than just saying "no," I'd propose a compromise: we could keep the hardware comparator as the primary protection, but use the firmware-based monitoring as a secondary, complementary layer that provides additional diagnostics and more flexible threshold adjustment. This gives the firmware lead the flexibility they want while maintaining the safety-critical independence.

If the firmware lead still disagrees, I'd suggest we do a formal risk analysis together — a mini-FMEA or a fault tree analysis — to document the failure modes and their mitigations. This takes the disagreement out of the realm of opinion and puts it into a structured engineering framework. If we still can't agree, I'd escalate to the project manager or the safety officer, presenting both options with their respective risks and benefits, and let the appropriate authority make the decision based on the full picture.

The key is to keep the discussion collaborative and evidence-based, not adversarial. The goal is the safest, most reliable device, and both of us want that — we just have different perspectives on how to achieve it.

**Possible follow-ups:**
- How would you handle the situation if the firmware lead refuses to accept your analysis and the disagreement escalates?
- What specific failure modes would you document in the risk analysis to support your position?