# space-rad-hard — Day 2

## Q1: What are the primary radiation effects that embedded systems designers must mitigate in space applications, and how do they influence component selection?

**Answer:** The three main radiation effects to consider are Total Ionizing Dose (TID), Single Event Effects (SEEs), and displacement damage. TID causes gradual degradation of semiconductor parameters (threshold voltage shifts, leakage current increases) over the mission lifetime. SEEs include Single Event Upsets (SEUs) where a charged particle flips a memory bit, Single Event Latchups (SELs) where a particle triggers a parasitic SCR structure causing a low-impedance path that can destroy the device, and Single Event Burnout (SEB) in power MOSFETs.

Component selection is driven by these effects. For TID, you select parts rated for the expected total dose — for example, in my work on the **5W High-Reliability EDFA** project, we required 50 kRad (Si) total dose tolerance, which meant using rad-hardened STM32 microcontrollers and external DAC/ADC components with guaranteed TID performance. For SEE mitigation, we avoid commercial-grade parts in critical paths, use radiation-tolerant FPGAs or microcontrollers with built-in error correction, and add external watchdog timers and current-limiting circuits to detect and recover from latchup events. Displacement damage is particularly relevant for optoelectronics and sensors, where lattice defects reduce charge collection efficiency over time.

**Possible follow-ups:**
- How would you test a design to verify it meets a 50 kRad TID requirement?
- What specific circuit techniques did you use in the EDFA project to protect against single-event latchup?

---

## Q2: In the 5W High-Reliability EDFA project, what specific design challenges did you face related to radiation hardening, and how did you address them?

**Answer:** The **5W High-Reliability EDFA** was a space-qualified booster module requiring 50 kRad radiation hardness. One major challenge was ensuring the STM32 microcontroller and external DAC/ADC chain maintained accuracy under radiation exposure. Radiation can cause ADC reference voltage drift and DAC output errors, which would directly affect the EDFA's pump laser current control and optical output stability.

We addressed this by implementing redundant measurement paths — using two independent ADC channels for critical parameters like laser temperature and drive current, with software voting logic to reject anomalous readings caused by SEUs. For the DAC, we used a radiation-tolerant external DAC with periodic recalibration cycles triggered by the STM32's internal watchdog timer. Another challenge was the hot-swap protection circuitry: we needed it to survive latchup events without damaging the power supply or the downstream laser driver. We designed the hot-swap controller with a fast-acting current limit that would trip within microseconds of detecting an overcurrent event, then auto-retry after a safe interval — this prevents permanent damage from latchup while allowing the system to recover if the event was transient.

**Possible follow-ups:**
- How did you validate that the redundant ADC voting scheme actually worked under radiation?
- What was the rationale for using an external DAC instead of the STM32's internal DAC?

---

## Q3: Explain the difference between radiation-hardened (rad-hard) and radiation-tolerant (rad-tolerant) design approaches. When would you choose one over the other?

**Answer:** Rad-hard components are specifically manufactured with process modifications (like silicon-on-insulator substrates, hardened oxide layers, or special doping profiles) to inherently resist radiation effects. They typically guarantee performance up to 100 kRad–1 MRad TID and have proven SEU/SEL immunity. Rad-tolerant approaches use commercial-off-the-shelf (COTS) components but apply system-level mitigation techniques — error correction codes, triple modular redundancy, watchdog timers, current limiting, and software-based fault detection.

You choose rad-hard when the mission demands guaranteed survival in high-radiation environments (e.g., deep-space probes, geostationary orbits passing through Van Allen belts, or nuclear environments). The trade-off is cost — rad-hard parts can be 10–100x more expensive and have lower performance than equivalent COTS parts. Rad-tolerant is suitable for low-earth orbit missions with shorter durations (2–5 years) where occasional bit flips are acceptable if the system can recover. In the **5W High-Reliability EDFA** project, we used a hybrid approach: the STM32 microcontroller was a rad-tolerant COTS part with system-level mitigation, while the power MOSFETs and optocouplers in the hot-swap circuit were fully rad-hardened because a failure there could cause catastrophic damage to the laser module.

**Possible follow-ups:**
- How would you decide which parts in a system need to be rad-hard versus rad-tolerant?
- Can you give an example of a system-level mitigation technique that worked well in practice?

---

## Q4: Describe a situation where you had to debug a radiation-related failure in a design. What was your approach, and what did you learn?

**Answer:** During testing of the **5W High-Reliability EDFA** prototype, we observed intermittent output power drops during radiation beam exposure at a test facility. The system would suddenly report a "laser current fault" and shut down the pump laser, then recover after a power cycle. This was a classic single-event upset signature — the fault was transient and cleared on reset.

My approach followed an 8D-style root-cause investigation (similar to what I used at Trudell Medical for medical device failures). First, we captured the fault logs from the STM32's UART output during testing, which showed the ADC reading for laser drive current had spiked to an out-of-range value just before shutdown. We then reviewed the schematic and identified that the ADC input pin had no external filtering — it was directly connected to the current sense resistor. The SEU had likely flipped a bit in the ADC's internal registers or corrupted the reading. Our corrective action was to add a simple RC low-pass filter (100 Ω, 10 nF) on the ADC input to suppress single-event transients, and we also implemented a software debounce: the firmware now requires three consecutive out-of-range readings (over 30 µs) before triggering a fault shutdown. After these changes, we re-ran the radiation test and the false fault rate dropped to zero over the same exposure duration. The key lesson was that even simple passive filtering can be highly effective against SEUs when combined with software-based validation.

**Possible follow-ups:**
- Why did you choose an RC filter instead of a more complex solution like a Schmitt trigger?
- How did you determine the 30 µs debounce window was appropriate?

---

## Q5: Behavioral — Walk me through a time when you had to balance radiation-hardening requirements against cost or schedule constraints on a project. How did you make the trade-off decisions?

**Answer:** On the **5W High-Reliability EDFA** project, we had a tight budget and schedule, but the customer required 50 kRad TID tolerance. Initially, the team proposed using fully rad-hardened components for every part — which would have blown the budget by roughly 40% and added 12-week lead times for some specialized parts.

I led a trade-off analysis where we categorized every component by its criticality to mission success and its failure mode under radiation. For example, the STM32 microcontroller — if it experienced an SEU, the system could recover via watchdog reset, so we could use a rad-tolerant COTS part with software mitigation. But the pump laser diode — if its driver MOSFET suffered single-event burnout, the laser would be destroyed permanently, so that MOSFET had to be rad-hardened. We also identified that the EEPROM storing calibration data needed to be rad-hard to prevent corruption of critical parameters.

I presented this tiered approach to the customer with a risk matrix: we'd save 30% on BOM cost and reduce lead time by 8 weeks by using rad-tolerant parts for non-critical functions, while maintaining full rad-hard protection for the laser driver, power management, and calibration memory. The customer accepted the proposal after we demonstrated that the system could survive and recover from SEUs in the STM32 through our watchdog and error-correction firmware. The project delivered on schedule and within budget, and the final qualification testing passed all radiation requirements. This experience taught me that radiation hardening isn't binary — it's about intelligent risk allocation based on failure criticality.

**Possible follow-ups:**
- How did you convince the customer that the STM32's software mitigation was reliable enough?
- What would you have done differently if the customer had insisted on fully rad-hard components?