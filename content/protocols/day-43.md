# protocols — Day 43

## Q1: How would you approach designing a USB 2.0 device that must support both remote wakeup and selective suspend, where the device needs to wake the host when a patient alarm condition occurs while the host is in suspend mode?

**Answer:** I'd start by treating this as two distinct problems: enumeration-time capability declaration and runtime power management behavior. During enumeration, the device descriptor must set the remote wakeup bit in the configuration descriptor's bmAttributes field, and the device must properly handle the SET_FEATURE(DEVICE_REMOTE_WAKEUP) standard request from the host — some hosts enable it, some don't, and the device should track whether it has been granted permission to wake the host.

For the firmware architecture, I'd structure the application around three power states: fully active, suspended (device has detected suspend via lack of SOF frames or the suspend signal on the bus), and an intermediate "armed" state where the device is suspended but monitoring the alarm input. The key design decision is what can wake the device from suspend. In a medical device, the alarm condition must be able to wake the device's own microcontroller, not just the host — so the alarm input needs to be routed to an interrupt-capable GPIO or a wake-up source on the MCU, not polled.

When the alarm fires while suspended, the firmware must first resume its own clock and stabilize power, then assert remote wakeup on the bus by driving the D+ line according to the USB signaling specification. There's a timing constraint here: the device must signal resume within a specific window after detecting the alarm, and the resume signaling duration must meet the specification. After the host acknowledges the resume, the device re-enters the active state and can send the alarm notification via an interrupt or bulk endpoint.

A subtle point is handling the case where the host does not grant remote wakeup permission. The device still needs to ensure the alarm is eventually communicated — perhaps by resuming operation locally, illuminating an indicator, or storing the alarm event until the host next polls. The design should never rely solely on remote wakeup succeeding, because some hosts disable it by policy.

**Possible follow-ups:**
- How would you test remote wakeup behavior across different host controllers and operating systems, given that some are more lenient than others in their suspend timing?
- What happens if the device needs to wake the host but the USB cable has been disconnected or the host has been powered off entirely — how does the alarm get communicated?

---

## Q2: You're debugging a system where a UART link between a microcontroller and a wireless module occasionally drops the first few bytes of a transmission after the system has been idle for several minutes. The link uses hardware flow control (RTS/CTS). How would you approach this?

**Answer:** This pattern — data loss after idle periods with hardware flow control — often points to a handshake timing issue rather than a baud rate or signal integrity problem. I'd approach it systematically.

First, I'd capture the actual signals on a logic analyzer or oscilloscope, triggering on the first byte after idle. I want to see the relationship between the transmitter asserting RTS, the receiver asserting CTS, and the actual data on TX/RX lines. A common failure is that the receiver's firmware deasserts RTS (indicating "not ready") when its receive buffer is empty or when it enters a low-power state during idle, then reasserts it slightly too late when the transmitter has already begun sending. The transmitter sees CTS deasserted, holds off, but if the timing of the re-assertion is marginal relative to the transmitter's polling interval, the first bytes can be lost.

Another angle is the wireless module's own power management. Many radio modules enter a low-power sleep state after inactivity, and their UART interface may not be fully ready the instant the host begins transmitting. The module might need a wake-up preamble or a specific assertion sequence on RTS before it can receive data reliably. If the microcontroller doesn't account for this wake-up latency, the first bytes can be transmitted into a module that isn't listening yet.

I'd also check the flow control polarity and whether both sides agree on the meaning of asserted/deasserted RTS/CTS. Some devices use active-low with pull-ups, and a misconfiguration in firmware — for example, configuring the pin as active-high — can cause intermittent failures that only appear after idle when line states have settled differently.

The fix might involve adding a small delay after asserting RTS before sending data, implementing a "wake-up byte" or break condition to rouse the module, or reworking the flow control state machine to ensure the receiver asserts ready well before it can accept data.

**Possible follow-ups:**
- How would you distinguish between a firmware handshake timing issue and an electrical issue like line capacitance or missing pull-ups on the RTS/CTS lines?
- If the wireless module's datasheet specifies a wake-up time from sleep, how would you incorporate that into the protocol design?

---

## Q3: How would you approach selecting between a daisy-chain SPI configuration and independent chip selects for connecting multiple sensors in a medical device where PCB space is limited, but the sensors have different clock polarity and phase requirements?

**Answer:** This is a classic trade-off between hardware simplicity and protocol flexibility. Independent chip selects give you the freedom to reconfigure the SPI peripheral's clock polarity (CPOL) and phase (CPHA) for each slave transaction — you can change the mode between chip select assertions. Daisy-chain configuration, by contrast, typically requires all slaves to share the same clock mode because they're all clocked simultaneously through a shift-register chain.

In a medical device context, I'd first ask whether the sensors genuinely need different SPI modes or whether the requirement is only in the datasheet and the sensors would actually work in a common mode. Some sensors are flexible about CPOL/CPHA within certain limits, and testing might reveal that a single mode works for all. If they truly require different modes, daisy-chain is essentially ruled out unless you're willing to insert a hardware translation layer, which defeats the space savings.

If independent chip selects are needed, the PCB space concern becomes a question of how many GPIOs are available and whether the routing can be managed. One technique is to use a GPIO expander over I2C to generate chip selects, though that adds latency and a dependency on another bus. Another option is to use a demultiplexer to select among multiple slaves with fewer GPIOs, at the cost of an extra chip.

