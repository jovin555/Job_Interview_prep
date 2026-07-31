# tools — Day 10

## Q1: How would you approach setting up a signal integrity analysis in Altium Designer for a mixed-signal PCB that has both high-speed digital interfaces and sensitive analog sensor inputs?

**Answer:** I'd start by defining what I actually need to verify, because signal integrity analysis can quickly become a time sink if you try to simulate everything. For a mixed-signal board, the critical questions are usually: (1) are the high-speed digital traces clean enough at the receiver, and (2) is digital switching noise coupling into the analog front-end?

My workflow would be:

1. **Set up the stackup first** — SI analysis is meaningless without an accurate layer stackup. I'd define the dielectric materials, thicknesses, copper weights, and impedance targets in the layer stack manager. This is the foundation everything else depends on.

2. **Configure the constraint system** — Before running simulations, I'd make sure the design rules reflect the actual requirements: impedance targets for controlled traces, maximum trace lengths, spacing rules between digital and analog regions. The SI analysis will flag violations, but the constraint manager should already be catching the obvious ones.

3. **Run impedance and reflection analysis on critical nets** — I'd select the high-speed nets (clock lines, data buses, SPI at speed) and run the reflection analysis. This shows whether terminations are adequate and whether stub lengths are causing reflections. I'd look at the waveform at the receiver and check for overshoot, undershoot, and ringing.

4. **Check crosstalk between aggressor and victim nets** — This is where the mixed-signal aspect comes in. I'd identify the worst-case coupling scenarios: high-speed digital traces running parallel to analog sensor lines, or clock lines crossing the analog ground plane. The crosstalk analysis shows the coupled noise amplitude at the victim receiver.

5. **Correlate with the analog budget** — For the analog side, I'd take the simulated noise from crosstalk and compare it against the sensor's noise budget. If the ADC has a 16-bit resolution and a 5V reference, the LSB is about 76 µV — so any coupled noise above a fraction of that needs attention.

The key trade-off here is simulation accuracy versus time. I'd start with the most critical nets and the simplest models (transmission line with lumped loads) and only add complexity where the initial results are marginal. I'd also validate the simulation setup against at least one real measurement — a TDR measurement of a test trace or an oscilloscope capture of a known signal — to make sure my models are reasonable.

**Possible follow-ups:**
- How would you decide which nets are "critical enough" to simulate versus which ones you can rely on design rules alone?
- What would you do if the simulation shows marginal crosstalk on an analog sensor line — what mitigation options would you consider?

---

## Q2: How would you approach using a thermal simulation tool like Flotherm or Icepak to validate the thermal design of a sealed medical device enclosure before building a prototype?

**Answer:** Thermal simulation for a sealed medical device is particularly important because there's no airflow to help — everything is conduction and radiation through the enclosure. I'd approach it in stages:

1. **Build the simplified geometry** — I'd start with the major heat sources: the microcontroller, power management ICs, any motor drivers or amplifiers, and the battery. I'd model the PCB as a layered structure with copper planes, since those are significant heat spreaders. The enclosure material and wall thickness matter too, especially if it's plastic versus metal.

2. **Define the thermal loads** — I'd assign power dissipation values to each component based on worst-case operating conditions, not typical. For a medical device that runs continuously, I'd use the maximum ambient temperature specified in the requirements and the maximum internal power draw. I'd also consider duty cycles — a motor that runs 10% of the time has a different thermal impact than one that runs continuously.

3. **Set up the boundary conditions** — For a sealed enclosure, the dominant heat transfer path is conduction through the PCB to the enclosure wall, then natural convection and radiation from the outer surface. I'd model the ambient environment at the specified maximum temperature and check whether any internal components need dedicated thermal paths (thermal pads, heat spreaders, or vias under hot components).

4. **Run the simulation and iterate** — The first pass usually reveals which components are running hot. I'd look at junction temperatures against the datasheet limits and the device's reliability targets. If something exceeds its limit, I'd consider: adding thermal vias under the component, routing a copper plane to spread heat, adding a thermal pad to the enclosure, or moving the component to a cooler location on the board.

