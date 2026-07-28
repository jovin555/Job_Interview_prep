# space-rad-hard — Day 7

## Q1: How would you approach designing a fault-tolerant power distribution architecture for a satellite payload that has multiple voltage rails (e.g., 3.3V, 1.8V, 1.2V) and must survive a single-event latch-up (SEL) on any single rail without losing the entire system?

**Answer:** I'd start by recognizing that SEL events can cause a low-impedance path that draws excessive current, potentially dragging down the entire power bus if not isolated. The architecture would use per-rail current limiting with active foldback or latching current limiters (e.g., radiation-hardened eFuses or PTCs with crowbar circuits) that trip before the rail voltage collapses. Each rail would have its own SEL detection circuit that monitors current and, upon detecting an overcurrent condition consistent with latch-up, either momentarily removes power to that rail (a "power cycle" of just that domain) or holds it off until a system-level reset clears the condition. The key is to ensure that the SEL on one rail doesn't propagate to other rails through shared ground returns or coupling — so I'd use separate return paths and star-point grounding, with each rail's return tied back to a common point at the power entry. The system controller (or a dedicated latch-up management CPLD) would log the event and attempt recovery: typically a brief power-off of the affected rail (100-500 ms) followed by re-enable. If the SEL persists after a few retries, the controller would permanently disable that rail and flag a fault. I'd also ensure that downstream loads on each rail can tolerate a brief power interruption — for example, using local decoupling capacitance to hold up logic states during the glitch, or designing the system so that only the affected subsystem resets while others continue operating.

**Possible follow-ups:** How would you size the current-limit threshold to distinguish between a normal transient (like an FPGA inrush) and a latch-up event? What if the SEL occurs on the same rail that powers the latch-up management controller itself?

---

## Q2: You are reviewing a design for a space-deployed system that uses a COTS FPGA with no radiation characterization. The design uses external configuration memory stored in a parallel NOR flash. How would you evaluate the risk of configuration bit upsets, and what mitigation strategies would you recommend beyond just using TMR on the FPGA fabric?

**Answer:** The risk here is multi-layered. First, the configuration memory (the NOR flash) itself can suffer SEUs, which could corrupt the bitstream loaded into the FPGA at power-up. Second, even if the flash is error-free at boot, the FPGA's configuration SRAM (if it's an SRAM-based FPGA) can accumulate upsets during operation. Third, the flash interface (address/data lines) can experience single-event transients that corrupt the loading process.

For evaluation, I'd start by estimating the upset rate for the flash part based on its process geometry and the mission orbit — using CREME96 or similar tools if the part's cell size is known, or bounding it with worst-case assumptions. I'd also look at whether the flash supports error correction internally (many NOR flashes have ECC for the memory array but not for the read path).

Mitigation strategies would include:
- **Configuration memory scrubbing:** Periodically read back the configuration bitstream from the FPGA and compare it to a golden copy stored in a radiation-hardened PROM or MRAM. If a mismatch is found, reconfigure the FPGA. This catches upsets in the configuration SRAM.
- **Redundant configuration storage:** Store two or three copies of the bitstream in the NOR flash with checksums, and use a majority vote at boot time. If the flash has sector-level ECC, verify that it's enabled and tested.
- **CRC on the bitstream:** Most FPGAs support CRC checking during configuration. Ensure this is enabled, and configure the FPGA to assert an error signal if the CRC fails, triggering a reconfiguration.
- **Triple-redundant configuration controller:** Use a rad-hard CPLD or a separate small rad-hard FPGA to manage the configuration process, so a single upset in the controller doesn't cause a corrupted load.
- **Watchdog on configuration time:** If configuration takes too long (indicating a stuck state), the watchdog forces a power cycle and retry.

I'd also consider whether the application can tolerate brief periods of reconfiguration (milliseconds to seconds) — if not, I'd recommend moving to a radiation-hardened FPGA with built-in configuration memory (like an antifuse or flash-based FPGA) rather than relying on external storage.

**Possible follow-ups:** How would you test that your scrubbing logic actually works under radiation? What if the golden copy itself gets corrupted — how do you protect against that?

---

