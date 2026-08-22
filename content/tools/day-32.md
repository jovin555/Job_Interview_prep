# tools — Day 32

## Q1: How would you approach setting up a mixed-signal simulation in LTSpice to verify that a precision analog front-end will maintain adequate performance when the digital section of the board is actively switching?

**Answer:** I'd start by defining what "adequate performance" means for the specific sensor application — usually a target signal-to-noise ratio or a maximum allowable noise floor at the ADC input. The key challenge is that a pure analog simulation won't capture the coupling mechanisms from the digital side, so I'd build the simulation in stages.

First, I'd model the analog front-end in isolation: the sensor source impedance, any input filtering, the amplifier stages, and the ADC input stage. I'd run AC and transient analyses to establish the baseline noise performance and frequency response. This gives me a reference point.

Next, I'd add the coupling paths. The dominant mechanisms are usually power supply noise and ground bounce. For the power supply, I'd model the switching regulator output with its ripple and switching transients, then include the decoupling network (bulk capacitor, ceramic capacitors with their ESL/ESR, and the PCB trace inductance between them). I'd inject that noise into the analog supply node through the modeled impedance of the PCB traces. For ground coupling, I'd add a small inductance between the analog and digital ground reference points and inject a current source representing the digital switching current — a trapezoidal waveform at the digital clock frequency with realistic rise/fall times.

I'd then run a transient simulation long enough to capture several switching cycles and look at the voltage at the ADC input. I'd also run a noise analysis to see how the supply noise couples through the amplifier's PSRR — the simulation should include the PSRR frequency dependence, not just a flat value.

The critical validation step is correlating with real measurements. I'd build the front-end on a bench with the digital section running, measure the ADC input noise with a spectrum analyzer or FFT on an oscilloscope, and compare the noise floor and specific spurs against the simulation. If they don't match, I'd look at what coupling path I missed — often it's the return current path through a connector or a ground plane slot that wasn't modeled.

**Possible follow-ups:**
- How would you model the PSRR of an op-amp in LTSpice if the datasheet only provides a typical curve?
- What would you do if the measured noise floor is significantly higher than the simulation predicts?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize the noise coupling between a switching regulator and a precision analog sensor on the same PCB?

**Answer:** The goal is to understand both the magnitude and the mechanism of coupling, so I'd set up the measurement to capture the noise source, the victim, and the coupling path simultaneously.

I'd use at least three channels: one on the switching node of the regulator (the source), one on the analog sensor's supply pin or output (the victim), and one on the ground reference between the analog and digital sections. The fourth channel could be used for the regulator's output ripple or the ADC's reference voltage.

The key is synchronization and triggering. I'd trigger on the switching node to establish a time reference, then look at the victim signal in the time domain to see if noise events correlate with switching edges. If the noise appears at the switching frequency, it's likely conducted through the supply or ground. If it appears as bursts at different intervals, it might be radiated coupling or related to load transients.

I'd use the FFT function to look at the frequency content of the victim signal. This helps distinguish between broadband noise (poor decoupling, ground bounce) and narrowband spurs (switching frequency and harmonics). I'd also use the oscilloscope's math functions to compute the transfer function between the source and victim — essentially dividing the victim's FFT by the source's FFT to see which frequencies are coupling most efficiently.

For the measurement itself, probe technique matters. I'd use short ground springs on passive probes rather than the long ground leads, which can pick up radiated noise and create ground loops. For the switching node, I'd use a high-voltage-rated probe. For the analog signal, I'd use a low-noise probe or possibly an active probe if the signal is high-impedance.

I'd also vary operating conditions: different load currents on the regulator, different sensor gain settings, and different digital activity levels. This helps identify whether the coupling is primarily through the supply, ground, or radiation. For example, if the noise increases when the digital section is active but the regulator load is constant, that points to ground coupling or radiated coupling rather than supply conduction.

**Possible follow-ups:**
- How would you distinguish between conducted and radiated coupling using the oscilloscope measurements?
- What bandwidth would you need on the oscilloscope to properly characterize this coupling?

---

## Q3: How would you approach setting up a Git-based workflow for a firmware project that needs to support multiple hardware revisions with different sensor configurations, while maintaining a single codebase and ensuring that the correct configuration is built for each revision?

**Answer:** I'd structure this around three layers: the build system, the board definition layer, and the application code layer.

At the build system level, I'd use Kconfig or equivalent configuration management to define hardware revision options as selectable configurations. Each hardware revision gets a named configuration that selects the correct sensor drivers, pin mappings, and bus interfaces. The key is that these are compile-time selections, not runtime detection — though I might add runtime detection as a safety check.

In the board definition layer, I'd create a directory structure where each hardware revision has its own device tree or board definition file. This keeps the hardware-specific details — pin assignments, peripheral instances, clock configurations — isolated from the application code. The application code then talks to abstracted interfaces: a sensor API that doesn't care whether the underlying bus is I2C or SPI.

