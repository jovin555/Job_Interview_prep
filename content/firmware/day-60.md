# firmware — Day 60

## Q1: How would you approach designing a firmware module that must handle a peripheral which can be accessed by more than one thread, where the access patterns differ — one thread does short register reads, another does long burst transfers — and you want to avoid one starving the other?

**Answer:** The core problem is that a shared peripheral is a single resource, but the two access patterns have very different hold times. A short register read might occupy the bus for tens of microseconds; a long burst transfer might occupy it for milliseconds. If you protect the peripheral with a single coarse mutex, the burst transfer can block the register-read thread for the entire burst duration, which may be unacceptable if that thread has a real-time deadline. If you don't protect it at all, the two threads will interleave transactions and corrupt each other's state.

The first thing I'd do is clarify the actual timing requirements. Does the register-read thread have a hard deadline, or is it just "should be responsive"? Does the burst transfer have to be atomic from the peripheral's perspective, or can it be chunked? The answer determines the design.

If the burst can be chunked, the cleanest approach is to break the long transfer into smaller units — say, a few hundred bytes at a time — and release the mutex between chunks. That bounds the worst-case hold time to the chunk duration, so the register-read thread's latency is bounded by the chunk size rather than the whole transfer. The burst thread re-acquires the mutex for each chunk. This does add some overhead and requires the peripheral to tolerate being paused mid-transfer, but many peripherals (especially DMA-driven ones) handle this fine.

If the burst cannot be chunked, I'd consider a priority-inheritance or priority-ceiling mutex so that a high-priority register-read thread can preempt the burst thread's hold on the mutex. Zephyr's `k_mutex` supports priority inheritance, which prevents the classic priority inversion problem. But priority inheritance only helps if the register-read thread actually has higher priority — if both threads are the same priority, you still get starvation.

A third option is to serialize all access through a single dedicated thread or work queue that owns the peripheral. The other threads post requests to it. This makes the access pattern explicit and lets you implement a scheduling policy — for example, "always service register reads before starting a new burst, but don't preempt an in-progress burst." The cost is an extra context switch and a request/response mechanism, but it's often the most maintainable design because the peripheral's access policy lives in one place.

I'd also want to instrument the system to measure actual hold times and queue depths, because the right answer depends on real numbers, not assumptions. If the burst is 10 ms and the register read deadline is 1 ms, chunking is mandatory. If the burst is 200 µs and the deadline is 5 ms, a simple mutex is fine.

**Possible follow-ups:**
- How would you decide between priority inheritance and a dedicated peripheral-owner thread?
- What would you do if the peripheral cannot tolerate being paused mid-burst, and the register-read thread has a hard deadline shorter than the burst duration?

## Q2: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those things that's easy to get wrong in both directions — too small causes intermittent corruption that's hard to debug, too large wastes RAM that a constrained device can't spare. I'd approach it as a measurement problem, not a guess.

The starting point is to understand what actually consumes stack in each thread. Local variables, function call depth, interrupt nesting (if the thread can be interrupted), and any library calls that have their own stack usage. Floating-point operations, `printf`-family functions, and cryptographic routines are notorious for large stack footprints. A thread that looks simple at the source level might have a deep call chain underneath.

For initial sizing, I'd use a conservative estimate based on the worst-case call path, then add margin. But the real work is verification. Zephyr provides stack analysis tooling — `CONFIG_THREAD_ANALYZER` and the `k_thread_stack_space_get()` API — that let you query the high-water mark of stack usage at runtime. I'd enable that during development and instrument the system to log the peak usage per thread after exercising all the code paths, including error paths and rare branches. The high-water mark tells you what the thread actually used, not what you think it used.

The tricky part is that the worst case often occurs in paths that are hard to exercise — an error handler that only runs when a sensor fails, or a recovery path that only triggers after a fault. So I'd also do static analysis where possible, and I'd deliberately inject faults during testing to force those paths to run and measure their stack usage.

For the final sizing, I'd add a safety margin — typically 25–50% over the measured high-water mark, depending on how confident I am that I've exercised all paths. On a medical device, I'd lean toward the larger margin, because a stack overflow in the field is a safety issue, not just a bug. I'd also enable Zephyr's stack sentinel or canary feature (`CONFIG_STACK_SENTINEL`) so that an overflow is detected immediately rather than silently corrupting adjacent memory.

