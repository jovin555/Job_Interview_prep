# debugging-failure-analysis — Day 18

## Q1: How would you approach a failure investigation where a medical device's analog measurement is accurate when tested with a known-good reference signal, but shows a consistent gain error when connected to the actual patient sensor — and the error magnitude varies between different sensor units?

**Answer:** This pattern — accurate with a reference, but gain error with real sensors — points me toward the interface between the sensor and the measurement chain rather than the measurement chain itself. I'd start by characterizing the sensor interface parameters that could affect gain: excitation voltage accuracy, input impedance of the front-end relative to the sensor's output impedance, and any cable or connector resistance in series with the signal path.

For a bridge-type sensor, for example, a gain error that varies between units often traces back to the excitation voltage being loaded differently by different sensor impedances, or to the front-end's input bias currents interacting with source impedance mismatches. I'd measure the actual excitation voltage at the sensor terminals — not just at the regulator output — because voltage drop across connector contacts, cabling, or protection components can vary with each sensor's current draw.

I'd also check whether the gain error correlates with any sensor parameter that varies between units, such as bridge resistance or offset. Plotting gain error against sensor resistance across multiple units would quickly reveal whether this is a source-impedance interaction. If the correlation is strong, the fix is typically either a higher-impedance front-end, a true ratiometric measurement (using the excitation voltage as the ADC reference), or a calibration step that accounts for per-unit sensor characteristics.

**Possible follow-ups:**
- How would you determine whether the error is a gain error versus an offset error, and why does that distinction matter for the investigation?
- What design changes would you consider if the root cause turned out to be connector contact resistance variation?

---

## Q2: How would you approach debugging a medical device where the firmware occasionally fails to detect a button press, and the failure is more frequent when the device is powered from battery than from a bench supply?

**Answer:** The battery-versus-bench-supply difference is a strong clue that this isn't purely a firmware logic issue — it suggests something about the power source is affecting the button input path. I'd start by comparing the two power conditions systematically: battery voltage under load, ripple on the supply rail, and the button input's voltage levels during the press in both cases.

A common mechanism is that the button input lacks a proper debounce or has marginal threshold margins, and the battery's higher internal impedance or lower voltage shifts the operating point. If the button uses an internal pull-up in the microcontroller, the pull-up value can be weak (typically 30–50 kΩ), and any leakage path — moisture, flux residue, or a protection diode — can pull the input below the logic threshold. On battery power, the rail may be slightly lower, narrowing the margin further.

I'd also check whether the firmware configures the button pin with an interrupt and whether the interrupt is edge-triggered or level-triggered. If it's edge-triggered, a slow press that causes the signal to hover near the threshold could produce multiple edges or missed edges. I'd capture the button signal with an oscilloscope during a press under both power conditions, looking at the actual rise/fall times and any ringing or bounce that could confuse the edge detection.

The systematic approach is to isolate whether this is a level margin problem, a timing/debounce problem, or a firmware configuration problem — and the scope measurement under both power conditions will separate those hypotheses quickly.

**Possible follow-ups:**
- What specific measurements would you take on the button input pin to distinguish between a threshold margin issue and a debounce timing issue?
- If the root cause turned out to be the internal pull-up being too weak, what design alternatives would you consider?

---

## Q3: How would you approach a failure investigation where a medical device's firmware occasionally writes corrupted data to an external EEPROM, and the corruption is always in the same address range but the data pattern varies?

**Answer:** The consistent address range is the key clue here — it suggests a systematic interaction rather than random bit flips. I'd start by examining what's different about that address range: is it near the end of a page boundary, is it in a region written by a specific code path, or does it correspond to a particular logical record?

For an external EEPROM, I'd look at the write timing and the bus activity around those addresses. A classic mechanism is that the firmware writes data while another bus master or interrupt-driven routine is also accessing the same bus, causing a corrupted transaction. If the EEPROM shares the I2C or SPI bus with other devices, I'd check whether the corruption correlates with activity on another bus device — for example, a sensor read that happens to occur during the EEPROM write.

Another angle is the write-cycle timing. EEPROMs have a write cycle time (typically 5–10 ms) during which the device ignores bus traffic. If the firmware polls the EEPROM's acknowledge bit to detect write completion, but the polling logic has a bug that causes it to proceed before the write completes, the next write could be corrupted. The fact that the corruption is in the same address range might mean that particular record is written more frequently or at a specific point in the operational cycle.

I'd also examine the power supply during writes. EEPROM writes draw more current than reads, and if the supply has marginal decoupling, a write could cause a glitch that corrupts the data. I'd probe the supply rail and the bus lines simultaneously during a write to that address range, looking for any anomalies.

The investigation should also include a review of the firmware's write sequence: does it check the write-protect pin, does it verify data after writing, and does it handle the case where a write is interrupted by a reset or power loss?