For the application layer, I'd use conditional compilation sparingly. The goal is to minimize `#ifdef` blocks in the application code. Instead, I'd use driver abstraction — each sensor type has a common interface, and the board configuration selects which driver implementation gets compiled. This way, the application logic stays the same across revisions, and the differences are contained in the driver layer.

For version control, I'd use Git branches for active development on different revisions, but with a strict merge strategy. The main branch always builds for all supported revisions — I'd set up CI to build every configuration on every commit. Release tags would include the hardware revision they support. I'd also maintain a compatibility matrix in the repository documentation that maps firmware versions to hardware revisions.

The critical practice is testing. Every hardware revision needs its own test configuration, and the regression test suite needs to run against all supported revisions. I'd also add a build-time check that verifies the selected configuration matches the expected hardware revision — for example, checking that the sensor address in the configuration matches the address strapped on the board.

**Possible follow-ups:**
- How would you handle a situation where a hardware revision requires a different RTOS configuration, such as different stack sizes or thread priorities?
- How would you manage the transition when a new hardware revision is added mid-development?

---

## Q4: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This is a classic intermittent failure that's likely temperature-dependent, so I'd approach it as a two-part problem: capturing the failure when it happens, and then analyzing the captured data to find the root cause.

For the capture setup, I'd connect the logic analyzer to the SPI lines — SCK, MOSI, MISO, and CS — plus a few additional channels for context: maybe a GPIO that indicates when the system is actively reading the sensor, and possibly the interrupt line from the slave if it has one. I'd set the sampling rate to at least 4-5 times the SPI clock to get good edge resolution.

The challenge with intermittent failures is that you can't just sit and watch. I'd set up the logic analyzer to trigger on the failure condition. Since the failure is "master fails to receive data," I'd look for a trigger condition like a read transaction where MISO doesn't transition when expected, or where the data returned is all ones or all zeros. Some logic analyzers allow triggering on protocol-level conditions — for example, a SPI decoder that triggers when the received data doesn't match an expected pattern.

I'd also set up long-duration capture. Many logic analyzers have deep memory or streaming mode to disk. I'd capture continuously over several hours, then analyze the data around the failure event. The key is to look at the transactions leading up to the failure — is there a gradual degradation (marginal setup/hold times, missing bits) or is it an abrupt failure?

Once I have the capture, I'd analyze the timing. I'd check the SPI clock frequency against the slave's specified maximum — temperature drift could push the clock slightly out of spec. I'd look at the MISO data validity window relative to the clock edges: is the slave's data changing too close to the sampling edge? I'd also check the CS timing — is the slave being deselected and reselected properly between transactions?

Temperature is likely affecting either the slave's internal timing or the PCB trace characteristics. I'd correlate the failure with temperature by monitoring the enclosure temperature alongside the SPI traffic. If the failure consistently occurs at a specific temperature threshold, that points to a component specification issue — the slave's timing margins shrinking at temperature, or a passive component (like a pull-up resistor) drifting.

I'd also consider power supply effects — at higher temperatures, the regulator's output might droop slightly under load, and the slave's timing could be affected by supply voltage. I'd add a channel to monitor the slave's supply voltage during the capture.

**Possible follow-ups:**
- How would you determine whether the issue is with the master's sampling timing or the slave's data output timing?
- What would you do if the logic analyzer capture shows the SPI signals are clean but the data is still wrong?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first priority is to stop the clock on assumptions and get everyone looking at the same ground truth. I'd call an immediate meeting with both teams, but not to assign blame — to establish facts. I'd bring the actual hardware schematic, the sensor datasheet, and the firmware source code to the table.

The key move is to verify the hardware configuration directly rather than relying on what either team believes. I'd have someone physically probe the address pins on the PCB or read back the device's ID register through a known-good I2C master — maybe a logic analyzer or a bench-top I2C controller — to confirm what address the hardware actually responds to. At the same time, I'd have the firmware team show me the exact register map they're using, cross-referenced against the datasheet for the specific sensor variant on the board.

Once we have confirmed facts, I'd assess the impact. If the hardware is already in fabrication, changing the address strapping isn't an option. The firmware change might be straightforward — updating the address and register map — but I'd need to verify the register map differences don't affect other functionality. If the register layouts are significantly different, the firmware changes could be more extensive than just an address change.

I'd then make a decision based on risk and schedule. If the firmware change is low-risk and can be verified quickly, I'd authorize it with a clear change control process — documented, reviewed, and tested. If the change is high-risk or the register map differences are substantial, I'd consider whether the hardware can be reworked or whether we need to delay integration testing.

The critical part is communication. I'd be transparent with the team about the situation, the decision, and the rationale. I'd also use this as a process improvement opportunity — this kind of mismatch should have been caught earlier through a hardware-firmware interface document or a bring-up checklist that verifies the I2C address and register map before integration testing.

After resolving the immediate issue, I'd implement a preventive measure: a formal interface control document that both teams sign off on, and a bring-up test that verifies the I2C communication against the documented protocol before full integration testing begins.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct because it works on the evaluation board?
- What would you do if the hardware team says the address strapping is correct per the schematic, but the firmware team's code is already approved for a regulatory submission?