5. **Validate with a sanity check** — Before trusting the simulation, I'd do a hand calculation for the worst-case component: estimate the thermal resistance from junction to ambient through the PCB and enclosure, and see if the numbers are in the same ballpark. If the simulation and hand calc disagree by more than 30-40%, something is wrong with the model.

The key insight is that thermal simulation is most valuable for comparing design options — "does adding a thermal pad under this regulator drop its temperature by 20°C?" — rather than predicting absolute temperatures with high precision. I'd use it to guide design decisions and identify risk areas, then validate with thermocouple measurements on the prototype.

**Possible follow-ups:**
- How would you handle the uncertainty in the power dissipation values for components that have variable loads?
- What would you do if the simulation shows the enclosure surface temperature exceeds the touch-temperature limit for medical devices?

---

## Q3: How would you approach setting up a DFM (Design for Manufacturing) rule deck in Cadence Allegro to catch common fabrication issues before sending a design to the board house?

**Answer:** A good DFM rule deck is essentially encoding the board house's manufacturing capabilities into your design rules so you catch issues before they become expensive respins. I'd approach it in layers:

1. **Start with the board house's capabilities** — The first step is to get the specific fabrication and assembly guidelines from the manufacturer I plan to use. Different board houses have different minimum trace widths, spacing, hole sizes, and annular ring requirements. I'd use their published capabilities as the baseline, not generic industry defaults.

2. **Set up the physical rule deck** — In Allegro's constraint manager, I'd configure:
   - Minimum trace width and spacing (including differential pair spacing)
   - Minimum annular ring for vias and through-hole pads
   - Minimum hole size and drill tolerance
   - Minimum solder mask sliver and solder mask expansion
   - Minimum silkscreen text height and line width
   - Copper-to-edge clearance and board edge routing requirements

3. **Configure the manufacturing rules** — Beyond the physical rules, I'd set up checks for:
   - Unconnected copper pours or islands
   - Copper slivers that could peel during etching
   - Acid traps (acute angles between traces)
   - Vias placed too close to SMD pads (solder wicking risk)
   - Components placed too close to the board edge (panelization and depaneling clearance)

4. **Run DFM checks early and often** — The key is to run these checks throughout the layout process, not just at the end. I'd set up the rule deck before starting the layout and run DFM checks at each milestone: after placement, after routing, and before final sign-off. Catching a spacing violation during placement is much cheaper than catching it after routing is complete.

5. **Review the DFM report with the board house** — Before sending the design out, I'd generate the DFM report and review it with the manufacturer. They often have additional checks or specific preferences that aren't in their published guidelines. This conversation can catch issues that automated checks miss, like unusual via structures or non-standard board shapes.

The trade-off here is between being too conservative (which increases board cost and size) and too aggressive (which risks fabrication issues). I'd aim for a rule deck that matches the board house's capabilities with a small safety margin, and I'd document any intentional violations with a rationale so they're not "fixed" by someone who doesn't understand the design intent.

**Possible follow-ups:**
- How would you handle a situation where the DFM rule deck conflicts with a critical electrical requirement, like a minimum trace width for current carrying capacity?
- What DFM checks would you prioritize for a prototype run versus a high-volume production run?

---

## Q4: How would you approach using a logic analyzer to debug a USB 2.0 enumeration failure where the device is not being recognized by the host, but the oscilloscope shows the D+ and D- lines are toggling?

**Answer:** This is a classic case where the oscilloscope tells you "something is happening" but not "what is happening." The logic analyzer is the right tool because USB enumeration is a protocol-level process, and you need to see the packet traffic to understand where it's failing.

My approach would be:

1. **Set up the logic analyzer for USB decoding** — I'd connect the logic analyzer probes to D+ and D- at the device side, ideally at the connector or the closest test point. I'd configure the analyzer for USB 2.0 low-speed or full-speed decoding, depending on the device. The sample rate needs to be high enough to capture the signaling — for full-speed USB at 12 Mbps, I'd want at least 100 MS/s to see the waveform details.

2. **Capture the enumeration sequence** — I'd trigger on the first USB activity (the host sending a reset or a SOF packet) and capture several seconds of traffic. The enumeration sequence follows a predictable pattern: reset, device descriptor request, address assignment, configuration descriptor request, and so on. I'd look for where this sequence breaks down.

