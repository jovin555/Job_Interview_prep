# firmware — Day 47

## Q1: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This pattern — corruption in an unrelated region under heavy load — points to several classic root causes, and I'd approach it systematically rather than guessing. First, I'd try to determine whether the corruption is happening during the flash write itself or is a symptom of something else that coincides with heavy load.

My first hypothesis would be a stack overflow or stack collision. Flash writes often use a deep call chain (driver → HAL → low-level programming routine), and under heavy load, interrupt nesting or deeper call paths can push the stack into an adjacent memory region. I'd check the linker map to see what sits next to the stack, then instrument the system to detect stack overflow — either using the MCU's stack pointer monitoring features, filling the stack with a known pattern and checking it periodically, or using the RTOS's built-in stack checking if available.

Second, I'd look at DMA. If the flash controller uses DMA, a misconfigured transfer length or address could write to the wrong location. I'd verify the DMA descriptors and buffer addresses are correct, and check whether the corruption address correlates with any DMA source/destination registers.

Third, I'd consider whether the flash driver properly handles interrupts during the write. Many flash controllers require interrupts to be disabled or carefully managed during programming. If an ISR fires mid-write and accesses flash (e.g., reading a constant from flash, or executing code from flash on a single-bank device), it can cause a bus fault or corrupt the write. Under heavy load, more interrupts fire, increasing the chance of this collision.

I'd also check for a classic C bug: a buffer overflow in the code path leading up to the flash write. Under heavy load, a different code path might populate a buffer with more data than it can hold, and the overflow lands in the region that later appears corrupted. The flash write itself might be innocent — the corruption happened earlier, and the flash write is just when it's noticed.

To isolate this, I'd add a memory protection unit (MPU) region around the corrupted area if the MCU supports it, configured to trigger a fault on access. That would catch the offending code at the exact moment of corruption. I'd also enable the hardware fault handler to capture the program counter and stack frame, which often points directly at the culprit. Finally, I'd try to correlate the corruption with specific operations — logging timestamps, task IDs, and interrupt activity around the failure can reveal a pattern.

**Possible follow-ups:**
- How would you use the MPU to catch this without disrupting normal operation?
- What specific information would you capture in the fault handler to help identify the root cause?

---

## Q2: You're designing a Zephyr RTOS-based system where multiple sensor threads need to share a pool of fixed-size data buffers. How would you choose between using a memory pool versus memory slabs, and what configuration considerations would you need to account for?

**Answer:** In Zephyr, the distinction between memory pools and memory slabs is important, and the choice depends on the allocation pattern. Memory slabs allocate fixed-size blocks — every allocation is the same size, which eliminates fragmentation entirely and makes allocation and freeing deterministic and fast. Memory pools (the older k_mem_pool API) support variable-size allocations by splitting larger blocks, which can lead to internal fragmentation over time and more complex allocation logic.

For a sensor data buffer pool where all buffers are the same size, memory slabs are almost always the right choice. The fixed block size means no fragmentation, allocation is O(1), and the behavior is fully deterministic — critical for a real-time system. The configuration is straightforward: you define the block size (which must accommodate your largest sensor data frame plus any header/metadata) and the number of blocks. You need to ensure the total memory reserved is adequate for the worst-case burst scenario — if the system can temporarily need more buffers than you've allocated, you need a policy for what happens when the pool is exhausted.

With memory pools, you get flexibility for variable-size requests, but you pay for it with more complex internal bookkeeping and the risk of fragmentation over time. In a medical device that runs for extended periods, fragmentation is a serious concern — it's hard to predict and can lead to allocation failures at the worst possible moment. I'd generally avoid variable-size allocation in a hard real-time context unless there's a strong reason for it.

Configuration considerations include: block size must account for alignment requirements (typically word-aligned, sometimes cache-line-aligned if DMA is involved); the number of blocks must cover the worst-case concurrent usage across all threads plus some margin; and you need to decide on blocking behavior — whether a thread that can't get a buffer should block with a timeout, or fail immediately and handle the error. For sensor data, I'd typically use a timeout so the thread waits for a buffer rather than dropping data, but the timeout must be short enough not to stall the sensor read loop. I'd also consider using K_NO_WAIT in ISR context, since you can't block in an interrupt handler.