## Q3: How would you approach designing a thermal management strategy for a high-power DC-DC converter (e.g., 50W output) in a vacuum environment where the only heat rejection path is conduction to a spacecraft chassis at 50°C, and the converter's junction temperature must stay below 125°C?

**Answer:** In vacuum, there's no convective cooling, so the design relies entirely on conduction and radiation. The first step is to minimize the heat generated at the source: select a converter topology with high efficiency (e.g., >90% at full load) to reduce the waste heat. For a 50W output at 90% efficiency, that's about 5.6W of heat to dissipate — manageable. At 85% efficiency, it's nearly 9W, which is significantly harder.

The thermal path would be: converter components (MOSFETs, magnetics, diodes) → PCB copper planes and thermal vias → baseplate or heat spreader → thermal interface material (TIM) → spacecraft chassis. I'd use a metal-core PCB or an aluminum baseplate bonded to the PCB with a thermally conductive adhesive, with the converter mounted directly on the baseplate. The baseplate would be bolted to the chassis with a high-conductivity TIM (e.g., graphite sheet or indium foil, not silicone grease which can outgas). The contact area should be maximized, and the bolt pattern designed to apply even pressure.

For the PCB itself, I'd use thick copper (2 oz or more) on the power layers, with arrays of thermal vias under hot components to conduct heat to the baseplate. The vias should be filled or tented to avoid outgassing issues. I'd also consider using a heat pipe embedded in the baseplate if the distance to the chassis is significant, though that adds complexity and qualification cost.

Radiation cooling is a secondary path — I'd use high-emissivity coatings (e.g., black anodize) on the converter's enclosure and any exposed surfaces to radiate heat to the spacecraft interior, but in most spacecraft, the interior is also warm, so this is less effective than conduction.

Finally, I'd derate the components: for a 125°C junction limit, I'd aim for a maximum junction temperature of 105-110°C under worst-case conditions, giving margin for aging and part-to-part variation. I'd run thermal simulations (FEA) to verify the path, and test in a thermal vacuum chamber with the converter mounted on a temperature-controlled plate at 50°C.

**Possible follow-ups:** How would you handle the thermal expansion mismatch between a ceramic substrate (e.g., AlN) and an aluminum baseplate? What if the chassis temperature could reach 70°C during peak solar loading?

---

## Q4: How would you approach selecting a radiation-hardened voltage reference for a precision ADC in a space application that must maintain accuracy within 0.1% over a 5-year mission, including the effects of TID and ELDRS (enhanced low-dose-rate sensitivity)?

**Answer:** The selection process would start with the mission requirements: the reference must maintain its initial accuracy (typically ±0.05% or better) plus drift over temperature, radiation, and time, all within the 0.1% budget. I'd first look at qualified parts on the QML Q or V lists, such as the ADRxx series or the LT1236 in rad-hard packages, which have characterized radiation performance.

Key parameters to evaluate:
- **Initial accuracy and temperature coefficient:** A tempco of 5 ppm/°C or better is typical; I'd calculate the drift over the mission temperature range (e.g., -20°C to +60°C) and ensure it's within budget.
- **TID tolerance:** The reference must survive the mission's total dose (e.g., 50 krad) without significant shift. Some references exhibit a "turnaround" effect where output voltage shifts one direction at low dose and reverses at high dose — I'd look for parts with published TID data showing less than 0.05% shift at the mission dose.
- **ELDRS:** Bipolar references are susceptible to enhanced degradation at low dose rates (space-like rates). I'd check if the part has been tested at low dose rate (typically 0.01 rad/s) or if it's a radiation-hardened design that mitigates ELDRS. If no low-dose-rate data exists, I'd apply a derating factor (e.g., 2x or 3x the high-dose-rate degradation) or choose a bandgap reference that is less susceptible.
- **Single-event effects:** Heavy-ion testing for SETs (single-event transients) on the reference output. A transient glitch on the reference could corrupt an ADC conversion. I'd look for parts with published SET data showing transient amplitude and duration, and ensure the ADC's sampling timing can tolerate or reject such transients (e.g., by averaging multiple samples or using a sample-and-hold that is insensitive to brief glitches).
- **Long-term stability:** Aging data (typically <50 ppm/1000 hours) to ensure the reference doesn't drift over 5 years.