One more consideration: interrupt stack usage. On many architectures, interrupts run on a separate interrupt stack, but if the architecture shares the thread stack for interrupts, the thread's stack budget has to account for the deepest interrupt handler plus its own usage. That's a common source of underestimation.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage is hard to measure because it depends on external input?
- What would you do if you discovered, late in the project, that a thread's stack is overflowing intermittently and you can't easily increase it because RAM is tight?

## Q3: You're debugging a firmware issue where a device works correctly for days, then a peripheral driver starts returning errors that clear on reboot. How would you approach this?

**Answer:** The fact that it clears on reboot is the most important clue — it tells me the problem is in accumulated state, not in a permanent hardware fault or a configuration error that would manifest immediately. Something is drifting, filling up, or being corrupted over time, and the reboot resets whatever that something is.

My first step would be to characterize the failure more precisely. What exactly does "starts returning errors" mean? Is it a specific error code, a timeout, a CRC failure, a bus error? Does it happen at a consistent time, or does it vary? Does it correlate with any external event — a particular operation, a temperature change, a power event? The more precisely I can describe the failure, the narrower the search space.

Then I'd look at the driver's state. Drivers often maintain internal state — a transaction counter, a buffer, a state machine, a retry count, a cached configuration. If any of that state can grow unboundedly or wrap incorrectly, it could cause failures after enough operations. A counter that overflows after N transactions, a buffer index that doesn't reset properly, a state machine that gets stuck in a state it can't recover from — these are all classic "works for a while, then fails" patterns.

I'd also look at the peripheral's own state. Many peripherals have internal registers that can get into a bad state — an error flag that's set and never cleared, a FIFO that's full, a clock that's been gated off. If the driver doesn't clear error flags or reset the peripheral on certain conditions, the peripheral can get stuck. The reboot clears the peripheral's state, which is why it recovers.

Another angle is resource exhaustion. If the driver allocates memory, opens handles, or takes semaphores without releasing them on all paths, those resources leak over time. Eventually an allocation fails or a semaphore can't be taken, and the driver starts returning errors. A reboot frees everything. I'd check for unbalanced allocations, missing releases on error paths, and any place where a resource is acquired but not released if a subsequent step fails.

I'd also consider whether the failure is actually in the driver or in something the driver depends on. If the driver talks to a sensor over I2C, and the I2C bus itself is getting into a bad state — a stuck clock line, a slave that's holding the bus — the driver would report errors even though its own logic is fine. The reboot resets the bus. So I'd want to distinguish between "the driver is broken" and "the driver is correctly reporting that something else is broken."

For diagnosis, I'd add logging that captures the driver's internal state and the peripheral's status registers at the moment of failure, and ideally a rolling log of the last N transactions so I can see what led up to it. If the failure takes days to reproduce, I'd want the log to persist across reboots so I don't lose the evidence. I'd also try to accelerate the failure — run the device in a loop, increase the transaction rate, or stress the specific operation that seems to trigger it — so I can iterate faster.

**Possible follow-ups:**
- How would you distinguish between a driver bug and a hardware issue that the driver is correctly reporting?
- What would you do if the failure only reproduces in the field and you can't reproduce it in the lab?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The bootloader/application split is a design decision that's hard to change later, so it's worth getting right up front. The guiding principle is that the bootloader should contain only what's needed to safely get the application running and to update it — nothing more. Every line of code in the bootloader is code that can't be updated in the field without a risky bootloader update, so the bootloader should be as small and as stable as possible.

The bootloader's essential responsibilities are: verify the application image before booting it (CRC, signature, or both), select which image to boot if there are multiple banks, provide a mechanism to receive and write a new image, and handle the case where the application is invalid or missing. That's the core. Everything else is a candidate for the application.

Things that often get pulled into the bootloader but usually shouldn't: application-specific configuration, communication protocol stacks beyond what's needed for the update, user interface, logging beyond minimal diagnostics, and any feature that might need to change over the product's lifetime. If a feature might need to be updated, it belongs in the application, because the application can be updated safely and the bootloader can't.