**Possible follow-ups:**
- What happens when a thread blocks waiting for a buffer from an empty slab — how does that interact with priority inversion?
- How would you handle the case where a sensor produces data faster than buffers are freed, causing the pool to exhaust?

---

## Q3: You're reviewing a colleague's firmware code that uses a large number of global variables to share state between modules. The code works correctly in testing but is difficult to maintain and test. How would you approach refactoring this without introducing regressions?

**Answer:** Refactoring a codebase with heavy global state is risky, especially in a medical device where correctness is paramount. I'd approach this incrementally, with testing at each step, rather than attempting a big-bang rewrite.

First, I'd establish a safety net. Before changing anything, I'd ensure there's adequate test coverage — unit tests where feasible, but at minimum integration tests that exercise the key behaviors. If the codebase lacks tests, I'd write characterization tests that capture current behavior, even if that behavior isn't ideal. These tests document what the system actually does, so I can detect unintended changes during refactoring.

Next, I'd categorize the global variables. Some are truly global configuration or system state — these might be legitimate, though they should be accessed through well-defined interfaces. Others are shared between specific modules — these are candidates for encapsulation. I'd look for groups of globals that are always modified together, which suggests they belong in a single struct or module.

The refactoring strategy would be to introduce accessor functions first, without changing behavior. Replace direct global variable access with function calls — getters and setters — even if those functions initially just read or write the global. This breaks the direct coupling and gives me a place to add validation, locking, or logging later. I'd do this module by module, running tests after each change.

Once access is through functions, I can start moving the actual storage. A group of related globals might become a struct owned by a module, with the accessor functions becoming the module's public API. The global variables become static — visible only within the module. This is a mechanical transformation that preserves behavior while improving encapsulation.

For state that's shared between ISRs and tasks, I'd pay special attention to synchronization. If the original code relied on interrupt disabling or happened to work because of timing, I need to make the synchronization explicit — using Zephyr's atomic operations, spinlocks for short critical sections, or proper kernel objects like mutexes or message queues where appropriate.

Throughout this process, I'd keep changes small and reviewable. Each commit should be one logical step: "encapsulate sensor state behind accessors," "move calibration globals into sensor module," and so on. This makes regression hunting trivial — if something breaks, the last change is the prime suspect.

**Possible follow-ups:**
- How would you handle globals that are accessed from both ISR context and thread context during the refactoring?
- What's your approach if the existing tests don't cover a critical code path that uses the globals?

---

## Q4: You're implementing an I2C driver for a medical sensor that must read 12 bytes of data every 10 ms. The sensor sometimes holds the clock line low (clock stretching) for up to 5 ms. How would you configure the I2C peripheral and handle this timing constraint in firmware?

**Answer:** This is a classic I2C timing challenge, and the key insight is that 5 ms of clock stretching is a very long time in a 10 ms period — the sensor can consume half the available time just stretching. The design has to accommodate this without stalling the rest of the system.

First, I'd check the I2C peripheral's capabilities. Many MCUs have a hardware timeout for clock stretching — if the controller detects the clock held low beyond a configurable period, it generates a timeout interrupt or error. I'd configure this timeout to be slightly longer than the sensor's maximum stretch (say 6 ms) so legitimate stretching doesn't trigger a false timeout, but a stuck bus is detected. If the peripheral doesn't have this feature, I'd implement a software timeout using a timer.

The critical decision is whether to use polling, interrupts, or DMA for the I2C transaction. Polling in a tight loop is unacceptable here — waiting up to 5 ms in a busy-wait would waste CPU and potentially starve other tasks. Interrupt-driven is the right approach: the I2C peripheral generates interrupts on transaction completion or error, and the firmware task can block on a semaphore or similar synchronization primitive while the transaction is in progress. This frees the CPU for other work during the stretch period.

