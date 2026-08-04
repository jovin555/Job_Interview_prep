# hardware-design — Day 14

## Q1: How would you approach designing a hardware-based fault detection and response scheme for a medical device that monitors a patient's physiological parameter, where the detection must be independent of the main application processor?

**Answer:** The key principle here is defense in depth — the fault detection should not rely on the same processor that might be failing. I'd structure this as a layered approach with a dedicated hardware supervisor path.

First, I'd identify which parameters need independent monitoring. For a physiological monitor, this typically includes: power supply rails (over/under-voltage), system clock integrity, and a "heartbeat" from the main processor. The detection circuitry should use a separate reference — not the same regulator or reference that feeds the main system, otherwise a common-mode failure defeats the purpose.

For voltage monitoring, I'd use dedicated supervisory ICs with precision internal references rather than a comparator fed from the main supply. These provide a clean, specified threshold with built-in hysteresis to prevent chatter. For processor health, a windowed watchdog timer is more robust than a simple timeout watchdog — it detects both "stuck" and "runaway" conditions (too slow *or* too fast), which matters because a processor executing out of control can still toggle a pin.

The response path is critical: the fault output should be a hard-wired, failsafe chain that can place the device into a safe state — for example, cutting power to a therapeutic output or activating an alarm — without requiring the main processor to execute any code. I'd use a latching mechanism so the safe state persists until explicitly cleared by an operator, not automatically reset, which could cause a repeated fault/reset cycle.

For a medical device, I'd also add a test mechanism — a way to inject a simulated fault during manufacturing or self-test to verify the detection path actually works. This is often required for compliance and is good engineering practice anyway.

**Possible follow-ups:** How would you prevent nuisance trips from normal transient conditions like inrush current? How would you design the fault output to be failsafe (i.e., fail in the safe direction)?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end exhibits a periodic, low-frequency disturbance (approximately 1–10 Hz) that appears on the output even when the input is disconnected and shorted to ground?

**Answer:** A low-frequency periodic disturbance with the input shorted points to something other than the signal path itself — I'd suspect thermal, mechanical, or reference-related effects before suspecting the amplifier.

My first step would be to characterize the disturbance precisely: measure its frequency, amplitude, and whether it's stable or drifting. I'd use a spectrum analyzer or FFT on a long time-domain capture to see if the frequency corresponds to anything identifiable — 1 Hz could be thermal cycling from a nearby power component, 10 Hz could be mechanical vibration or a switching regulator's low-frequency modulation.

Next, I'd check the obvious suspects systematically:
- **Reference voltage stability**: Is the reference drifting? A precision reference can exhibit low-frequency noise (flicker noise increases at low frequencies), but a *periodic* disturbance suggests something else — possibly the reference's output changing with temperature.
- **Thermal effects**: Use a thermal camera or probe to see if any component is cyclically heating and cooling. A nearby resistor dissipating power, or a regulator that bursts current, can create a thermal wave that shifts the amplifier's offset.
- **Mechanical/electromechanical**: If the board is near a fan, transformer, or any vibrating element, piezoelectric effects in ceramic capacitors can generate microvolt-level signals. This is a classic issue with high-impedance circuits and MLCCs.
- **Ground loops or reference bounce**: A periodic current draw elsewhere on the board (e.g., a radio transmitting, an LED blinking) can modulate the ground or power plane, which the amplifier's finite PSRR/CMRR converts to output.

I'd also check the amplifier's input bias current path — with the input shorted, the bias current still flows through the feedback network, and if the feedback resistor is large, thermal EMFs at junctions can create low-frequency drift.

The key debugging technique is isolation: power the amplifier from a clean bench supply, bypass the board's regulator, and see if the disturbance persists. If it disappears, the issue is upstream in the power path. Similarly, if the disturbance changes when I touch or gently tap the board, it's mechanical.

**Possible follow-ups:** What if the disturbance only appears when the device's wireless radio is transmitting? How would you distinguish between conducted and radiated coupling?

---

## Q3: How would you approach selecting the PCB stackup and layer assignment for a mixed-signal medical device that contains a high-resolution ADC, a switching power supply, and a wireless radio, given constraints on board thickness and cost?

**Answer:** The fundamental tension is between signal integrity, EMI control, and cost. For a medical device with a high-resolution ADC and a radio, I'd start from the premise that a dedicated, unbroken ground plane is non-negotiable — the question is how many layers and how to arrange them.

My default starting point would be a 6-layer stackup with this arrangement (top to bottom):
1. **Signal (components)** — analog and digital components placed with separation
2. **Ground** — continuous, unbroken
3. **Power** — split or with dedicated islands for analog and digital rails
4. **Signal (routing)** — orthogonal to top layer
5. **Ground** — second ground plane, providing shielding between the routing layer and bottom
6. **Signal (components)** — low-speed or less critical signals

The two ground planes provide a low-impedance return path and shield the signal layers from each other. The power layer sits between two grounds, which also provides some decoupling capacitance at high frequencies.

For layer assignment, I'd keep the ADC's analog inputs and reference on the top layer with the analog ground plane directly beneath. The switching regulator would be placed on the bottom layer, physically separated from the analog section, with its switching node kept short and its return current path directly under the switch. The radio section gets its own ground region, ideally with a slot or moat to isolate it from the analog ground, but connected at a single point to avoid ground loops.

