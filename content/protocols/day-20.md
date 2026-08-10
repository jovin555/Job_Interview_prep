# protocols — Day 20

## Q1: How would you approach designing a mixed-signal PCB layout where a high-speed digital bus (e.g., SPI at 10+ MHz) runs parallel to a sensitive analog sensor front-end on the same board, and you're concerned about crosstalk and noise coupling?

**Answer:** I'd approach this as a partitioning and isolation problem from the very start of the layout, not as something to fix after the fact. The first step is a clear physical separation of the board into analog and digital zones, with the analog front-end placed as far as practical from the high-speed digital traces. I'd establish a solid ground plane and think carefully about how return currents flow — the key principle is that every signal trace's return current wants to flow directly beneath it, so I'd avoid routing digital traces over or near analog circuitry where their return currents could couple into sensitive nodes.

For the SPI bus specifically, I'd keep the traces short and use series termination resistors near the driver to reduce ringing and high-frequency harmonics. I'd also consider slowing down the edge rate if the protocol allows — sometimes a slightly slower rise time dramatically reduces radiated emissions and crosstalk without affecting throughput. Guard traces with ground vias between the digital bus and analog section can help, though a solid ground plane with proper separation is usually more effective.

On the analog side, I'd pay attention to where the sensor's output traces enter the ADC or amplifier. Keeping those traces short, shielding them with ground on both sides, and ensuring the analog ground reference is clean are all important. I'd also think about the power distribution — separate analog and digital supply rails with proper filtering, and careful placement of decoupling capacitors so digital switching currents don't modulate the analog supply.

Finally, I'd verify the design with a pre-layout signal integrity analysis if tools are available, and always do a post-layout review checking for potential coupling paths. In a medical device context, this kind of care is especially important because the consequences of noise on a sensor reading aren't just a performance issue — they could affect clinical decisions.

**Possible follow-ups:** How would you decide whether to use a split ground plane or a single solid ground plane? What specific measurements would you take during bring-up to verify that crosstalk is within acceptable limits?

---

## Q2: How would you approach implementing a firmware watchdog strategy for a medical device that uses multiple communication interfaces (I2C, SPI, UART) and must never leave a sensor in an unknown state, even if the main application task hangs?

**Answer:** I'd design a layered watchdog strategy rather than relying on a single mechanism. At the hardware level, I'd use the microcontroller's built-in watchdog timer (WDT) as the last line of defense — it should be configured with a timeout that's long enough to avoid false triggers during normal operation but short enough to catch a genuine hang. The key is that the WDT should be kicked by a low-level task or interrupt, not by the main application loop, so that a hang in the application logic still gets caught.

Above that, I'd implement a software watchdog or health-monitoring task that tracks the state of each communication interface. For example, each protocol driver could maintain a "last successful transaction" timestamp, and a supervisory task periodically checks that all interfaces have been active within expected timeframes. If an interface hasn't completed a transaction within its expected window, the supervisory task can attempt a recovery sequence — resetting the peripheral, re-initializing the bus, or putting the sensor into a known safe state.

For the "unknown state" concern specifically, I'd design each sensor driver to have explicit state management. Before any transaction, the driver knows what state the sensor should be in; if a transaction fails or times out, the driver transitions the sensor to a defined safe state rather than leaving it indeterminate. This might mean de-asserting chip selects, releasing the I2C bus, or sending a specific reset command to the sensor.

In a Zephyr RTOS context, I'd use the kernel's built-in watchdog subsystem and potentially a separate monitoring thread with a lower priority than the communication tasks. The monitoring thread would check health flags set by each driver and take corrective action. I'd also make sure that any recovery action is logged for later analysis, since intermittent hangs often have root causes that only become clear when you can correlate them with other events.

**Possible follow-ups:** How would you choose the watchdog timeout values to avoid false triggers during normal operation? What recovery actions would you consider safe for a medical device, and how would you decide between resetting just the sensor versus resetting the entire system?

---

## Q3: You're debugging a system where a sensor on an SPI bus communicates correctly at 1 MHz but produces corrupted data at 8 MHz, even though the sensor datasheet specifies operation up to 10 MHz. The PCB traces are approximately 5 centimeters long. How would you approach this?

**Answer:** I'd start by recognizing that the datasheet's 10 MHz specification likely assumes ideal conditions — short traces, proper termination, and a clean clock. At 8 MHz with 5 cm traces, I'd suspect signal integrity issues rather than a fundamental sensor limitation.

First, I'd look at the signal integrity of the clock and data lines. At 8 MHz, the rise and fall times of the signals become significant relative to the trace length. I'd check for ringing, overshoot, and undershoot using an oscilloscope at the sensor's pins. If the clock signal has excessive ringing, it could cause double-clocking or missed edges. I'd also check the MISO line — if the sensor's output driver is weak or the trace has high capacitance, the data might not settle within the setup time at higher clock rates.

Second, I'd examine the SPI mode configuration. At higher speeds, the timing margins for setup and hold times become tighter. I'd verify that the clock polarity and phase settings match what the sensor expects, and I'd check the actual timing parameters — clock high time, clock low time, data setup, and data hold — against the sensor's minimum requirements. Sometimes a sensor's maximum clock frequency assumes a specific duty cycle or edge relationship that isn't being met.