**Possible follow-ups:**
- How would you determine whether the corruption happens during the write operation itself or during a subsequent read?
- What fault-injection techniques would you use to reproduce the corruption in a controlled environment?

---

## Q4: You're leading a cross-functional investigation where a medical device's firmware and hardware teams disagree on the root cause of an intermittent failure. The device occasionally fails to complete a sensor read within the required time window, and the sensor occasionally returns stale data. The firmware team believes the hardware has a timing issue — the sensor's clock is slow or the data line has excessive capacitance. The hardware team believes the firmware is not handling the sensor's timing requirements correctly. How would you handle this situation and structure the investigation?

**Answer:** The first thing I'd do is reframe the discussion from "whose fault is it" to "what is the actual failure mechanism." The disagreement itself is a symptom of insufficient data — both teams are working from hypotheses rather than measurements. I'd structure the investigation around gathering objective evidence that either confirms or eliminates each hypothesis.

I'd start by defining the exact failure criteria: what does "fails to complete a sensor read within the required time window" mean in measurable terms? What is the required window, and what is the actual timing when the failure occurs? I'd ask the firmware team to instrument the code to log precise timestamps of each step in the read sequence — when the read is initiated, when the sensor responds, and when the data is considered complete. I'd ask the hardware team to characterize the sensor's actual timing parameters — the clock frequency, rise/fall times on the data line, and the sensor's specified read time — under the conditions where the failure occurs.

The key is to get both teams to agree on what data would be conclusive. For example, if the firmware logs show that the sensor's response time is consistently within specification but the firmware is waiting longer than necessary due to a timeout setting, that points to a firmware issue. If the logs show the sensor's response time is occasionally outside its datasheet specification, that points to a hardware or sensor issue.

I'd also look for a way to reproduce the failure in a controlled environment where both teams can observe the behavior together. A logic analyzer capturing the bus traffic during a failure would show exactly what happened — whether the sensor was slow to respond, whether the clock had glitches, or whether the firmware aborted the read prematurely.

Throughout this, I'd keep the focus on the evidence rather than opinions. If the evidence is inconclusive, I'd design experiments to gather more data rather than allowing the investigation to stall in disagreement. The goal is to reach a root cause that both teams can agree on because the data supports it, not because one team "won" the argument.

**Possible follow-ups:**
- How would you handle the situation if the evidence clearly points to one team's area, but that team continues to resist the conclusion?
- What role would the sensor manufacturer's datasheet play in resolving this disagreement, and how would you handle conflicting interpretations of the datasheet?

---

## Q5: How would you approach a failure investigation where a medical device's battery life has degraded significantly in the field — devices that should last 7 days on a charge are now lasting only 3–4 days after about a year of use — and the battery management system logs show normal charge/discharge cycles with no overvoltage, overcurrent, or overtemperature events?

**Answer:** This pattern — normal BMS logs but accelerated capacity loss — suggests the degradation mechanism isn't a single dramatic event but a chronic condition that the BMS isn't monitoring. I'd start by distinguishing between two possibilities: the battery cells are genuinely degrading faster than expected, or the device's power consumption has increased over time.

The first step would be to measure the actual current draw of a returned device and compare it to the design specification. If the device is drawing more current than it should — due to a firmware issue, a component that has drifted, or a peripheral that's not entering sleep mode — then the battery isn't the problem; the load is. I'd use a power analyzer or a precision shunt to profile the current draw across all operating modes: active, idle, sleep, and during wireless communication.

If the current draw is within specification, then the issue is with the battery itself. I'd look at the battery's internal resistance and capacity through a controlled discharge test. A battery that has degraded prematurely often shows increased internal resistance, which can cause the voltage to sag under load and trigger the device's low-battery threshold earlier even though the remaining capacity is adequate.

I'd also examine the charging profile. The BMS logs show normal charge cycles, but I'd want to verify the actual charge termination voltage and current. If the charger is slightly overcharging — even within the BMS's tolerance — it can accelerate capacity loss over a year of daily cycles. Similarly, if the device is frequently charged to 100% and deeply discharged, that's a more stressful cycle profile than a partial charge/discharge pattern.

The investigation should also consider environmental factors. If the device is used in a warm environment — near a patient's body, for example — the elevated temperature accelerates chemical degradation in lithium-ion cells. I'd check whether the field usage patterns correlate with higher ambient temperatures.

Finally, I'd compare the returned devices' battery performance against a control group that was stored rather than used. This helps separate normal calendar aging from cycle-induced degradation.

**Possible follow-ups:**
- How would you determine whether the accelerated degradation is due to the charging profile versus the discharge pattern?
- What changes would you consider to the battery management system or the device's power architecture to extend battery life in the field?