If no fully qualified part exists, I'd consider a hybrid approach: use a rad-hard reference for the main ADC and a secondary COTS reference with radiation testing (at least TID and SET characterization) for a less critical channel. I'd also design the ADC circuit to be tolerant of reference drift — for example, using a ratiometric measurement where the reference drift cancels out, or periodically calibrating against an on-board precision source (like a Zener diode in a temperature-controlled oven).

**Possible follow-ups:** How would you design a test to characterize SETs on a voltage reference if no heavy-ion data is available? What if the reference's output drifts monotonically with TID — can you compensate for that in firmware?

---

## Q5: Imagine you are leading a team designing a radiation-hardened control board for a satellite payload. Midway through development, a junior engineer discovers that the rad-hard FPGA they selected has a known issue: under heavy-ion irradiation, the configuration logic can enter a state where it refuses to accept a new configuration bitstream until a full power cycle. The engineer proposes working around this by adding a watchdog that power-cycles the FPGA if configuration fails. How would you evaluate this proposal, and what additional considerations would you raise?

**Answer:** This is a good example of a practical engineering trade-off. The junior engineer's proposal is a reasonable first step — a watchdog that detects a configuration failure and power-cycles the FPGA is a standard mitigation for configuration lock-up. However, I'd want to evaluate several aspects before accepting it:

**First, understand the failure mode in detail:** Is the lock-up state guaranteed to be cleared by a power cycle, or could it persist? Some FPGAs have internal charge pumps or bias circuits that take time to discharge — a brief power cycle (e.g., 100 ms) might not fully reset the configuration logic. I'd ask the engineer to review the FPGA manufacturer's application note on this issue and determine the required power-off duration. If it's longer than a typical watchdog reset, the watchdog circuit needs to be designed accordingly.

**Second, consider the impact on the rest of the system:** A power cycle of the FPGA means all its internal state is lost — any ongoing operations, buffered data, or communication sessions would be interrupted. The system must be designed to tolerate this. For example, if the FPGA is controlling a motor or a heater, the power cycle could leave those actuators in an undefined state. I'd ask the engineer to map out what happens to every output during and after the power cycle, and ensure fail-safe states are enforced (e.g., pull-down resistors on critical outputs, or a separate supervisor that holds outputs in a safe state during FPGA reset).

**Third, evaluate the watchdog design itself:** The watchdog must be radiation-hardened or at least radiation-tolerant, because if the watchdog also suffers an upset, the mitigation fails. I'd recommend a dual watchdog approach: a primary watchdog implemented in a rad-hard CPLD or discrete timer, and a secondary watchdog (e.g., a separate RC-based timer) that triggers if the primary watchdog fails to reset. The watchdog should also monitor the FPGA's configuration done signal, not just a periodic "I'm alive" heartbeat — because the FPGA could be running but with corrupted configuration.

**Fourth, consider whether there's a better mitigation:** Some FPGAs allow partial reconfiguration or have a "reload from external memory" pin that doesn't require a full power cycle. If the FPGA supports this, it would be preferable because it's faster and doesn't disrupt other subsystems. I'd ask the engineer to investigate whether the configuration logic lock-up can be cleared by toggling the PROGRAM_B pin or by reasserting the configuration interface signals, rather than a full power cycle.

**Fifth, test the mitigation:** The watchdog and power-cycle circuit must be tested under radiation to ensure it actually works — the watchdog itself could be susceptible to SETs that cause false triggers or fail to trigger. I'd recommend including this in the radiation test plan.

Ultimately, I'd approve the proposal if the engineer can demonstrate that the power cycle reliably clears the lock-up, that the system can tolerate the interruption, and that the watchdog is robust against radiation. But I'd also push for exploring a partial-reconfiguration or PROGRAM_B-based solution as a more elegant alternative.

**Possible follow-ups:** How would you design the power switch for the FPGA to ensure it can be reliably turned off and on by the watchdog, given that the watchdog itself might be powered from the same rail? What if the FPGA's lock-up occurs during a critical maneuver where a power cycle could cause loss of mission data?