# debugging-failure-analysis — Day 1

## Q1: Walk me through your structured approach to debugging a new hardware failure that you've never seen before.

**Answer:** My approach follows a systematic funnel from observation to root cause. First, I gather all observable symptoms—what exactly is failing, under what conditions, and with what repeatability. I document the environment: temperature, supply voltage, load conditions, and any recent changes. Then I isolate the failure domain: is it power-related, signal integrity, firmware, or component-level? I start with the simplest measurements—visual inspection for shorts/cold joints, then power rail integrity with an oscilloscope (ripple, droop under load). Next, I check clock signals and critical control lines. If the issue is intermittent, I look for timing dependencies or thermal effects. I use divide-and-conquer: disconnect subsystems until the failure disappears, then add back until it reappears. At Trudell Medical International, I ran multiple 8D root-cause investigations for critical medical device failures, and this structured methodology was essential—especially when patient safety was on the line. The 8D process forces discipline: define the problem, contain it, identify root cause, implement permanent corrective action, and verify.

**Possible follow-ups:** How do you differentiate between a hardware issue and a firmware issue when symptoms overlap? What's your go-to tool for intermittent failures?

---

## Q2: Describe a specific debugging challenge you faced during IEC 60601 compliance testing and how you resolved it.

**Answer:** During the Lotus (Printer and Toco) project, we were performing IEC 60601 testing for the maternal/infant care system. During EMC emissions testing, the printer unit showed unexpected radiated emissions at specific frequencies that exceeded the standard limits. The **Situation** was that we had a production-ready design failing a mandatory regulatory test, which could delay certification and market release. The **Task** was to identify the emission source and implement a fix without major PCB respin. The **Action** involved systematic near-field probing with an EMC probe and spectrum analyzer to locate the hot spots. I traced the emissions to the switching regulator driving the printer's thermal print head—the switching frequency harmonics were coupling onto the enclosure via the ground plane. I implemented a two-part fix: added ferrite beads on the power input to the print head driver, and improved the local decoupling with a low-ESR capacitor closer to the switching node. I also adjusted the switching frequency slightly to move harmonics away from problematic bands. The **Result** was that emissions dropped below the limit with margin, we passed the retest, and the fix was incorporated into the production BOM without a board revision.

**Possible follow-ups:** What specific IEC 60601 clauses were you testing against? How did you validate the fix didn't affect other performance parameters?

---

## Q3: Explain how you would debug an I2C communication failure between a sensor and a microcontroller in a battery-powered medical device.

**Answer:** I'd approach this systematically. First, verify the physical layer: check SDA and SCL lines with an oscilloscope for proper voltage levels (are they reaching the correct logic thresholds?), rise/fall times, and pull-up resistor values. In a battery-powered device like the Smart OPEP Device, power management is critical—I'd check if the sensor's power rail is stable during communication or if there's droop when the radio or LED fires. Next, check the I2C bus for contention: are both lines being pulled high properly when idle? Look for clock stretching issues—some sensors stretch the clock while processing, and the master must support this. I'd also check for address conflicts if multiple devices share the bus. If the scope looks clean, I'd add debug prints or toggle a GPIO on the master to confirm the firmware is actually initiating the transaction at the right time. A common issue in medical devices is that the sensor enters a low-power sleep mode and doesn't respond until woken up—I'd verify the wake sequence timing. Finally, I'd check for ground loops or noise coupling, especially since medical devices often have isolated sections.

**Possible follow-ups:** How would you handle a situation where the bus works at room temperature but fails at 40°C? What pull-up resistor value would you start with for a 400kHz I2C bus?

---

## Q4: You're debugging a PCB that passes functional test but fails after 100 hours of continuous operation. What's your failure analysis plan?

**Answer:** This sounds like a latent failure mechanism—something that develops over time rather than an immediate defect. My plan would be:

First, **thermal analysis**: use a thermal camera during operation to identify hot spots. Components operating near their maximum junction temperature can fail after hours of thermal cycling. I'd check if the failure correlates with temperature by accelerating it—run at elevated ambient temperature to see if failure occurs sooner.

Second, **power analysis**: monitor all power rails with a data-logging oscilloscope over the full 100-hour period. Look for gradual drift, increasing ripple, or a regulator going into thermal shutdown. Electrolytic capacitors drying out or inductors saturating as they heat up are common culprits.

Third, **mechanical stress**: check for cracked solder joints or BGA balls that fail after thermal cycling. This was relevant in the SOBA Heart Lung Support Machine project where we had continuous operation requirements—vibration from the motor could exacerbate mechanical failures.

Fourth, **component-level analysis**: if I identify a failing subsystem, I'd desolder and characterize suspect components—check ESR of capacitors, measure voltage references for drift, or use a curve tracer on semiconductors.

Finally, **cross-sectioning** if needed: physically slice the PCB to inspect via integrity or solder joint quality under a microscope.

**Possible follow-ups:** How would you design a HALT (Highly Accelerated Life Test) to catch this earlier in development? What failure modes are specific to medical devices that must operate continuously?

---

## Q5: Tell me about the most challenging 8D root-cause investigation you led at Trudell Medical International. What was the failure, and how did you identify the root cause?

**Answer:** **Situation:** We had a Class II medical device (the Smart OPEP Device) experiencing intermittent failures in the field—the device would occasionally fail to detect patient breathing patterns, causing the RGB LED feedback to behave incorrectly. The failure rate was low (~1%) but clinically significant since it affected therapy guidance.

**Task:** Lead the 8D investigation to identify root cause, implement containment, and develop permanent corrective action. Patient safety was the priority, so we needed to understand if the failure could lead to incorrect therapy.

**Action:** I assembled a cross-functional team including firmware, quality, and manufacturing. We started with D1 (problem definition)—we precisely characterized the failure: it only occurred after the device had been in continuous use for 3+ days, and only in certain patient positions. D2 (containment) involved a field advisory with instructions to reset the device if symptoms appeared. For D3-D4 (interim action and root cause analysis), we used fishbone diagrams and 5-Whys. The breakthrough came when we analyzed logged pressure sensor data from returned units. I noticed the pressure sensor's I2C bus occasionally returned all-ones (0xFF) during specific breathing patterns. Using an oscilloscope on a test setup that replicated the failure conditions, I found that the sensor's power rail had a 50mV droop that coincided with the Li-ion boost converter switching—but only when the battery was below 30% charge. The droop was just enough to cause the sensor's internal voltage reference to drift, corrupting the I2C communication.

**Result:** The root cause was a marginal decoupling capacitor on the sensor's power rail that had adequate capacitance at nominal voltage but lost effective capacitance as the battery voltage dropped (DC bias effect on MLCC capacitors). The permanent corrective action was replacing the capacitor with a higher-voltage-rated MLCC that maintained capacitance across the full battery range. We also added firmware validation to reject corrupted sensor readings. The fix eliminated the failure mode completely.

**Possible follow-ups:** How did you replicate the 3-day failure condition in the lab? What other MLCC DC bias effects should designers watch for in battery-powered devices?