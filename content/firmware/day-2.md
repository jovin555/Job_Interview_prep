# firmware — Day 2

## Q1: In a Zephyr RTOS application, how would you implement a sensor data acquisition task that must run at 100 Hz while a lower-priority task handles Bluetooth communication, without missing sensor samples?

**Answer:** In Zephyr RTOS, I'd use a combination of a high-priority thread and a timer-driven approach. The sensor acquisition task would be created with `K_THREAD_DEFINE` at a priority higher than the Bluetooth task (e.g., priority 2 vs 5, where lower numbers are higher priority). I'd use `k_timer` to trigger at 10ms intervals, and the sensor thread would pend on the timer using `k_timer_status_sync()` or a semaphore given by the timer callback. This ensures the sensor thread wakes precisely at 100 Hz regardless of what the Bluetooth task is doing.

The sensor thread would read the sensor via I2C/SPI, process the data minimally, push it into a ring buffer (using `ring_buf_put()`), and then yield. The Bluetooth task, running at lower priority, would only execute when the sensor thread is blocked waiting for the next timer tick. This prevents priority inversion and ensures deterministic sensor sampling.

For the Smart OPEP Device project, we used a similar approach with pressure sensors. The pressure sensor data needed reliable capture at fixed intervals to calculate flow characteristics, while a lower-priority task handled RGB LED feedback updates. The timer-driven thread guaranteed we never missed a sample even during LED animations.

**Possible follow-ups:**
- How would you handle the case where the sensor read occasionally takes longer than 10ms due to I2C bus contention?
- What Zephyr kernel object would you use to pass sensor data from the ISR/high-priority thread to the Bluetooth task safely?

---

## Q2: Explain the difference between polling, interrupt-driven, and DMA-based approaches for reading data from an SPI ADC. When would you choose each in a medical device context?

**Answer:** 

**Polling:** The CPU continuously checks the ADC's status register in a loop. Simple to implement but wastes CPU cycles — the processor is stuck waiting. Acceptable only for very slow, non-critical reads where power consumption isn't a concern.

**Interrupt-driven:** The ADC asserts an interrupt line when conversion is complete. The CPU saves context, runs an ISR to read the data, then resumes. Much more efficient than polling — the CPU can do other work while waiting. However, for high-speed continuous sampling, the interrupt overhead (context save/restore) can become significant.

**DMA-based:** The ADC is configured to trigger DMA transfers automatically. When conversion completes, the DMA controller moves data directly from the ADC's data register to memory without CPU involvement. The CPU only gets an interrupt when a buffer is full (e.g., after 64 samples). This is the most efficient for high-throughput applications.

For medical devices, the choice depends on the criticality and data rate. In the SOBA Heart Lung Support Machine, we used DMA for the pressure and temperature sensors that monitored biological parameters. These sensors streamed data continuously, and DMA ensured we never lost a sample while the CPU handled motor speed control and Wi-Fi communication. For the Toco device's uterine contraction monitoring, we used interrupt-driven reads because the data rate was lower (~100 Hz) and we needed to validate each sample immediately for safety checks before storing it. Polling would be inappropriate for any medical device where CPU availability for safety monitoring is critical.

**Possible follow-ups:**
- What potential issue could arise with DMA when the memory buffer wraps around, and how would you handle it in a medical device?
- How does cache coherency affect DMA transfers on Cortex-M processors?

---

## Q3: Describe a situation where you had to debug a firmware timing issue that was causing intermittent device failures. How did you approach it?

**Answer:** During the Lotus (Printer and Toco) project at Trudell Medical International, we encountered an intermittent issue during IEC 60601 testing where the printer unit would occasionally fail to record Toco values during uterine contraction monitoring. The failure was non-deterministic — sometimes it worked for hours, other times it failed within minutes.

**Situation:** The Toco device captured uterine contraction data and sent it to the printer unit for recording alongside maternal and fetal heart rates. During regulatory testing, we'd see gaps in the printed records where Toco values were missing.

**Task:** Identify why the printer was intermittently missing data and fix it before passing IEC 60601 testing.

**Action:** I started by adding timestamped debug logging via UART to a logic analyzer, capturing both the incoming Toco data packets and the printer's processing state. This revealed that the printer's main loop was spending too long formatting the display update (a segment LCD with custom characters), causing it to miss incoming UART data when packets arrived back-to-back during active labor contractions.

The root cause was that the UART receive interrupt was being masked during the LCD update routine, which took approximately 15ms — long enough to overflow the UART's 16-byte hardware FIFO when data arrived at high rates. I restructured the firmware to use a DMA-based UART receive with a circular buffer, so data was captured independently of CPU activity. I also split the LCD update into smaller chunks using a state machine that yielded control back to the main loop between segments.