3. **Analyze the packet-level failures** — Common issues I'd look for:
   - **CRC errors on the device's responses** — this suggests a signal integrity issue or a timing problem in the device's USB transceiver
   - **The device not responding to the host's requests** — this could be a firmware issue where the USB stack isn't handling the request correctly
   - **The device responding with a stall or error** — this suggests the firmware is rejecting the request, possibly because the descriptor data is wrong
   - **The host not sending the expected next step** — this could mean the host is rejecting the device's response

4. **Correlate with the oscilloscope** — If the logic analyzer shows CRC errors or corrupted packets, I'd go back to the oscilloscope with the decoded packet information to look at the analog characteristics of the specific failing packets. Is the rise time too slow? Is there ringing on the edges? Is the bit timing off?

5. **Check the firmware configuration** — If the packets look clean but the device is still not enumerating, I'd review the USB descriptor configuration in firmware. A common issue is a descriptor that violates the USB specification — for example, a configuration descriptor with an incorrect total length or an endpoint descriptor with an invalid maximum packet size.

The key insight is that the logic analyzer gives you the protocol-level view, which narrows down the problem space dramatically. Once you know whether it's a signal integrity issue, a firmware issue, or a host-side issue, you can focus your debugging effort in the right direction.

**Possible follow-ups:**
- How would you distinguish between a signal integrity issue and a firmware issue when the logic analyzer shows corrupted packets?
- What would you look for if the device enumerates correctly on some hosts but not others?

---

## Q5: (Behavioral) Imagine you are leading a hardware bring-up for a new medical device prototype, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a situation where the first priority is to establish the facts without letting anyone feel blamed, because both teams genuinely believe they're correct. The timeline pressure makes it tempting to just pick a side and force a fix, but that risks creating a deeper problem if we guess wrong.

My approach would be:

1. **Bring both teams together with the actual documentation** — I'd call a meeting with the firmware lead and the hardware lead, and ask each to bring their source of truth: the firmware's I2C driver code and the hardware's datasheet or interface specification. The goal is to compare the two implementations against the actual hardware capability, not against anyone's memory of what was agreed.

2. **Trace the discrepancy to its source** — I'd walk through the specific I2C transactions the firmware sends and map them against what the hardware actually expects. This usually reveals where the mismatch originated — perhaps an early datasheet revision had different addressing, or the register map was changed during development and the firmware was never updated. Understanding the source helps determine which side is "more correct" relative to the current hardware.

3. **Determine the lowest-risk path forward** — Once we know the actual mismatch, I'd evaluate the options:
   - If the hardware can support 7-bit addressing (some devices support both), the firmware change might be minimal
   - If the hardware is fixed at 10-bit addressing, the firmware needs to be updated, but I'd check whether the register map differences are also addressable in firmware
   - If the register map is fundamentally incompatible, we might need a hardware workaround or a firmware shim layer

4. **Make a decision and assign ownership** — I'd make the call based on the risk assessment, not on which team is "right." The decision needs to be made quickly given the timeline, so I'd assign one owner for the fix and set a clear deadline. I'd also document the decision and the rationale so it's clear to everyone why we chose this path.

5. **Set up a verification step** — Before the integration test, I'd have the team that made the change demonstrate the fix on the bench with a logic analyzer capture showing the I2C transactions matching the expected protocol. This gives us confidence before the formal test.

6. **Address the process gap** — After the immediate crisis is resolved, I'd look at why this mismatch wasn't caught earlier. Was there no interface control document? Was the register map not reviewed by both teams? This is where the real lesson is — the protocol mismatch is a symptom of a communication gap between teams.

The key principle here is to separate the technical problem from the people problem. The technical problem needs a fast, evidence-based decision. The people problem — how to prevent this from happening again — needs a more thoughtful process improvement discussion, but not in the heat of the moment.

**Possible follow-ups:**
- How would you handle it if the firmware lead strongly disagrees with your decision and wants to escalate to management?
- What process changes would you propose to prevent this type of interface mismatch in future projects?