The critical discipline is: **never route a signal across a split in the ground plane**. If the power plane must be split between analog and digital, any signal crossing the split needs a return path — either a bridge capacitor or a dedicated trace on an adjacent layer.

For cost constraints, I'd consider a 4-layer stackup as a fallback, but I'd first verify that the ADC's noise requirements can be met. The trade-off is usually: 4-layer with careful routing and more decoupling vs. 6-layer with cleaner separation. I'd prototype both if schedule allows, or use simulation to compare.

**Possible follow-ups:** How would you handle the ground connection between the analog and digital sections — single point or direct connection? How would you route the radio's antenna feed line through this stackup?

---

## Q4: How would you approach designing a hardware-based interlock system for a medical device that delivers a therapeutic output (e.g., a motor-driven actuator), where the interlock must prevent activation unless multiple independent conditions are met, and must fail safe?

**Answer:** The core design principle is that safety interlocks must be **independent, diverse, and failsafe** — they cannot share components, power supplies, or logic paths with the main control system, and their failure mode must be toward the safe state (output disabled).

I'd start by defining the interlock conditions. For a motor-driven actuator, these might be: (1) a physical limit switch confirms the actuator is in a safe position, (2) a pressure or force sensor confirms no obstruction, (3) an operator enable signal is present, and (4) the main processor is healthy (watchdog output). Each condition needs its own sensor and its own detection path.

For the logic, I'd use a hard-wired AND gate — either discrete logic (e.g., a 74HC-series AND gate) or a small CPLD — rather than implementing the interlock in the main processor's firmware. The processor can *request* activation, but the interlock logic independently verifies all conditions before enabling the motor driver's power or enable pin.

For failsafe operation, I'd design the interlock output to be **active-low** — the motor driver's enable pin is pulled low (disabled) by default, and the interlock logic must actively drive it high to enable. This way, any failure (loss of power, open wire, logic fault) results in the safe state. I'd also add a series element: the enable path should require both a logic signal and a power path that can be interrupted by a relay or MOSFET in series with the motor supply.

For diversity, I'd use different sensor technologies where possible — a mechanical limit switch and an optical sensor, for example — so a common-mode failure (e.g., both sensors being optical and both getting dirty) is less likely. The interlock logic should also be tested periodically: a self-test routine that injects a simulated fault and verifies the interlock responds correctly.

For a medical device, I'd also consider redundancy — two independent interlock channels with a voting scheme (e.g., 2-out-of-2 to enable, 1-out-of-2 to disable). This is more complex but may be required depending on the risk assessment.

**Possible follow-ups:** How would you test the interlock system to verify it fails safe under all fault conditions? How would you handle the trade-off between interlock complexity and device usability (e.g., nuisance trips)?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the manufacturing engineer argues that your chosen PCB surface finish (ENIG) is too expensive and proposes replacing it with HASL to reduce cost. You believe ENIG is necessary because the board includes a high-density BGA package and a high-resolution ADC that requires a flat, uniform surface for reliable solder joints and consistent electrical performance. How would you handle this disagreement?

**Answer:** I'd approach this as a data-driven engineering decision, not a matter of opinion or authority. The goal is to find the best solution for the product, considering both cost and technical requirements.

First, I'd acknowledge the manufacturing engineer's concern — cost is a legitimate constraint, and if HASL can meet the requirements, it's the right choice. I wouldn't dismiss the suggestion just because I specified ENIG initially.

Then I'd lay out the technical case for ENIG, grounded in specifics:
- **BGA reliability**: HASL produces an uneven surface (especially with lead-free HASL, which has a thicker, less uniform coating). For a fine-pitch BGA, this unevenness can cause solder joint voids or insufficient coplanarity, leading to intermittent connections that are extremely difficult to detect and diagnose in the field — a serious concern for a medical device.
- **ADC performance**: The high-resolution ADC's performance depends on consistent solder joint quality and minimal parasitic effects. ENIG's flat, uniform surface provides more consistent contact resistance and less variation across temperature.
- **Shelf life and handling**: ENIG has better corrosion resistance and a longer shelf life than HASL, which matters if boards are stored before assembly.

I'd also ask the manufacturing engineer to share their data — do they have yield data comparing ENIG vs. HASL on similar boards? What's the actual cost difference per board? If the cost difference is small relative to the risk of field failures, ENIG is clearly justified.

If the manufacturing engineer still disagrees, I'd propose a compromise: build a small test batch with HASL, subject it to the same qualification testing (thermal cycling, vibration, electrical test), and let the data decide. This is a fair, evidence-based approach that respects both perspectives. If HASL passes, we save money; if it fails, we have concrete evidence to justify ENIG.

The key is to keep the discussion focused on product requirements and data, not on who has the final say. In a medical device context, the risk assessment and design history file should document the decision and its rationale.

**Possible follow-ups:** What if the test batch with HASL passes all your qualification tests, but you still have concerns about long-term reliability? How would you weigh the cost savings against the unquantified risk? How would you document this decision in the design history file?