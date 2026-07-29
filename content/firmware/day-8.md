# firmware — Day 8

## Q1: You're designing a Zephyr RTOS-based system where a sensor task must read data every 10 ms, but the device also needs to enter a low-power sleep state between reads to conserve battery life. How would you structure the power management to ensure no data is missed while maximizing sleep time?

**Answer:** I'd approach this by leveraging Zephyr's power management subsystem rather than manually toggling sleep modes in application code. The key is to separate the timing concern from the power management concern.

First, I'd configure the sensor task to use a Zephyr timer or a hardware timer interrupt as its wake-up source, rather than relying on a periodic software timer that might not account for sleep entry/exit latency. The timer interrupt should be set to fire slightly before the 10 ms deadline to account for wake-up time — I'd measure the actual wake latency during bring-up and add a small margin.

For the sleep strategy, I'd use Zephyr's system power management hooks. The idle thread can automatically enter a light sleep mode (like tickless idle) between thread executions. If deeper sleep is needed, I'd implement a custom power policy that selects the appropriate sleep state based on the time until the next scheduled wake. Zephyr's `pm_policy_next_state()` callback allows this decision to be made dynamically.

The critical detail is ensuring the timer peripheral used for wake-up remains powered in the chosen sleep state. Some MCUs have a subset of timers that stay active in deep sleep — I'd verify this against the hardware reference manual and configure the power manager to only enter states where that timer remains functional.

I'd also add a guard: if the sensor task ever detects that more than 10 ms has elapsed since its last wake (indicating a missed deadline), it should log the event and potentially escalate to a higher-power mode where timing is guaranteed, rather than silently losing data.

**Possible follow-ups:**
- How would you handle the case where the sensor itself requires a warm-up or stabilization period after waking from deep sleep?
- What if the system has multiple periodic tasks with different wake intervals — how would you coordinate sleep states across them?

---

## Q2: You're debugging a firmware issue where a MicroPython script running on a constrained MCU causes a hard fault when performing string concatenation in a loop. The system has 64 KB of RAM total. How would you approach diagnosing whether this is a memory fragmentation issue, a stack overflow, or something else?

**Answer:** I'd start by ruling out the most dangerous possibility first: stack overflow. MicroPython's C stack usage can spike during string operations because it may call into the garbage collector or allocate temporary objects. I'd check the stack pointer at the point of the hard fault using the debugger, and compare it against the configured stack size for the MicroPython thread. If the remaining stack is very small (under a few hundred bytes), that's suspicious.

If stack usage looks fine, the next step is memory profiling. MicroPython's `gc.mem_free()` and `gc.mem_alloc()` functions can show overall heap state, but they don't reveal fragmentation directly. I'd add a periodic call to `gc.dump_free()` (if available) or manually inspect the heap by enabling MicroPython's heap statistics at build time. The key diagnostic is whether `gc.mem_free()` reports plenty of free memory while allocations still fail — that's the classic sign of fragmentation.

String concatenation in MicroPython is particularly problematic because `s1 + s2` creates a new string object, leaving the old ones as garbage. In a loop, this generates many short-lived allocations that fragment the heap. I'd verify this by checking whether the fault occurs at a predictable iteration count or varies with string length.

If fragmentation is confirmed, the fix is to avoid repeated concatenation in MicroPython. Options include: using `str.join()` with a list of parts (which allocates once), pre-allocating a `bytearray` and writing into it, or moving the string-building logic to a C module if performance is critical. For a quick diagnostic, I'd also try calling `gc.collect()` manually at strategic points to see if it defers the crash — that would confirm fragmentation as the root cause.

**Possible follow-ups:**
- How would you determine the optimal heap size for MicroPython in a system that also runs native C tasks?
- What tools or compile-time options does MicroPython provide for tracking heap fragmentation over time?

---

## Q3: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The bootloader's decision logic should be simple, deterministic, and fail-safe — it must never boot an invalid image. I'd structure it as a state machine with three possible outcomes: boot Bank A, boot Bank B, or enter a recovery mode.

The decision starts by reading a persistent metadata structure stored in a dedicated flash page (or EEPROM) that contains: the active bank indicator, a boot attempt counter, and a flag for "image confirmed good." On each power-on or reset, the bootloader reads this metadata and applies the following logic:

1. If the active bank's image has been marked as "confirmed good" (by the application after successful operation), boot that bank unconditionally.
2. If the active bank's image is not yet confirmed, check the boot attempt counter. If it's below a threshold (e.g., 3 attempts), increment the counter and boot the active bank. If it exceeds the threshold, mark that bank as failed and switch to the alternate bank.
3. If neither bank is valid, enter recovery mode (e.g., wait for a USB or UART connection to load firmware).

