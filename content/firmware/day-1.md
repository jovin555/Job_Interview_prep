# firmware — Day 1

## Q1: What is the difference between a task and a semaphore in a real-time operating system like Zephyr RTOS, and when would you choose one over the other?

**Answer:** A task (or thread) is an independent execution context with its own stack and scheduling priority — it runs code. A semaphore is a kernel synchronization object used to signal between tasks or to guard access to a shared resource. In Zephyr RTOS, you'd use a task when you need a continuous execution loop (e.g., a sensor reading thread that runs every 10 ms), and a semaphore when you need one task to wait for an event from another task or an ISR. For example, on the **Smart OPEP Device** project, we had a pressure sensor task that would release a semaphore when a valid breath event was detected. A separate LED control task would pend on that semaphore to trigger the RGB feedback — this decoupled the sensor polling from the visual response and avoided busy-waiting.

**Possible follow-ups:**
- How does Zephyr's semaphore implementation differ from a binary semaphore in FreeRTOS?
- What happens if a semaphore is given from an ISR — any special handling needed?

---

## Q2: Explain how you would implement a watchdog timer in firmware for a medical device, and why it's critical for IEC 60601 compliance.

**Answer:** In medical devices, a watchdog timer (WDT) is a hardware or software mechanism that resets the system if the firmware stops responding — this is required under IEC 60601 for fail-safe operation. On the **Lotus (Printer and Toco)** project, we implemented a hardware watchdog using an external watchdog IC (not just the internal MCU watchdog) because IEC 60601 requires independent redundancy. In firmware, we'd configure the WDT timeout (e.g., 1 second) and then "pet" the watchdog in the main loop or a high-priority task. Critically, we structured the petting to only happen after key health checks passed: the sensor acquisition task was alive, the communication stack was responsive, and no critical fault flags were set. If the firmware hung during a print operation or sensor read, the watchdog would trigger a system reset and log the event for post-mortem analysis. This was validated during IEC 60601 testing as part of the risk management file.

**Possible follow-ups:**
- What happens if you pet the watchdog in an ISR — is that safe?
- How do you test that the watchdog actually works during production?

---

## Q3: Describe a situation where you had to debug a firmware issue that only occurred intermittently. How did you approach it?

**Answer:** During the **SOBA — Heart Lung Support Machine** project, we had an intermittent issue where the Wi-Fi communication to the tablet would drop out randomly after 30–60 minutes of operation. The system used a Zephyr-based STM32 with an external Wi-Fi module over UART. The issue was difficult to reproduce in the lab. I approached it systematically: first, I added debug logging with timestamps around the Wi-Fi driver calls and the UART receive buffer. I also used a logic analyzer to capture the UART traffic during a failure event. The logs showed that the UART RX buffer was overflowing during high motor-speed control activity. The root cause was that the motor control PWM interrupt had a higher priority than the UART RX interrupt, and during heavy motor load, the UART ISR was delayed long enough to lose bytes. The fix was to increase the UART RX buffer size and implement a circular buffer with flow control, then re-test over 8-hour continuous runs. This was documented in our 8D root-cause investigation process.

**Possible follow-ups:**
- What tools did you use to capture the UART traffic?
- How did you verify the fix didn't introduce new timing issues?

---

## Q4: What is the purpose of a bootloader in an embedded medical device, and what considerations are unique to medical firmware updates?

**Answer:** A bootloader is a small program that runs at power-on to validate and load the main application firmware. In medical devices, it's critical for field-updatable firmware without opening the device (reducing contamination risk) and for recovery from a corrupted application. On the **Smart OPEP Device**, we implemented a dual-bank bootloader in Zephyr: Bank 0 held the current firmware, Bank 1 held the update image. The bootloader would check a CRC32 of the application before jumping to it. Medical-specific considerations included: (1) the update must be atomic — if power is lost mid-update, the bootloader must fall back to the previous known-good firmware; (2) the update process must be authenticated (signed firmware images) to prevent malicious code; (3) the bootloader itself must be in write-protected flash to prevent accidental corruption; (4) the device must not enter an unsafe state during the update (e.g., if it's a respiratory device, it should fail to a safe state like "off" rather than delivering incorrect therapy). These were all documented in our risk management file per IEC 60601.

**Possible follow-ups:**
- How do you handle the case where both banks are corrupted?
- What's the difference between a bootloader and a firmware monitor?

---

## Q5: Walk me through how you would structure the firmware for a battery-powered medical device that needs to run for 7 days continuously, like the Smart OPEP Device.

**Answer:** For the **Smart OPEP Device**, which required 7 days of continuous use on a Li-ion battery, the firmware architecture was built around aggressive power management. The structure was:

1. **State machine architecture**: The main application ran as a state machine — SLEEP, IDLE, ACTIVE_THERAPY, CHARGING, ERROR. In SLEEP mode, the MCU entered deep sleep (Zephyr PM_STATE_SUSPEND_TO_RAM), waking only on a real-time clock interrupt every 100 ms to check for button presses or a scheduled therapy session.

2. **Peripheral power gating**: The pressure sensor, RGB LEDs, and Wi-Fi module each had independent power FETs controlled by GPIO. The firmware would power down the sensor completely between readings (only powering it 50 ms before a measurement), and the Wi-Fi module was only powered on during data sync windows (every 4 hours).

3. **Sensor sampling strategy**: Instead of continuous sampling, we used a duty-cycled approach — sample pressure at 100 Hz for 2 seconds during a breath, then sleep for 8 seconds. The ADC was configured for single-shot conversion with automatic shutdown.

4. **Battery monitoring**: A fuel gauge IC communicated over I2C. The firmware checked battery level only when the device woke from sleep, not during active therapy, to avoid drawing extra current.

5. **RTOS tick optimization**: We configured Zephyr's tickless idle mode so the kernel didn't wake unnecessarily. The idle thread would enter the deepest sleep state allowed by pending timers.

This architecture achieved the 7-day target during validation testing, with the device consuming approximately 15 µA in sleep mode and 45 mA during active therapy.

**Possible follow-ups:**
- How did you measure the actual power consumption to validate your estimates?
- What happens if the battery gets critically low during a therapy session?