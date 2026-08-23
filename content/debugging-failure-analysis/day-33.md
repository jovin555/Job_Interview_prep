# debugging-failure-analysis — Day 33

## Q1: How would you approach a failure investigation where a medical device's analog front-end produces accurate readings on the bench, but shows a consistent offset error when connected to the patient cable — and the offset varies between different cable samples?

**Answer:** This is a classic interface-dependent failure that points to something about the cable connection itself rather than the analog front-end's core circuitry. My approach would start with characterizing the offset systematically across multiple cable samples to understand its distribution — is it proportional to cable length, connector type, or shielding configuration?

The most likely culprits fall into a few categories. First, I'd check for ground offset or ground loop issues — if the patient cable introduces a different ground path than the bench setup, even a small ground potential difference can create a consistent offset. I'd measure the ground voltage difference between the device's reference and the cable's shield or patient-side ground.

Second, I'd look at input bias current paths. If the analog front-end has high-impedance inputs, the cable's conductor resistance, connector contact resistance, or even moisture absorption in the cable insulation can create voltage drops that appear as offset. Different cable samples with slightly different contact resistance or conductor quality would explain the sample-to-sample variation.

Third, I'd examine the cable's shielding and guard drive configuration. If the front-end uses a driven guard or shield, a broken or high-resistance shield connection in some cables would degrade the guard effectiveness and change the effective input capacitance or leakage path, producing offset.

My systematic approach would be: measure the offset with multiple cables and correlate it with measured cable parameters (resistance, capacitance, shield continuity); inject a known signal through each cable to isolate whether the error is in the cable or the front-end's interaction with it; and test with a cable simulator that lets me vary individual parameters independently. I'd also check whether the offset changes with cable flexing or temperature, which would point to intermittent contact issues.

**Possible follow-ups:** How would you distinguish between an offset caused by the cable's series resistance versus one caused by leakage current between conductors? What measurements would you take on the cable itself before modifying the front-end design?

---

## Q2: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a frustrating class of bug because the obvious checks pass — the addresses are valid, the lengths are within bounds, yet the copy still faults. I'd approach this by questioning the assumption that the fault is actually caused by the memory copy operation itself, rather than being merely where the fault is detected.

First, I'd consider whether the fault is a bus fault rather than a memory protection fault. The stack trace pointing to a memory copy could mean the CPU is trying to access memory that's valid in the logical address space but not physically present or not accessible at that moment. For example, if the copy is accessing memory-mapped peripherals or external memory that's temporarily powered down or in a low-power state, the bus transaction could fault even though the address "looks" valid.

Second, I'd examine whether the fault is actually a stack overflow or stack corruption that manifests at the copy operation. If the stack pointer is corrupted, the fault handler's stack trace could be misleading — the copy operation might be innocent, and the real issue is that the stack was already corrupted before the copy started. I'd check the stack pointer value at the fault, compare it to the stack boundaries, and look for evidence of stack overflow in the preceding code.

Third, I'd look at alignment issues. Some architectures require aligned accesses for certain operations, and a misaligned copy source or destination could trigger a fault. The compiler might be generating an unaligned word access that the hardware doesn't support, even though the byte-level addresses appear valid.

Fourth, I'd consider whether the fault is actually an undefined instruction or similar — if the code memory is corrupted, the "memory copy" the stack trace points to might not actually be executing the intended instructions. I'd verify the code integrity at that location and check whether the program counter is actually within the expected function.

My systematic approach would be: capture the full fault status register contents (not just the stack trace), examine the actual faulting address from the hardware registers, verify the stack integrity, and reproduce with fault injection to test hypotheses about which memory region or access type triggers the fault.

**Possible follow-ups:** How would you use the fault status registers to narrow down whether this is a bus fault, memory management fault, or usage fault? What instrumentation would you add to the firmware to capture more context around the fault?

---

## Q3: How would you approach debugging a medical device where the failure occurs only when the device is connected to a specific accessory cable, but never when using the test harness on the bench?

**Answer:** This is a strong signal that the accessory cable is introducing something the test harness doesn't — and the key is to characterize what's different about that cable. My approach would start with a detailed electrical characterization of the suspect cable compared to the test harness.

First, I'd measure the cable's pin-to-pin continuity, isolation between adjacent pins, shield continuity, and connector contact resistance. I'd also check for intermittent connections by flexing the cable while measuring. A marginal connection that works at rest but fails under slight movement or temperature change would explain why the failure is specific to that cable.

Second, I'd look at the cable's electrical characteristics beyond simple continuity — capacitance between conductors, leakage resistance, and whether the cable introduces any unexpected coupling between signals. A cable with damaged insulation or moisture ingress could create leakage paths that load down signals or create crosstalk.

