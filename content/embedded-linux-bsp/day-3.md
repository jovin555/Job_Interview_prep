# embedded-linux-bsp — Day 3

## Q1: How would you approach debugging a kernel panic that occurs only on every third or fourth boot, with no consistent trigger?

**Answer:** This sounds like a timing-dependent or race-condition issue, which requires a systematic approach. First, I'd enable kernel debugging features that don't significantly alter timing: `CONFIG_DEBUG_KERNEL`, `CONFIG_DEBUG_BUGVERBOSE`, `CONFIG_PRINTK_TIME`, and `CONFIG_DEBUG_INFO`. I'd also enable `CONFIG_LOCKDEP` and `CONFIG_DEBUG_ATOMIC_SLEEP` if the system can tolerate the overhead, as these catch common concurrency bugs.

Next, I'd capture the full panic output using a serial console or `netconsole` — the register dump, call trace, and `PC` value are essential. If the panic message points to a specific function or memory address, I'd use `addr2line` or `gdb` with the vmlinux image to map it to source code and line number.

If the panic is in driver code, I'd look for patterns: does it correlate with a specific peripheral being accessed, a DMA transfer completing, or an interrupt firing? I'd add temporary `printk` statements (or use `trace_printk` for lower overhead) at key points to log execution flow across boots. For truly intermittent issues, I'd set up a script to automatically reboot the board after each panic and log the output, then analyze the collected traces for common patterns.

If the issue appears related to memory corruption, I'd enable `CONFIG_SLUB_DEBUG` and `CONFIG_KMEMCHECK` (if available) or use KASAN for the kernel address sanitizer. I'd also check whether the panic correlates with specific hardware states — for example, does it only happen when a particular sensor is actively sampling, or when the system enters a low-power state?

**Possible follow-ups:** How would you distinguish between a hardware-timing issue and a software race condition in this scenario? What if the panic only occurs on production hardware but not on your development board?

---

## Q2: Walk through the boot sequence from power-on to a running Linux userspace on an ARM-based embedded system. What are the key stages and what can go wrong at each?

**Answer:** The boot sequence has several distinct stages, each with its own failure modes:

1. **ROM bootloader (BootROM):** The SoC's internal ROM executes first, reading boot configuration from strapping pins or OTP fuses. It initializes minimal hardware (typically just the boot medium interface) and loads the next stage. Failures here are usually board-level: wrong boot mode pins, corrupted boot medium, or power sequencing issues.

2. **Primary bootloader (SPL/MLO for TI, or U-Boot SPL):** This small program initializes DRAM and the storage controller, then loads the full bootloader. Common issues: incorrect DRAM timings causing memory corruption, or the SPL being too large for the limited SRAM available.

3. **Secondary bootloader (U-Boot proper):** This initializes more peripherals (Ethernet, MMC, USB), sets up the device tree, and loads the kernel. Failures include: wrong `bootargs` or `bootcmd` environment variables, missing or incorrect device tree, or the kernel image being corrupted or at the wrong load address.

