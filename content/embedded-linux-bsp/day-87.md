# embedded-linux-bsp — Day 87

## Q1: How would you approach debugging a kernel driver whose `probe()` function succeeds, but the device is completely non-functional afterward — no errors in the log, no timeouts, just silence?

**Answer:** A silent, "successful" probe that leaves the device dead is almost always a case of the driver doing the wrong thing without anything checking it. I'd work outward from the driver's own assumptions rather than from the log, since the log is telling me nothing.

First, I'd confirm the probe actually ran and reached the end — add a print at the last line of probe, or check that the device shows up under the expected sysfs path. If probe returned success but the device node isn't populated, the issue is in registration, not hardware.

Then I'd verify the basics the driver assumes are true: is the clock actually enabled and at the right rate, is the regulator on and at the right voltage, is the reset line de-asserted, is the pinmux set to the peripheral function rather than GPIO? A driver that enables a clock but never checks the return value, or that assumes the bootloader left a regulator on, will probe "successfully" against dead silicon. I'd read back the relevant registers — clock enable bits, power status — to confirm state rather than assume it.

Next I'd check the register access path itself. If the driver uses a regmap or an ioremap'd region, I'd read a known register (a device ID or revision register is ideal) and confirm it returns a sane value. A wrong base address, a wrong register width, or a missing `reg` entry in the device tree can all produce silent reads of zero or 0xFFFFFFFF without any fault.

If register reads look correct, I'd move to the interface level — scope the bus (I2C/SPI) during probe to confirm transactions are actually going out and being acknowledged. Silence on the wire usually means the driver never issued a transfer, which points back to a logic error in the init sequence.

Finally, I'd compare against a known-good reference: the vendor's driver, an earlier board revision, or a datasheet init sequence. The most common root cause for this exact symptom is an initialization step that's present in the reference but missing or mis-ordered in the custom driver.

**Possible follow-ups:**
- How would you tell the difference between a driver bug and a hardware bring-up problem in this scenario?
- If the device ID register reads back correctly but nothing else works, where would you look next?

## Q2: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration change can be applied cleanly without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth and express your board's deltas as additive artifacts layered on top, so that when the vendor bumps their kernel you rebase your small changes rather than re-merging a fork.

The cleanest mechanism is a kernel configuration fragment. Yocto's kernel class supports `.cfg` fragments that get merged into the final `.config` via `merge_config`, applied in a defined order. You create a fragment containing only the options your board needs — say, enabling a specific sensor driver or a bus controller — and reference it through a `SRC_URI` append in a `.bbappend` that lives in your own layer. The vendor's recipe and defconfig stay untouched.

For anything beyond config — a small patch to a driver, a device tree addition — you add those as `SRC_URI` appends too, with the patch files in your layer's `files/` directory. The `.bbappend` is the only file that references the vendor recipe by name, so the coupling is one file wide.

A few practices make this maintainable: keep fragments minimal and single-purpose so a rebase conflict is obvious; name them after the feature, not the board, where possible, so they can be reused across variants; and pin the vendor layer to a known revision in your `bblayers.conf`/manifest so a vendor update is a deliberate, testable event rather than a surprise.

I'd also verify the merge order — if the vendor's defconfig sets an option one way and your fragment sets it another, you need to know which wins, and that's controlled by fragment ordering. Documenting that order in the layer README saves the next person real time.

**Possible follow-ups:**
- What happens if the vendor later adds the same option to their defconfig — how do you detect and resolve the overlap?
- How would you validate that the fragment actually took effect in the built image, rather than assuming it did?

## Q3: You're bringing up a board where the kernel boots and the root filesystem mounts, but a userspace daemon that talks to a kernel driver via `ioctl` intermittently fails with `EINTR` and aborts. Nothing is intentionally sending it signals. How would you approach this?