There are exceptions. If the update mechanism itself requires a communication stack — say, the device updates over a wireless link — then that stack has to be in the bootloader, or the bootloader has to be able to use a stack that's in the application, which is fragile. In that case, the stack is part of the bootloader's essential function, and it has to be designed for stability.

Another consideration is recovery. If the application is corrupted and the bootloader can't recover it, the device is bricked. So the bootloader needs a recovery path — a way to receive a new image even if the application is completely gone. That might mean a minimal communication interface in the bootloader, or a fallback mode that the device enters when the application is invalid. The recovery path is part of the bootloader's essential function, even if it duplicates some of the application's communication code.

I'd also think about the update protocol. Does the bootloader receive the image directly, or does the application receive it and then hand off to the bootloader to write it? The latter is often better, because the application has the full communication stack and can handle retries, resumption, and validation before committing to a bootloader handoff. The bootloader then just needs to verify and write the image, which is a much smaller responsibility.

Finally, I'd consider the security model. If the device needs secure boot, the bootloader has to verify the application's signature before booting it. That means the bootloader holds the public key and the verification code. That's essential bootloader function, but it also means the bootloader is now security-critical, and any bug in it is a vulnerability. So the verification code needs to be simple, well-tested, and ideally based on a well-reviewed library rather than hand-rolled.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself needs to be updated?
- What would you put in the bootloader to support recovery if the application is completely corrupted?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it relies on a global variable to communicate between two threads without any synchronization. They argue that the variable is just a flag and "it's only one byte, so it's atomic." How would you guide them?

**Answer:** This is a common and understandable misconception, and I'd want to correct it without making the engineer feel defensive. The "it's only one byte, so it's atomic" argument has a kernel of truth — on most architectures, a single-byte read or write is indeed atomic at the hardware level, in the sense that you won't see a torn value. But atomicity of the individual access is not the same as correctness of the communication, and that's where the argument breaks down.

The first issue is compiler optimization. Without a `volatile` qualifier or a memory barrier, the compiler is free to cache the flag in a register, reorder accesses around it, or eliminate a read entirely if it thinks the value can't change. So the flag might not even be re-read when the other thread changes it. That's not a hardware atomicity problem — it's a compiler problem, and it can cause the code to fail in ways that are very hard to debug because the source looks correct.

The second issue is memory ordering. Even if the flag access itself is atomic and the compiler doesn't reorder it, the compiler and the CPU can reorder other memory accesses around it. If the flag is meant to signal "the data is ready," but the data write is reordered to after the flag write, the reader can see the flag set before the data is actually written. On a single-core system with a simple in-order CPU, this might not happen in practice, but on a multi-core system or a CPU with a weak memory model, it absolutely can. And even on a single-core system, the compiler can reorder.

The third issue is that "it works in testing" is not evidence of correctness. Race conditions are timing-dependent. The code might work because the timing happens to be favorable in the test setup, but fail under different timing — a different compiler optimization level, a different CPU load, a different hardware revision. The fact that it hasn't failed yet doesn't mean it's correct; it means the failure hasn't been triggered.

So how would I guide them? I'd start by explaining the three issues — compiler optimization, memory ordering, and the limits of "it works in testing" — and I'd show them a concrete example of how the code could fail. Then I'd introduce the proper tools. For a simple flag, the right primitive is an atomic variable with the appropriate memory ordering, or a `volatile` flag combined with a memory barrier if the semantics are simple enough. For anything more complex — passing data, not just a flag — the right tool is a proper synchronization primitive: a mutex, a semaphore, a message queue, or a Zephyr `k_*` primitive designed for the purpose.

I'd also want to make the point that the choice of primitive should be driven by the semantics of the communication, not by what's convenient. A flag that signals "data is ready" is different from a flag that signals "please stop." A one-way signal is different from a request/response. Getting the semantics right makes the synchronization obvious.

Finally, I'd suggest that we add a code review checklist item or a static analysis rule to catch unsynchronized shared variables, so this class of bug gets caught systematically rather than relying on someone noticing it in review. That turns a one-time correction into a team-wide improvement.

**Possible follow-ups:**
- How would you decide between using an atomic variable and a mutex for a simple flag?
- What static analysis or tooling would you use to catch unsynchronized shared state in a codebase?