4. **Kernel decompression and early setup:** The kernel decompresses itself, then executes `start_kernel()`. Early failures often relate to: missing or incorrect device tree (the kernel can't find its root node or memory node), or the kernel being configured for a different CPU architecture variant.

5. **Kernel initialization:** The kernel sets up interrupt controllers, timers, and schedules. It then probes device tree nodes and initializes drivers. Failures here include: driver probe ordering issues (a device driver needs a clock or regulator that hasn't been initialized yet), missing firmware files, or memory allocation failures.

6. **Root filesystem mount:** The kernel mounts the root filesystem specified in `root=` bootargs. Common failures: wrong root device (e.g., `/dev/mmcblk0p2` vs `/dev/mmcblk1p2`), missing filesystem driver in the kernel, or filesystem corruption.

7. **Init process:** The kernel executes `/sbin/init` (or whatever is specified in `init=`). Failures include: missing init binary, incorrect permissions, or a broken init script that immediately crashes.

For debugging, I'd add `earlyprintk` or `earlycon` to see output from the earliest kernel stages, and use `initcall_debug` to see which driver initializations succeed or fail.

**Possible follow-ups:** How would you debug a system that hangs with no console output at all after power-on? What tools would you use to determine which stage is failing?

---

## Q3: How would you implement a reliable software watchdog mechanism on an embedded Linux system that must meet medical device uptime requirements?

**Answer:** For a medical device, the watchdog needs to be robust against both hardware hangs and software deadlocks. I'd approach this with a layered strategy:

First, I'd use the hardware watchdog timer (WDT) built into the SoC, configured via the kernel's watchdog framework. The hardware WDT is the last line of defense — if the kernel stops servicing it, the system resets. I'd configure it with a timeout that's long enough to avoid false resets during normal operation (e.g., 30-60 seconds) but short enough to meet the device's safety requirements.

Second, I'd implement a userspace watchdog daemon (like `watchdogd` or a custom one) that periodically pings the hardware watchdog. This daemon would monitor critical system health indicators: is the main application process still running? Is memory usage within limits? Are critical sensors returning valid data? If any check fails, the daemon stops pinging, and the hardware watchdog triggers a reset.

Third, I'd add a kernel-level monitoring mechanism using `CONFIG_WATCHDOG_SOFTWDT` or a custom kernel thread that monitors the health of the userspace daemon. This creates a chain: the kernel thread checks that the userspace daemon is alive, the daemon checks that the application is healthy, and the application checks that the system is functioning correctly. If any link breaks, the hardware watchdog eventually fires.

For medical devices, I'd also consider a dual-watchdog approach: one internal to the SoC and one external (a dedicated watchdog IC). The external watchdog monitors the SoC's power and a heartbeat GPIO — if the SoC fails to toggle the GPIO within the timeout, the external watchdog cuts power or asserts a system reset. This protects against scenarios where the SoC itself is stuck in a state that prevents it from servicing even its internal watchdog.

Finally, I'd ensure the watchdog is configured to survive kernel crashes: the hardware watchdog should be set up early in the bootloader and never disabled, so even a kernel panic triggers a reset. The bootloader should also check for watchdog-induced resets and log them for post-mortem analysis.

**Possible follow-ups:** How would you test that your watchdog mechanism actually works under fault conditions? What considerations apply if the device needs to preserve state across a watchdog reset?

---

## Q4: You're designing a BSP for a system with two processors: an application processor running Linux and a real-time microcontroller handling safety-critical sensor acquisition. How would you structure the inter-processor communication and resource sharing?

**Answer:** This is a common architecture for medical devices where you need both rich user interfaces (Linux) and deterministic real-time control (RTOS on the MCU). I'd structure the BSP around clear separation of concerns and well-defined communication channels.

For **resource partitioning**, I'd ensure each processor has exclusive access to its critical peripherals. The MCU would own all safety-critical sensors, ADCs, and actuators directly — no Linux involvement in real-time control loops. The application processor would handle the display, networking, storage, and user interface. Shared resources like power management or a shared memory region would need careful arbitration.

For **inter-processor communication (IPC)**, I'd use a combination of mechanisms:

- **Shared memory** for high-bandwidth data transfer (e.g., sensor data buffers). I'd define a fixed-size ring buffer structure in a reserved memory region, with atomic read/write pointers to avoid corruption. The memory region would be carved out in the device tree as a reserved-memory node, accessible to both processors.

- **Mailbox interrupts** for signaling. When the MCU has new data ready, it triggers an interrupt to the application processor via a dedicated hardware mailbox or GPIO. The Linux side would have a kernel driver that handles this interrupt and wakes up a userspace daemon to process the data.

- **A simple command/response protocol** over the shared memory. I'd define a fixed set of message types (e.g., START_ACQUISITION, SET_PARAMETER, STATUS_REQUEST) with a well-defined format including sequence numbers and CRC checksums for reliability.

On the Linux side, I'd implement this as a platform driver that:
1. Maps the shared memory region into kernel space
2. Registers an interrupt handler for the mailbox
3. Exposes a character device or netlink interface to userspace
4. Handles power management callbacks to coordinate sleep states with the MCU

For **boot sequencing**, the MCU would typically boot first and initialize its real-time tasks, then signal to the application processor that it's ready. The Linux BSP would include a device tree node describing the shared memory region and mailbox, and the driver would wait for the MCU's ready signal before exposing its interface to userspace.

**Possible follow-ups:** How would you handle firmware updates for the MCU from the Linux side? What happens if the MCU crashes — how does the Linux side detect and recover from that?

---

## Q5: Behavioral — You're the BSP lead for a new product, and during integration testing, you discover that the kernel driver for a critical sensor intermittently returns corrupted data. The hardware team insists the sensor interface is designed correctly, and the firmware team says their initialization sequence is correct. How would you handle this situation?

**Answer:** I'd approach this as a technical investigation first, not a blame assignment. The goal is to find the root cause, not to prove which team is wrong.

First, I'd gather objective data. I'd instrument the driver to log every register read and write, along with timestamps, during both good and bad reads. I'd also capture the raw sensor data at the hardware level using a logic analyzer or oscilloscope on the SPI/I2C lines. This gives us a factual basis for discussion rather than opinions.

Second, I'd look for patterns in the corruption. Is it always the same bit positions? Does it correlate with specific system states (e.g., when WiFi is active, or when the display refreshes)? Does it happen at specific data rates or clock speeds? This analysis might reveal whether it's a timing issue, a noise coupling problem, or a protocol violation.

Third, I'd organize a cross-team debugging session with the hardware and firmware engineers. I'd present the data I've collected and ask each team to explain what they see from their perspective. For example, if the logic analyzer shows the sensor is sending correct data but the driver reads it wrong, that points to a software issue. If the sensor output is actually corrupted on the bus, that's a hardware or firmware problem.

If the issue remains unclear, I'd propose controlled experiments: reduce the SPI clock speed, add explicit delays between transactions, or isolate the sensor from other noisy components. Each experiment narrows the possibilities.

Throughout this process, I'd keep the project manager informed of progress without escalating blame. I'd frame it as "we're investigating an intermittent data integrity issue" and provide regular updates on what we've ruled out and what we're testing next. If the investigation stalls, I'd suggest bringing in a third-party expert (e.g., the sensor manufacturer's FAE) to provide an independent perspective.

The key is to maintain a collaborative, data-driven approach. In my experience, intermittent issues like this often turn out to be a combination of factors — a marginal timing margin in the hardware combined with a race condition in the driver — and fixing it requires input from all teams.

**Possible follow-ups:** What if the hardware team refuses to acknowledge the issue and insists the problem is in software? How would you escalate this without damaging team relationships?