There's also a middle path: group sensors by SPI mode compatibility. If two sensors share the same mode, they can share a chip select in a daisy-chain or multi-drop arrangement, while sensors with different modes get their own chip selects. This hybrid approach can reduce GPIO usage without forcing all devices into a single mode.

For a medical device, I'd also consider the failure modes. With independent chip selects, a fault in one sensor's chip select line is isolated to that sensor. In a daisy chain, a single break in the chain can corrupt communication with all downstream devices, which complicates fault diagnosis and recovery — a significant consideration for a device where reliability is paramount.

**Possible follow-ups:**
- How would you handle the situation where one sensor in a daisy chain needs to be replaced in the field — does the chain design complicate serviceability?
- If you determined that a hybrid approach was needed, how would you document the grouping rationale in the design specification for future maintainers?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single I2C bus at 400 kHz with clock stretching enabled to connect a real-time pressure sensor and a high-volume data logger in a medical device. The pressure sensor requires deterministic read intervals, and the data logger can stretch the clock for up to 5 milliseconds during writes. How would you guide the team to evaluate this approach?

**Answer:** I'd frame this around the fundamental tension between I2C's shared-bus arbitration and the pressure sensor's determinism requirement. The data logger's 5-millisecond clock stretch is the critical constraint — during that stretch, the entire bus is held, and no other device can communicate. If the pressure sensor needs reads at a fixed interval, say every 10 milliseconds, a 5-millisecond stretch consumes half the available window and could cause the pressure read to be delayed past its deadline.

The first step in the review would be to quantify the actual timing budget. I'd ask the engineer to map out the worst-case bus occupancy: the data logger's write time including the stretch, the pressure sensor's read time, and any overhead for address arbitration and STOP/START conditions. If the worst-case total exceeds the pressure sensor's allowable read latency, the single-bus approach fails the determinism requirement regardless of how well the protocol is implemented.

I'd also probe whether the data logger's clock stretching is truly unavoidable or a configuration choice. Some devices stretch the clock because their internal write cycle is slow, but they may have a "no-stretch" mode or a smaller page size that reduces the stretch duration. If the stretch can be bounded to a shorter time, the single-bus approach might become viable.

If the timing doesn't work, I'd guide the team toward alternatives: separate buses for the two devices, using the data logger's write-complete polling instead of clock stretching, or moving the data logger to SPI where it can't stall other traffic. The key teaching point is that protocol selection must be driven by the worst-case timing analysis, not by the average case or by the convenience of a single bus.

Finally, I'd emphasize that in a medical device, this analysis should be documented as part of the design rationale — showing that the bus architecture meets the determinism requirement under all specified operating conditions, including the data logger's maximum stretch duration.

**Possible follow-ups:**
- How would you verify the worst-case timing analysis in practice, given that clock stretching duration can vary with temperature and data patterns?
- If the pressure sensor's read interval could be made adaptive — for example, skipping a read if the bus is busy — would that change your assessment of the single-bus approach?

---

## Q5: How would you approach developing a test strategy for verifying that a medical device's communication interfaces remain reliable over extended operation, given that intermittent failures often only appear after hours or days of continuous use?

**Answer:** I'd structure this as a multi-layered strategy combining accelerated testing, targeted stress conditions, and systematic fault injection — all documented in a way that supports the regulatory submission.

The first layer is long-duration soak testing with comprehensive logging. The device runs its normal communication patterns continuously — sensor reads, data logging, periodic transmissions — while a test harness monitors for errors at multiple levels: protocol-level errors (NACKs, framing errors, CRC failures), application-level errors (missing data, out-of-order packets, stale values), and electrical-level anomalies. The key is that the test harness must detect and log errors automatically, not just record raw traffic for later analysis. I'd also vary the environmental conditions during soak testing — temperature cycling, humidity, supply voltage variation — because intermittent failures in medical devices often correlate with environmental stress.

The second layer is targeted stress testing that accelerates specific failure mechanisms. For I2C, this might mean operating at maximum bus capacitance or marginal pull-up values. For UART, it could mean testing at the edges of the baud rate tolerance or with injected clock jitter. For RS-485, it might involve common-mode noise injection or marginal termination. The goal is to find the conditions where the interface begins to fail, so you understand the margin between normal operation and failure — not just to confirm that it works under nominal conditions.

The third layer is fault injection. I'd systematically introduce faults — bus contention, missing acknowledgments, corrupted frames, power glitches — and verify that the device's error handling and recovery mechanisms work as designed. This is particularly important for medical devices where the communication failure itself may not be the hazard, but the device's response to the failure could be. For example, if a sensor read fails, does the device default to a safe state or does it continue with stale data?

Throughout this, I'd maintain a traceability matrix linking each test to the specific requirement it verifies — whether that's a protocol timing requirement, a data integrity requirement, or a fault recovery requirement. For regulatory submission, the test plan, procedures, and results need to demonstrate that the communication design is robust under both normal and fault conditions.

**Possible follow-ups:**
- How would you decide when a device has been tested "enough" — what criteria would you use to determine that the soak testing duration is adequate?
- If a failure appears only after 72 hours of continuous operation, how would you go about isolating whether it's a communication protocol issue, a firmware memory leak, or a hardware degradation issue?