Third, I'd consider whether the cable is introducing a ground path difference. If the accessory cable connects the device to another piece of equipment, it could create a ground loop or a different ground reference than the bench setup. This could cause common-mode voltages, offset errors, or even latch-up conditions in interface circuits.

Fourth, I'd examine the cable's connector and whether it's making proper contact with the device's connector. A slightly bent pin, worn contact, or debris in the connector could cause marginal contact that works intermittently. I'd inspect both connectors under magnification and check contact resistance under different insertion depths and angles.

My systematic approach would be: reproduce the failure with the suspect cable while monitoring key signals (power rails, communication lines, sensor inputs) with an oscilloscope; compare those waveforms against the same measurements with the test harness; and then progressively modify the cable (shorten it, replace the connector, bypass sections) to isolate which part of the cable is responsible.

**Possible follow-ups:** What specific measurements would you take on the cable before connecting it to the device? How would you determine whether the issue is in the cable itself or in the device's connector interface?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that suggests the device's charging circuit is interacting with something specific about that third-party charger. My approach would start with electrical characterization of both chargers to understand what's different.

First, I'd measure the suspect charger's output characteristics: voltage accuracy, ripple, transient response, and — critically — its current limiting behavior. Some USB chargers have aggressive current limiting or fold-back behavior that can interact poorly with a device's inrush current or charging profile. I'd also check whether the suspect charger is actually USB-compliant in its handshake behavior — some chargers misidentify their current capability or use non-standard signaling on the D+/D- lines.

Second, I'd look at the charging circuit's input stage. If the device uses a switching charger with an input current limit, the interaction between the charger's output impedance and the device's input capacitance could cause oscillation or excessive current draw during startup. I'd measure the input current waveform at power-on and during charging with both chargers to see where the difference appears.

Third, I'd consider whether the suspect charger has a different ground or isolation configuration. Some cheap chargers have significant leakage current from their internal EMI filtering, which can create a path through the device that increases apparent current draw. I'd measure the leakage current and common-mode voltage of both chargers.

Fourth, I'd check whether the suspect charger's output voltage is higher than expected, which could push the charging circuit into an abnormal operating mode. A charger that outputs 5.5V instead of 5.0V could cause the input current limit to engage differently or stress the charging IC.

My systematic approach would be: characterize both chargers on a bench with a programmable electronic load; measure the device's input current profile with both chargers; and then test with a variable power supply to find the voltage/current conditions that trigger the excessive current draw. I'd also check the charging IC's datasheet for known compatibility issues and verify that the device's input protection circuitry (if any) is behaving correctly.

**Possible follow-ups:** How would you determine whether the issue is a charger problem, a device problem, or an interaction problem? What safety considerations would you keep in mind when testing with a non-compliant charger?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure investigation, because experience is valuable but can also create blind spots. My approach would focus on respecting the engineer's expertise while maintaining the integrity of the investigation process.

First, I'd acknowledge the engineer's hypothesis and take it seriously — their experience with a similar device is genuinely useful and might be correct. I'd ask them to walk me through the evidence that supports their hypothesis and how it maps to the current failure. This isn't just about being diplomatic; it's about making sure I haven't missed something they've seen.

Second, I'd frame the discussion around evidence rather than opinions. I'd ask what specific data would confirm their hypothesis, and what data would refute it. If their hypothesis is correct, there should be a way to test it that doesn't require a full design change. I'd propose a focused experiment or measurement that would either strengthen or weaken their case before committing to a fix.

Third, I'd explain the risk of implementing a fix before root cause is confirmed — in a medical device context, this isn't just about engineering rigor, it's about patient safety and regulatory compliance. A fix based on an unconfirmed hypothesis could introduce new failure modes, and if the actual root cause remains, the failure will recur. I'd frame this as a shared risk rather than a challenge to their judgment.

Fourth, I'd look for a way to parallelize the work. If the engineer's proposed fix is low-risk and reversible, we could potentially implement it as a containment action while the investigation continues. This respects their urgency while maintaining the discipline of confirming root cause before final corrective action. However, I'd be clear that a containment action is not the same as a root cause fix.

If the engineer continues to push, I'd escalate the discussion to the data — I'd propose a structured comparison of their hypothesis against the evidence, and I'd involve other team members in reviewing the analysis. The goal is to create a process where the best-supported hypothesis wins, not the most senior person.

**Possible follow-ups:** What if the engineer's proposed fix is the only one that can meet the project timeline — how would you balance speed against investigation rigor? How would you document this disagreement in the investigation record for regulatory purposes?