For the timing budget: the sensor needs a read every 10 ms, and the transaction can take up to 5 ms (stretch) plus the actual data transfer time. At 400 kHz (fast mode), 12 bytes plus addressing and control bytes is roughly 300-400 µs of actual bus time. So the worst case is about 5.5 ms of the 10 ms period — leaving about 4.5 ms for other processing. That's tight but feasible if the rest of the system is well-structured.

I'd also consider whether the 10 ms read period is a hard deadline. If the sensor must be read every 10 ms without exception, I'd need to verify that the worst-case transaction time plus any other higher-priority work fits within the budget. If it doesn't, I'd need to look at options: increasing the I2C bus speed if the sensor supports it, using DMA to offload the data transfer, or reconsidering whether the read period can tolerate occasional jitter.

One important detail: during clock stretching, the I2C peripheral is waiting, but the MCU's clock and other peripherals continue running. If the device is battery-powered, I'd check whether the power management subsystem might try to enter a low-power state during the stretch — that could disrupt the I2C transaction. I'd need to ensure the I2C peripheral holds a wake lock or the power management is aware of the active transaction.

Finally, I'd implement robust error handling. If a transaction times out or fails, the driver should retry or report the error to a higher level, depending on the system's fault tolerance. For a medical sensor, silently dropping a reading is not acceptable — the system needs to know the data is stale or missing.

**Possible follow-ups:**
- How would you handle the interaction between the I2C transaction and the device's low-power modes?
- What would you do if the 5 ms stretch plus other processing doesn't fit within the 10 ms budget?

---

## Q5: You're leading a firmware team where a junior engineer has implemented a low-power mode for a medical monitoring device. The device wakes on a timer interrupt, takes a sensor reading, then returns to sleep. The engineer is proud that the measured average current is very low, but you notice the wake-up handler performs the sensor read and data processing entirely within the ISR, including a flash log write that takes 30 ms. How would you approach this situation?

**Answer:** This is a situation where I'd want to acknowledge what the engineer got right while guiding them toward a more robust architecture. The low average current is a legitimate achievement — they've clearly thought about power consumption. But implementing the entire wake-up sequence inside an ISR, especially including a 30 ms flash write, creates several serious problems.

First, I'd explain why this is problematic. An ISR that runs for 30 ms blocks all other interrupts for that duration. If any time-critical event occurs during that window — a communication interrupt, a fault detection, a user input — it will be delayed or potentially lost. In a medical monitoring device, this is a safety concern. Additionally, running complex logic in ISR context is fragile: you can't block, you have limited stack space, and debugging is harder. The flash write in particular is dangerous because many flash controllers require interrupts to be managed carefully during programming, and doing this in an ISR risks corrupting the write if another interrupt fires.

The better architecture is to have the ISR do the minimum necessary — typically just waking the system and signaling a thread — and let a normal thread context handle the sensor read, processing, and flash write. In Zephyr, I'd use a semaphore or a work queue. The timer ISR gives the semaphore or submits work to a thread; the thread then performs the sensor read, processes the data, and writes to flash. This moves the 30 ms operation out of interrupt context entirely.

The power implication is worth discussing too. The engineer's approach might achieve low average current because the ISR runs to completion and then the system sleeps. But moving the work to a thread doesn't necessarily increase power consumption significantly — the thread runs, finishes, and the system can still enter sleep afterward. The key is that the system should sleep when idle, regardless of whether the wake-up work happens in an ISR or a thread. The thread approach might actually allow more aggressive sleep because the ISR returns quickly and the power management can make better decisions about when to enter low-power states.

I'd also raise the question of whether the sensor read and flash write need to happen on every wake-up. Could the sensor data be accumulated in RAM and written to flash less frequently? That would reduce both the time spent awake and flash wear. This is a design conversation worth having — the engineer's implementation works, but there might be a better overall approach.

Finally, I'd frame this as a learning opportunity about ISR best practices: ISRs should be short, deterministic, and free of blocking operations. The rule of thumb I'd share is that if an ISR needs to do more than acknowledge an interrupt and set a flag or wake a thread, it's probably doing too much.

**Possible follow-ups:**
- How would you help the engineer measure whether the thread-based approach preserves the low power consumption they achieved?
- What specific risks would you highlight about performing a flash write inside an ISR?