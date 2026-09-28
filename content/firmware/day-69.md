# firmware — Day 69

## Q1: How would you approach implementing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?
**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the resulting CPU utilization. If the ISR is consuming a large fraction of the CPU, the system has no headroom for anything else, and the design needs to change rather than be micro-optimized.

The core strategy is to make the ISR do the absolute minimum and defer everything else. In the ISR, I would only capture the essential data — typically reading a data register into a buffer and clearing the interrupt flag — and then signal a deferred context (a thread, work queue, or bottom-half) to do the processing. This keeps ISR latency bounded and predictable.

If the interrupt rate is genuinely too high for per-event servicing, I would look at hardware offload. DMA is the natural answer: configure the peripheral to write directly into a circular buffer in memory, and have the DMA controller generate an interrupt only on a half-buffer or full-buffer boundary rather than per sample. That reduces the interrupt rate by the buffer granularity — often by one or two orders of magnitude — while still giving timely access to the data.

Where DMA isn't available or suitable, I would consider batching in the ISR itself: instead of one interrupt per byte, read multiple bytes per interrupt if the peripheral supports a FIFO, or use a timer-driven polling scheme at a known rate if the data rate is deterministic. The trade-off is latency versus CPU load, and that has to be evaluated against the system's real-time requirements.

Finally, I would verify the design under worst-case conditions, not just nominal. Interrupt storms often only manifest when the system is also doing something else — a flash write, a wireless transmission — so the timing budget has to account for the whole system, not just the peripheral in isolation.

**Possible follow-ups:**
- How would you decide between DMA and a larger FIFO with a lower interrupt rate?
- What would you do if the deferred context itself can't keep up with the rate the ISR is producing data?

## Q2: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?
**Answer:** A brownout is a particularly nasty failure mode because the MCU may continue executing while its supply is out of spec, which means it can behave unpredictably — flash writes may partially complete, RAM contents may become unreliable, and the core may execute instructions incorrectly. The design has to assume that any code running during the sag is untrustworthy.

The first line of defense is hardware-assisted detection. Most modern MCUs have a brownout detector (BOD) or supply voltage monitor that can generate an interrupt or reset before the supply drops below the level at which the core is guaranteed to operate correctly. I would configure the BOD threshold with margin above the MCU's minimum operating voltage, and decide whether the response should be an interrupt (to allow a graceful shutdown) or a reset (to guarantee a clean restart). For a device with persistent state, an interrupt-driven graceful shutdown is usually preferable, but only if the shutdown path itself can complete before the supply falls further.

The second line of defense is the persistent state design. Any critical state written to flash or EEPROM should be written in a way that is atomic from the perspective of a reader — typically a two-phase commit with a checksum or a journaling scheme. If a write is interrupted mid-way, the reader must be able to detect the incomplete write and fall back to the previous valid state. This is the same principle as surviving a power loss mid-write, and it should be designed in from the start rather than bolted on.

The third consideration is what the device does after the brownout. If the supply recovers and the device is still running, it needs to re-validate its state and re-initialize any peripherals that may have been affected. If the BOD triggered a reset, the startup code needs to distinguish a brownout reset from a power-on reset and handle it appropriately — for example, by logging the event and re-validating persistent state before resuming normal operation.

**Possible follow-ups:**
- How would you test a brownout response without a programmable power supply?
- What's the difference between a brownout detector and a power-on reset, and when would you use each?

## Q3: You're debugging a firmware issue where a device's behavior is correct when powered from a bench supply but intermittently wrong when powered from a battery, and the wrong behavior correlates with the device transmitting wirelessly. How would you approach this?
**Answer:** The correlation with wireless transmission is the key clue — it points to a supply-related problem rather than a logic bug. Wireless transmitters draw current in short, high-amplitude bursts, and if the supply impedance is too high or the decoupling is inadequate, that burst can cause a local voltage droop that affects other parts of the system.

I would start by measuring the supply rail at the point of load, not at the battery terminals. A bench supply typically has very low output impedance and good regulation, which masks the problem; a battery has higher impedance, and the trace or connector between the battery and the MCU adds more. An oscilloscope with a short ground lead, triggered on the wireless transmit event, would show whether the rail is drooping during transmission and by how much.

If the droop is confirmed, the fix is usually in the power delivery network: adding bulk capacitance close to the load, reducing trace impedance, or improving the regulator's transient response. But I would also check whether the problem is actually a droop or a noise coupling issue — the wireless transmitter can also radiate or conduct noise back into sensitive analog or digital circuits, and that requires a different fix (shielding, filtering, layout changes).

