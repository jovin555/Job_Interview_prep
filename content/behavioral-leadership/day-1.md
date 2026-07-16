# behavioral-leadership — Day 1

## Q1: Describe a time when you had to lead a technical root-cause investigation for a critical failure in a medical device. How did you structure the process and ensure the team stayed focused on the right issues?

**Answer:** At Trudell Medical International, during the development of our Smart OPEP Device, we encountered intermittent failures in the pressure sensor flow capture during patient use testing. As the Electronics Design Engineering Specialist, I led an 8D root-cause investigation. I structured the process by first assembling a cross-functional team including firmware, mechanical, and test engineers. We started with a clear problem statement and containment actions—isolating suspect units and implementing temporary test limits to prevent further field exposure. I then guided the team through root cause analysis using fishbone diagrams and 5-Whys, systematically ruling out firmware timing issues, mechanical blockages, and power supply instability. The investigation revealed that insufficient decoupling on the sensor power rail was allowing transient noise from the Li-ion power management circuitry to corrupt sensor readings during specific battery discharge states. I directed the PCB layout redesign to add localized decoupling capacitors closer to the sensor, which reduced signal noise by 15% per our validation testing. The key to keeping the team focused was maintaining a disciplined timeline for each 8D phase and ensuring we had objective data before moving to the next step.

**Possible follow-ups:**
- How did you handle team members who wanted to jump to solutions before completing the root cause analysis?
- What documentation did you produce from the 8D process, and how did it feed into your design review process for future projects?

---

## Q2: Tell me about a time you had to influence a decision or drive alignment across multiple engineering disciplines without having direct authority over the team members.

**Answer:** During my tenure at GE Healthcare as a Lead Engineer (contractor via Quest Global), I was responsible for managing medical product development and executing regulatory testing phases. In one project, we had a disagreement between the hardware team and the software team regarding the timing requirements for a sensor data acquisition loop. The hardware team wanted a fixed sampling rate to simplify analog front-end design, while the software team argued for a variable rate to optimize power consumption. I didn't have direct authority over either team—both reported to different functional managers. I scheduled a series of technical alignment meetings where I presented the IEC 60601 regulatory constraints that applied to our device, showing that the fixed-rate approach actually had a compliance advantage for certain patient safety parameters. I then facilitated a trade-off discussion where we agreed on a hybrid approach: fixed-rate sampling during active monitoring modes and a reduced rate during standby, with clear handshake protocols between hardware interrupts and the Zephyr RTOS scheduler. This required me to translate between the hardware team's language (timing jitter, ADC settling times) and the software team's concerns (task priority inversion, power budget). The result was a design that passed regulatory testing on schedule.

**Possible follow-ups:**
- What specific IEC 60601 clauses were relevant to that timing decision?
- How did you handle it when one team's manager pushed back on the compromise?

---

## Q3: Describe a situation where you had to make a difficult technical trade-off that impacted project schedule or resources. How did you communicate that decision to stakeholders?

**Answer:** On the Lotus (Printer and Toco) project at Trudell Medical International, we were performing IEC 60601 testing when we discovered circuit design issues in the Toco device's uterine contraction monitoring channel. The issue was related to noise coupling from the printer unit's motor driver into the sensitive analog front end, causing artifacts in the contraction waveform during printing operations. We had two options: a quick firmware workaround that would disable printing during contraction monitoring (reducing clinical utility) or a hardware redesign of the analog front-end filtering and PCB layout (requiring 6-8 weeks and a new prototype run). I analyzed the clinical impact and determined that the hardware fix was the only path to meet the device's intended use requirements for continuous monitoring during labor. I presented this to program management with a clear risk assessment: the hardware redesign would push our regulatory submission by 8 weeks but would avoid a potential recall or field correction later. I also proposed a mitigation plan—parallel workstreams where we could begin updating the test protocols and documentation while the hardware team completed the layout changes. The stakeholders approved the schedule impact, and we successfully resolved the circuit design issues found during testing, ultimately passing the full IEC 60601 suite on the next attempt.

**Possible follow-ups:**
- What specific circuit design issues did you find, and how did you diagnose them?
- How did you manage the team's morale during the 8-week delay?

---

## Q4: How do you approach mentoring junior engineers on your team, particularly when they are working on high-stakes medical device projects where mistakes can have serious consequences?

**Answer:** At Trudell Medical International, I regularly mentor junior hardware engineers who join our medical device team. My approach is structured around progressive responsibility with safety nets. For example, when a junior engineer was assigned to help with the SOBA Heart Lung Support Machine's biological parameter monitoring circuits (temperature and pressure sensors), I didn't just hand them the schematic and say "go." I started with a design review of my existing reference design, walking through each block and explaining why specific component choices were made—particularly the isolation requirements and fail-safe mechanisms required for life-support equipment. Then I gave them a well-defined sub-block to design: the pressure sensor signal conditioning stage. I provided the sensor datasheet, the IEC 60601 isolation requirements, and the target accuracy specs. We set up weekly checkpoints where they would present their progress, and I would ask probing questions rather than giving direct answers: "What happens if the sensor output rail goes to 3.3V during a fault? How does your filter affect the 10Hz bandwidth we need?" This teaches them to think through failure modes. I also pair-review their PCB layouts before release, focusing on the decoupling and routing that I know from experience are critical for noise performance. The result is that junior engineers become productive contributors faster while the safety-critical aspects are still reviewed by a senior engineer.

**Possible follow-ups:**
- Have you ever had to step in and redo a junior engineer's work because of a safety concern? How did you handle that conversation?
- How do you balance giving them autonomy with the need for rigorous medical device documentation?

---

## Q5: Tell me about a time when you had to lead a team through a significant technical challenge where the initial approach was not working. How did you pivot and keep the team motivated?

**Answer:** During the development of the 5W High-Reliability EDFA for space-qualified booster modules at Vinvish Technologies, we were designing the radiation-hardened (50K rad-hard) hardware using STM32 microcontrollers with external DAC/ADC. Our initial approach used a single high-resolution ADC multiplexed across multiple monitoring channels (temperature, optical power, pump laser current). During board-level testing, we discovered that the multiplexing timing was introducing latency that caused the feedback loop for the pump laser current control to oscillate under certain operating conditions. The team was frustrated because we had spent weeks on the ADC selection and layout. I called a halt to further testing and led a design review where we brainstormed alternatives. I proposed splitting the monitoring into two groups: critical control parameters (pump laser current) would get a dedicated ADC channel with no multiplexing delay, while non-critical telemetry (temperature) could remain multiplexed. This required a PCB layout change to add a second ADC, but it preserved the radiation-hardened component selection we had already qualified. I kept the team motivated by framing this not as a failure but as a necessary refinement for a space-qualified product—emphasizing that finding this issue in testing was far better than discovering it after launch. We completed the redesign in three weeks, and the final hardware passed both the radiation testing and the industrial laser cutting application validation.

**Possible follow-ups:**
- What specific radiation-hardening techniques did you use for the ADCs and the STM32?
- How did you validate that the new dual-ADC approach didn't introduce new failure modes?