# debugging-failure-analysis — Day 2

## Q1: How would you approach debugging an intermittent failure in a battery-powered medical sensor device that only occurs after several hours of continuous operation?

**Answer:** Intermittent failures that appear only after extended operation typically point to thermal effects, power supply drift, or cumulative software state issues. I would start by instrumenting the device to log key parameters over the full operating window: supply voltage at multiple points, temperature at critical components (especially the battery charger, regulator, and sensor), and firmware state transitions. If possible, I'd add a real-time clock timestamp to correlate the failure with logged data.

Next, I'd try to accelerate the failure in a controlled way — for example, using a thermal chamber to cycle temperature or a programmable load to simulate battery discharge profiles. This helps determine whether the failure is temperature-dependent, voltage-dependent, or purely time-dependent. If the failure is thermal, I'd examine the PCB layout for hot spots using a thermal camera and check component derating at elevated temperatures. If it's voltage-related, I'd look at the battery discharge curve and regulator dropout margins. For software state issues, I'd review state machine transitions and watchdog timer behavior, particularly around low-power mode entry/exit sequences.

**Possible follow-ups:** How would you distinguish between a hardware and a software root cause for an intermittent failure? What debugging tools would you bring to the field if the device is already deployed with patients?

---

## Q2: Walk me through your approach to a root-cause investigation when a medical device fails during IEC 60601 electrical safety testing — specifically, a higher-than-expected leakage current measurement.

**Answer:** First, I'd verify the test setup and measurement methodology, because leakage current testing is sensitive to test equipment calibration, grounding configuration, and measurement point selection. I'd confirm the test was performed per the applicable standard (IEC 60601-1 Table 4 or 6, depending on the device class) and that the measuring device (MD) was properly calibrated.

Assuming the setup is correct, I'd isolate the leakage path systematically. I'd start by disconnecting non-essential subsystems to see if the leakage originates from the power supply, the isolated communication interface, or the patient-connected circuitry. For medical devices, the primary suspects are often the mains isolation transformer, Y-capacitors between primary and secondary, or the optocoupler/capacitive isolation barrier on communication lines. I'd measure the impedance of each isolation barrier and check for component damage or contamination that could create a conductive path.

If the leakage is capacitive rather than resistive, I'd review the Y-capacitor values against the standard's limits and consider whether the PCB layout has adequate creepage and clearance distances. I'd also check for moisture or flux residue that could reduce surface insulation resistance. The investigation would follow a structured 8D or similar methodology, documenting each hypothesis and test result to build a clear cause-and-effect chain.

**Possible follow-ups:** What would you do if the leakage current passes at room temperature but fails after a humidity preconditioning cycle? How would you redesign the isolation barrier to reduce leakage without compromising signal integrity?

---

## Q3: How would you debug a UART communication issue where a medical device intermittently loses data packets when connected to a host system, but works perfectly when tested with a USB-to-serial adapter on the bench?

**Answer:** This discrepancy between bench and system behavior strongly suggests a timing, grounding, or electrical interface mismatch. I'd start by comparing the electrical characteristics of both connections — specifically, the signal levels, slew rates, and grounding topology. The bench setup likely has a short cable and shared ground, while the host system may have a longer cable, different ground potential, or additional noise sources.

I'd use an oscilloscope to capture the UART signals at the device's connector under both conditions, looking for: excessive ringing or overshoot (indicating impedance mismatch), slow rise/fall times (capacitive loading from longer cables), or ground bounce (voltage difference between device ground and host ground). If the ground potential differs, I'd check whether the design uses galvanic isolation on the UART — for medical devices, this is often required for patient safety.

If the issue is ground-related, I'd recommend adding isolation (digital isolators or optocouplers) or ensuring a low-impedance ground path. If it's signal integrity, I'd adjust drive strength, add series termination resistors, or reduce baud rate. I'd also verify that both sides agree on parity, stop bits, and flow control settings — sometimes the host system uses hardware flow control that the bench adapter ignores.

**Possible follow-ups:** How would you implement a software-based robustness mechanism to recover from lost packets without requiring hardware changes? What baud rate would you choose for a medical device that must communicate reliably over a 3-meter cable in a noisy hospital environment?

---

## Q4: Describe how you would structure a failure analysis when a newly assembled batch of PCBs shows a 5% failure rate on the production test fixture, with the failures all exhibiting the same symptom — a specific sensor reading is consistently out of specification.

**Answer:** I'd approach this as a systematic 8D or DMAIC investigation. First, I'd contain the issue by quarantining the affected batch and verifying that the test fixture itself isn't the source — I'd run known-good boards from a previous batch through the same fixture to confirm it's not a calibration drift or test program error.

Next, I'd perform a detailed comparison between failed and passing units. I'd start with visual inspection under a microscope, looking for solder defects, component orientation, or damage around the sensor circuit. I'd then measure key voltages and signals on both populations — sensor supply voltage, reference voltage, output signal levels — to identify where the deviation occurs. If the sensor output is analog, I'd check the ADC reference and input circuitry; if digital (I2C/SPI), I'd verify communication timing and pull-up resistor values.

I'd also review the batch's manufacturing records: which component lot numbers were used, which reflow oven profile was applied, and whether any process parameters changed. Component lot variation is a common cause — a batch of sensors or passives might have shifted slightly in tolerance. I'd cross-reference the failed units' serial numbers with production date/time stamps to see if failures cluster around a specific shift or machine.

Finally, I'd perform root-cause verification by swapping a suspect component from a failed board into a known-good board (or vice versa) to confirm the failure follows the component, not the PCB or assembly process. This isolates whether it's a component issue, a soldering issue, or a design margin problem.

**Possible follow-ups:** How would you decide whether to rework the failed boards or scrap them? What documentation would you create to prevent this failure mode in future production runs?

---

## Q5: A junior engineer on your team has spent three days debugging a firmware crash that occurs randomly during system startup. They've tried adding delays, changing initialization order, and disabling features — nothing has worked. How would you guide them to a more effective debugging approach?

**Answer:** First, I'd acknowledge their effort and then help them step back from trial-and-error to a hypothesis-driven approach. Random startup crashes often stem from race conditions, uninitialized memory, or timing-dependent hardware initialization. I'd ask them to characterize the crash more precisely: Is it truly random, or does it correlate with specific conditions like battery voltage, temperature, or the presence of external connections? Can they capture the crash address or fault handler output?

I'd suggest they instrument the startup sequence with deterministic logging — for example, toggling a GPIO pin at each initialization step and capturing it on an oscilloscope alongside the crash event. This would reveal exactly which step fails and whether the timing relative to other events matters. If the microcontroller has a fault handler (HardFault, BusFault), I'd have them configure it to dump the stack frame and register contents to a reserved memory region that survives reset.

I'd also recommend they review the startup code for common pitfalls: peripherals being accessed before their clocks are enabled, DMA channels starting before buffers are initialized, or interrupt handlers firing before the interrupt controller is configured. If the system uses an RTOS, I'd check whether tasks or interrupts are accessing shared resources before the scheduler is ready. Finally, I'd suggest they create a minimal reproduction case — strip the startup sequence to the bare minimum and add back features one at a time until the crash reappears. This isolates the offending component without the noise of the full system.

**Possible follow-ups:** What would you do if the crash only occurs once every 50-100 power cycles and cannot be reproduced reliably on the bench? How would you teach the junior engineer to write a structured debugging plan before touching any code?