For validation before booting, I'd perform these checks in order, aborting to the alternate bank if any fails:
- **CRC check**: Verify the entire application image against a stored CRC32 or SHA-256 hash. This catches corruption during storage or flash wear.
- **Vector table validation**: Read the first word of the image (the initial stack pointer) and verify it points to valid RAM. Read the reset vector and verify it points to valid flash. This catches completely garbled images.
- **Image size check**: Ensure the image fits within the allocated bank and doesn't overflow into the bootloader region.
- **Version compatibility check**: Compare the image's version metadata against the bootloader's minimum supported version, to prevent booting an image built for incompatible hardware.

The bootloader itself should be stored in a write-protected flash region and should never update itself — that avoids the risk of bricking the device during a bootloader update.

**Possible follow-ups:**
- How would you handle the case where the device loses power during the OTA write itself, leaving both banks potentially corrupted?
- What security considerations would you add if the device needs to verify the authenticity of the OTA image before applying it?

---

## Q4: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** I'd acknowledge that increasing the timeout would technically fix the symptom, but I'd argue it's the wrong solution for a medical device. A 5-second watchdog timeout means any fault that hangs the main loop would take 5 seconds to detect — that's a long time for a device that might be monitoring a patient. The better approach is to restructure the code so the watchdog can be kicked more frequently, even during long operations.

I'd suggest breaking the calibration routine into smaller steps, each taking no more than a few hundred milliseconds. Between each step, kick the watchdog. This requires the calibration to be implemented as a state machine that can be resumed, rather than a single blocking function. For example, if calibration involves taking 30 measurements with 100 ms settling time between them, each measurement cycle can kick the watchdog after completion.

If the calibration truly cannot be interrupted (e.g., it involves a hardware sequence that must run uninterrupted), then I'd consider using a multi-tier watchdog strategy. The main watchdog stays at a short timeout (e.g., 1 second) and is kicked by a high-priority timer interrupt that runs regardless of what the main loop is doing. A separate, longer watchdog (or a software timer) monitors that the calibration actually completes within the expected 3-second window. This way, a main-loop hang is still caught quickly, while the calibration has appropriate supervision.

I'd also investigate why calibration takes 3 seconds — is there a hardware settling time that could be reduced, or is the firmware doing something inefficient like polling a sensor that could be interrupt-driven? Optimizing the calibration time itself might eliminate the problem entirely.

**Possible follow-ups:**
- How would you implement a watchdog kick from a timer interrupt without creating a race condition where the interrupt kicks the watchdog even though the main loop is hung?
- What testing approach would you use to verify that the restructured calibration reliably kicks the watchdog under all conditions?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd start by framing this not as a personal preference but as a design decision that depends on specific system requirements. I'd call a meeting with both engineers and walk through a structured decision framework together.

First, we'd define the protocol's timing requirements: what is the maximum acceptable latency between a data arrival and the firmware's response? What is the minimum interval between incoming messages? What is the worst-case CPU load from other tasks during that interval?

Then we'd evaluate both approaches against those requirements:

**Polling** works well when the polling interval can be shorter than the minimum message interval, and when the CPU has enough idle time to poll frequently without starving other tasks. It's deterministic — the response time is bounded by the polling period. It's also simpler to debug because there's no nested interrupt context to worry about.

**Interrupt-driven** is necessary when the message arrival is asynchronous and the required response latency is shorter than what polling can achieve without consuming excessive CPU. However, interrupts introduce complexity: priority inversion, nested interrupt handling, shared data protection, and potential for missed interrupts if the ISR takes too long.

I'd ask both engineers to produce a simple analysis: for polling, calculate the CPU utilization at various polling rates and the worst-case response time. For interrupts, estimate the interrupt latency and the maximum ISR duration. If both approaches meet the requirements, I'd lean toward polling for its simplicity and maintainability — especially in a medical device where predictability and testability are paramount.

If the requirements genuinely demand interrupts, I'd ask the interrupt advocate to produce a design that minimizes complexity: keep ISRs short (just copy data to a buffer and set a flag), defer all processing to a task, and use a mutex or atomic operations for shared data. I'd also ask them to document the interrupt priority scheme and justify why it won't cause priority inversion with other system interrupts.

Ultimately, the decision should be based on data, not opinion. If neither engineer can provide convincing analysis, I'd suggest prototyping both approaches on the target hardware and measuring actual latency and CPU usage under worst-case conditions.

**Possible follow-ups:**
- How would you handle the situation where the polling approach meets timing requirements in testing but fails under a corner case you hadn't considered?
- What documentation would you expect from either approach to support future maintenance and regulatory review?