On the firmware side, I would look at whether the device's behavior during transmission is timing-sensitive. If the firmware is doing something like reading an ADC or writing to flash at the same time as the transmit burst, and the supply is marginal, the failure may be in that concurrent operation rather than in the wireless stack itself. Adding a guard time around the transmit event, or deferring sensitive operations until after the burst, can sometimes work around the issue — but that's a mitigation, not a root-cause fix, and I would want to understand the underlying supply problem before relying on it.

**Possible follow-ups:**
- How would you distinguish between a supply droop and radiated noise as the root cause?
- What firmware-side mitigations would you consider if the hardware fix is not possible in the short term?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?
**Answer:** The guiding principle is that the bootloader should be as small, simple, and stable as possible, because it's the one piece of code that must work correctly for the device to be recoverable. Anything that can change over the product's lifetime — features, communication protocols, user interfaces — belongs in the application, not the bootloader.

Concretely, the bootloader's responsibilities are: verifying the integrity of the application image before booting it, selecting which image to boot (in a dual-bank scheme), performing the actual image copy or swap if required, and providing a minimal recovery path if the application is invalid. It should not contain business logic, sensor drivers, or anything that would need to be updated when the product's functionality changes.

The application's responsibilities include the update protocol itself — receiving the new image over whatever transport is used, validating it, and writing it to the inactive bank. This is a deliberate split: the application has the full communication stack and can be updated to support new transports or protocols, while the bootloader only needs to know how to verify and boot an image.

The boundary cases are the interesting ones. For example, should the bootloader handle the "enter update mode" trigger, or should the application? If the trigger is a button press at power-on, the bootloader has to handle it because the application isn't running yet. If the trigger is a command over a communication interface, the application can handle it and then hand off to the bootloader. The decision depends on what recovery paths need to work even if the application is corrupt.

Another boundary case is the rollback logic. The bootloader has to make the final decision about which bank to boot, but the criteria for that decision — how many boot attempts, what validation checks — are often best defined by the application team and then implemented in the bootloader. That requires a clear interface between the two, usually a small shared region of flash or a set of flags that both sides agree on.

**Possible follow-ups:**
- How would you handle a situation where the bootloader itself needs to be updated?
- What's the minimum set of validation checks the bootloader should perform before booting an image?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?
**Answer:** I would start by acknowledging what they got right: `volatile` does prevent the compiler from caching the variable in a register or optimizing away what looks like a redundant read, and for a single flag that's written by an ISR and read by a thread, that's a necessary condition. The problem is that it's not a sufficient condition, and the gap between "necessary" and "sufficient" is where the bugs live.

The first issue is atomicity. `volatile` says nothing about whether a read or write is atomic. For a single-byte flag on most architectures, the access is atomic, but for anything wider — a 16-bit or 32-bit value on an 8-bit or 16-bit MCU — the compiler may generate multiple instructions, and an interrupt can occur between them. If the ISR writes a multi-byte value while the thread is reading it, the thread can see a torn value. The fix is to either use a type that's guaranteed atomic on the target, or to protect the access with a critical section.

The second issue is ordering. `volatile` does not prevent the compiler or the CPU from reordering other memory accesses around the volatile access. If the ISR writes data to a buffer and then sets a flag, and the thread reads the flag and then reads the buffer, the compiler is free to reorder the thread's reads — and on a CPU with a weak memory model, the hardware can reorder them too. The result is that the thread can see the flag set before the data is actually visible. The fix is a memory barrier or, more practically, a synchronization primitive that provides the right ordering guarantees.

The third issue is that `volatile` doesn't compose. If the module grows to have multiple flags, or a flag plus a counter, the ad-hoc approach becomes unmaintainable and the bugs become harder to reason about. The right long-term answer is to use the RTOS's synchronization primitives — a semaphore, a message queue, or an atomic type — which are designed for exactly this purpose and provide the atomicity and ordering guarantees that `volatile` alone does not.

I would frame this as a teaching opportunity rather than a correction: the goal is for the junior engineer to understand *why* `volatile` is insufficient, not just to be told to use something else. I'd walk through a concrete scenario — a multi-byte value, or a buffer-plus-flag — and show how the code can fail even though `volatile` is present. Once they see the failure mode, the fix is usually obvious to them.

**Possible follow-ups:**
- What's the difference between `volatile` and `_Atomic` in C11, and when would you use each?
- How would you test for a torn read or a reordering bug that only manifests under specific timing conditions?