Third, I'd consider the microcontroller's SPI peripheral configuration. At higher speeds, the master's output drive strength, slew rate settings, and even the GPIO pin configuration can affect signal quality. Some microcontrollers have programmable drive strength or slew rate control that can be adjusted. I'd also check whether the SPI peripheral has any internal delays or sampling points that can be tuned.

Finally, I'd look at the physical layer — the 5 cm trace length is probably fine at 8 MHz, but I'd check for vias, connectors, or other discontinuities that could cause reflections. I'd also verify the ground return path between the microcontroller and sensor; a poor ground connection can cause ground bounce that corrupts data at higher speeds.

If signal integrity checks out, I'd then suspect the sensor's internal timing — perhaps it needs a longer inter-frame delay or has a minimum CS high time that isn't being met at higher clock rates. I'd review the sensor's timing diagrams carefully and potentially add small delays in firmware to ensure all timing requirements are satisfied.

**Possible follow-ups:** How would you determine whether the issue is signal integrity versus the sensor's internal timing? What specific oscilloscope measurements would you take to differentiate between these causes?

---

## Q4: How would you approach designing a communication architecture for a medical device where a central controller needs to communicate with multiple sensor modules, some requiring deterministic real-time response and others generating high-volume data, while keeping the system modular and testable?

**Answer:** I'd start by clearly separating the requirements for each communication path. The deterministic real-time sensors have fundamentally different needs than the high-volume data sensors — different latency budgets, different data sizes, and different failure consequences. Trying to force them onto a single bus with a single protocol usually ends up compromising one requirement to satisfy another.

My approach would be to categorize each sensor by its communication profile: latency-critical, throughput-critical, or neither. For latency-critical sensors, I'd consider a dedicated bus or a protocol with deterministic arbitration, like CAN-FD with proper message prioritization. For throughput-critical sensors, I'd consider a higher-bandwidth interface like SPI or USB, where the focus is on sustained data rate rather than bounded latency. For sensors that are neither, I'd use a lower-speed, lower-complexity interface like I2C.

At the architecture level, I'd design a modular abstraction layer where each sensor has a driver that presents a uniform interface to the application, regardless of the underlying transport. This is where the real testability comes in — each driver can be tested in isolation with simulated hardware, and the application logic can be tested with mock drivers. I'd also design the communication layer to be configurable, so the same firmware can support different sensor configurations without code changes.

For the deterministic requirement specifically, I'd think carefully about scheduling. In a Zephyr RTOS environment, I'd assign different priorities to different communication tasks and use synchronization primitives like mutexes and semaphores carefully to avoid priority inversion. For the high-volume data path, I'd use DMA where possible to reduce CPU load and ensure that the real-time path isn't starved.

I'd also build in observability from the start — each communication path should have diagnostic counters (messages sent, received, errors, timeouts) that can be read over a debug interface. This makes it much easier to characterize the system's behavior under real workloads and to verify that the real-time requirements are being met.

Finally, I'd think about failure modes. What happens if a sensor stops responding? What happens if the high-volume data path saturates? Each failure mode should have a defined behavior — alert, retry, or safe shutdown — and that behavior should be testable.

**Possible follow-ups:** How would you decide whether to use a single multi-protocol bus versus separate dedicated buses for different sensor types? How would you verify that the real-time requirements are actually being met under worst-case conditions?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame this as a structured decision-making exercise rather than taking sides. The first step is to clarify the actual requirements — what are the data rates, latency needs, and reliability expectations for each sensor? Without those, we're debating architecture without a basis for comparison.

I'd ask the junior engineer to walk through the multiplexer design in detail. How would the software handle different baud rates on a single UART? UART is a point-to-point protocol, so switching between sensors would require either external switching hardware or a shared bus with careful line discipline. If the sensors are on a shared bus, how would addressing work? Standard UART doesn't have addressing, so you'd need a protocol layer on top — and that protocol layer needs to handle collisions, timeouts, and the fact that sensors might not all support the same framing.

I'd also ask about the failure modes. If one sensor holds the line low or generates continuous framing errors, does that block communication with the other three? What happens during a baud rate switch — is there a risk of the line being in an indeterminate state? How would you debug a problem when you can't isolate which sensor is causing it?

Then I'd ask the hardware engineer to quantify the cost of four separate UARTs. Is it a pin count issue? Package size? Power? If the microcontroller has four UART peripherals available, the hardware cost might be minimal — just four sets of traces and connectors. If it requires a larger package or additional components, that's a real trade-off.

My guidance would be to evaluate the options against the requirements. If the sensors have genuinely different baud rates and protocols, a single UART with a multiplexer adds significant complexity and risk. The software overhead of managing the multiplexer, handling line turnaround, and debugging intermittent issues could easily exceed the cost of four separate UARTs. On the other hand, if the sensors are all low-speed and can tolerate a shared bus with a simple protocol, the multiplexer approach might be viable — but I'd want to see a detailed protocol design and a risk assessment before approving it.

I'd also suggest a middle ground: perhaps two UARTs, grouping sensors with similar characteristics, or using a different protocol entirely, like I2C or RS-485, which are designed for multi-drop operation. The decision should be based on data — throughput calculations, latency analysis, and failure mode assessment — not on preference.

**Possible follow-ups:** What specific questions would you ask the junior engineer to evaluate the robustness of the multiplexer design? How would you help the team reach a consensus if they remain divided after the analysis?