**Result:** The data gaps were eliminated. We passed the IEC 60601 testing on the next attempt, and the fix was documented in the device's design history file. The DMA approach also reduced overall CPU utilization by about 12%.

**Possible follow-ups:**
- How did you verify the fix wouldn't introduce new timing issues elsewhere in the system?
- What specific IEC 60601 clause covers data integrity for patient monitoring devices?

---

## Q4: You're designing firmware for a battery-powered medical device that must run for 7 days continuously. Walk through your power management strategy using Zephyr RTOS.

**Answer:** For the Smart OPEP Device, which required 7 days of continuous use on a Li-ion battery, I implemented a multi-level power management strategy in Zephyr:

**1. System-level idle management:** Zephyr's power management subsystem (`CONFIG_PM`) was configured to enter tickless idle mode. When no threads are ready to run, the SoC enters a low-power sleep state. The device spends most of its time waiting for the user to breathe into it, so idle power dominates.

**2. Peripheral power gating:** Sensors (pressure, flow) and the RGB LED were powered through GPIO-controlled MOSFETs. The firmware would power down all sensors between breathing events, only enabling them when the device detected the start of a breath cycle via a low-power wake-on-change interrupt on the pressure sensor's interrupt pin.

**3. Clock scaling:** During active monitoring, the CPU ran at a moderate frequency (e.g., 48 MHz). During idle periods, we scaled down to 8 MHz using Zephyr's clock control API. The ADC and timer peripherals were configured to run from a low-power oscillator when possible.

**4. Battery monitoring:** A fuel gauge IC was read periodically (every 60 seconds) via I2C. If battery voltage dropped below a threshold, the device would enter a critical low-power state, disabling the RGB LED feedback and reducing sensor sampling rate to extend operation until the user could recharge.

**5. Wake-up strategy:** The device used a real-time clock (RTC) alarm for periodic wake-ups to check battery status, and a GPIO interrupt from the pressure sensor for breath detection. Between these events, the system remained in deep sleep with RAM retention.

This approach achieved the 7-day target during testing, with the device drawing approximately 50 µA in standby and peaking at 25 mA during active breath monitoring.

**Possible follow-ups:**
- How did you ensure the device could wake reliably from deep sleep within the required latency for breath detection?
- What Zephyr power management states did you use, and how did you transition between them?

---

## Q5: Compare and contrast using a bare-metal main loop versus an RTOS for a medical device that must handle sensor acquisition, user interface, and safety monitoring. When would you choose one over the other?

**Answer:** 

**Bare-metal main loop:** All tasks run sequentially in a super-loop. Timing is managed through careful scheduling and timer interrupts. Advantages include lower memory footprint (no RTOS kernel overhead), simpler debugging (no context switching surprises), and deterministic execution if well-designed. Disadvantages include difficulty handling multiple asynchronous events, poor separation of concerns, and the risk that a long-running task blocks critical safety checks.

**RTOS (like Zephyr):** Tasks run as independent threads with priority-based scheduling. Advantages include natural separation of concerns (sensor task, UI task, safety monitor task), easier handling of multiple timing domains, and built-in synchronization primitives (semaphores, mutexes, message queues). Disadvantages include kernel overhead (RAM/ROM for task stacks and kernel objects), potential for priority inversion, and more complex debugging of race conditions.

**When to choose bare-metal:** For very simple devices with a single, well-defined timing loop and minimal concurrency. For example, a basic infusion pump with a fixed-rate motor and simple button input might be fine bare-metal. Also appropriate for ultra-low-power devices where every microamp counts and the RTOS tick overhead is unacceptable.

**When to choose RTOS:** For complex medical devices with multiple concurrent responsibilities, different timing requirements, and safety-critical monitoring. The SOBA Heart Lung Support Machine is a perfect example — it needed to simultaneously control a motor (speed loop at 1 kHz), monitor biological parameters (temperature/pressure at 100 Hz), handle Wi-Fi communication (asynchronous, variable latency), and maintain a safety watchdog. An RTOS allowed us to assign priorities correctly: the safety monitor ran at highest priority, motor control at medium, sensor acquisition at medium-low, and Wi-Fi at lowest. This ensured that even if Wi-Fi communication stalled, the life-support functions continued uninterrupted.

For the Smart OPEP Device, we chose Zephyr RTOS because the device had to handle pressure sensor acquisition, RGB LED feedback animations, battery management, and Bluetooth connectivity — all with different timing requirements. The RTOS's tickless idle mode also gave us better power management than a bare-metal approach with busy-waiting.

**Possible follow-ups:**
- In an RTOS-based medical device, how do you prevent priority inversion from causing a safety-critical task to miss its deadline?
- What specific Zephyr features make it suitable for medical device firmware compared to a custom bare-metal scheduler?