**Answer:** `EINTR` means a blocking syscall was interrupted by a signal that the process has a handler for (or that isn't ignored). If the daemon isn't deliberately receiving signals, the first question is: what signal, and from where? I'd instrument before theorizing — run the daemon under `strace -f -e trace=signal,ioctl` and see exactly which signal arrives and at what point in the ioctl.

Common sources of "unintended" signals in an embedded system: a watchdog or supervisor process sending `SIGTERM`/`SIGUSR1` on a timer; a parent process or init system sending signals during service management; `SIGCHLD` if the daemon forks; or a debug/monitoring tool. I'd check what else is running and whether any of it targets this process.

But there's a second, more subtle possibility: the ioctl itself is returning `-EINTR` from the kernel because the driver's blocking wait was interrupted — for example, a `wait_event_interruptible` that woke on a signal rather than on the condition it was waiting for. In that case the signal may be benign (even `SIGCHLD` or a profiling signal) and the real bug is that the driver returns `-EINTR` to userspace instead of restarting the wait, and the daemon treats any error as fatal.

So there are two fixes depending on the cause. If the signal is spurious and expected, the daemon should handle `EINTR` correctly — retry the ioctl rather than abort, which is standard practice for any blocking syscall. If the driver is the source, it should use an interruptible wait but loop on `-ERESTARTSYS` semantics so a signal doesn't surface as a hard failure unless the caller actually wants to be interrupted.

The deeper point I'd make in an interview: `EINTR` is not an error condition to be surprised by — it's part of the contract of interruptible sleeps, and both the driver and the userspace caller need to handle it deliberately. A daemon that aborts on `EINTR` is fragile by design.

**Possible follow-ups:**
- How would you decide whether the driver should use an interruptible or uninterruptible wait for this ioctl?
- If the signal turns out to be coming from the init system, how would you change the service definition to avoid it?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path controls, so the design has to decouple them rather than have them contend for the same lock or the same bus transaction.

The cleanest structure is a producer/consumer split inside the driver. The real-time task's access path — the ioctl or read that must meet its deadline — takes a short, bounded lock, does the minimum hardware interaction, and copies its result into a pre-allocated buffer or ring. It never waits on the logging side. The logging task reads from that buffer asynchronously, and if the buffer is full, the logging task drops or overwrites according to policy — it never blocks the producer.

Concretely, I'd use a lock-free or minimally-contended ring buffer between the two, with the real-time side as the single writer and the logging side as the reader. The real-time path should avoid any allocation, any sleeping lock, and any operation whose latency depends on the logging task's progress. If the hardware itself is a shared resource — say both tasks read the same sensor — I'd serialize at the hardware level with a spinlock held only for the register access, not for the whole logging operation, and make sure the logging task's hardware access is itself bounded.

Priority matters too: the real-time task should run at a higher scheduling priority, and if it's a threaded IRQ or a `SCHED_FIFO` task, the logging task must not be able to hold a resource it needs. I'd also consider whether the logging task can be moved entirely out of the driver — for example, the driver exposes a character device the real-time task reads, and a separate userspace logger consumes from a shared memory region. That removes the logging path from the kernel critical section altogether.

The thing I'd emphasize: "never delay" is a latency requirement, so it has to be verified, not assumed. I'd measure worst-case latency of the real-time path under heavy logging load, not just nominal timing.

**Possible follow-ups:**
- How would you size the ring buffer, and what's your policy when the logging consumer falls behind?
- If the hardware register access genuinely can't be made non-blocking, how would you restructure the design?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination and risk-management problem, not a purely technical one, because both teams have legitimate concerns and the real question is how to make the change safely rather than whether to make it.

First I'd get the facts on the table: what exactly does the manufacturing line depend on — is it the debug UART specifically, or any early console output? Is the dependency on a specific physical connector, a specific baud rate, or just "we can see boot messages"? That determines how much freedom we actually have. Often the requirement is "early visibility," which can be satisfied by a different pin or a different console, not necessarily the same UART on the same pins.

Then I'd assess the change's true blast radius. Moving a pinmux group touches the bootloader's early console setup, the device tree's pin control and chosen console node, and possibly the kernel command line. That's a known, bounded set of changes — not a reason to refuse, but a reason to sequence them carefully and test on real hardware, not just in the build.

I'd propose a path that de-risks it: keep the current debug UART working through the next prototype or build so manufacturing isn't blocked, and bring up the new pinmux on a separate branch or board variant in parallel. Validate that early boot output still appears on the new pins before switching the default. If the new peripheral is genuinely needed for the next milestone, we schedule the switch with a validation gate rather than doing it blind.

Throughout, I'd keep the conversation focused on the shared goal — shipping a device that meets its requirements — and make sure the manufacturing team's dependency is documented as a real constraint, not dismissed as an inconvenience. If the change turns out to be unavoidable and the console dependency can't be preserved, that's a decision for the project to make with full information, and I'd want it recorded as a risk with a mitigation, not discovered later on the line.

**Possible follow-ups:**
- If manufacturing insists the exact same physical debug connector must be preserved, how would that change your approach?
- How would you verify the new pinmux works for early boot before committing to the switch?