# high-speed-digital-fpga — Day 3

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a design that transfers a multi-bit control word from a 100 MHz domain to a 150 MHz domain, where the control word changes infrequently but must be captured reliably?

**Answer:** For a multi-bit CDC where the source data changes infrequently, the key concern is avoiding metastability and ensuring all bits of the word are captured in the same clock cycle on the destination side. A simple synchronizer chain (two or three flip-flops) works for single-bit signals, but for multi-bit buses, individual bits may arrive at different times due to routing skew, causing the destination to capture an inconsistent value.

The standard approach is to use a handshake protocol or, more commonly, a FIFO. For infrequently changing control words, a two-register handshake works well: the source asserts a request signal (synchronized through a dual flip-flop chain in the destination clock domain), the destination captures the data word and asserts an acknowledge signal (synchronized back to the source), and the source then de-asserts the request. This guarantees the destination sees a stable word.

Alternatively, if the control word is small (e.g., 4-8 bits) and changes rarely, a gray-code encoded counter or a "valid-then-hold" scheme can work, but the handshake is more robust. I would also add a static timing analysis constraint to verify that the synchronizer flip-flops have adequate setup/hold margins, and I'd simulate the CDC paths with back-annotated delays to check for any race conditions.

**Possible follow-ups:** How would your approach change if the control word changed on every clock cycle? What CDC verification tools or methodologies have you used to catch bugs before tape-out?

---

## Q2: How would you approach selecting the appropriate I/O standard for an FPGA bank that interfaces with both a DDR3 memory (1.5V SSTL) and several general-purpose 3.3V CMOS control signals?

**Answer:** This is a common challenge because FPGA I/O banks typically require a single VCCIO voltage per bank. Mixing 1.5V SSTL and 3.3V CMOS in the same bank is generally not possible without violating the FPGA's I/O bank voltage rules. The correct approach is to partition the interfaces across separate banks.

I would assign the DDR3 interface to one or more banks powered at 1.5V, using the appropriate SSTL-15 standard with the required on-die termination (ODT) and reference voltage (VREF). The 3.3V control signals would go to a different bank powered at 3.3V, using LVCMOS33. If the FPGA has limited bank count and this separation isn't possible, I'd consider using level translators (e.g., a dedicated voltage translation IC) for the 3.3V signals, or redesigning the control interface to use 1.8V or 1.5V logic if the connected devices support it.

I'd also check the FPGA's I/O standard compatibility tables—some FPGAs allow certain voltage-tolerant inputs, but outputs always follow the bank VCCIO. For the DDR3 interface specifically, I'd ensure the selected bank supports the required DQS strobe termination and write-leveling features.

**Possible follow-ups:** What happens if you accidentally mix 3.3V and 1.5V signals in the same bank? How would you handle a situation where the PCB layout forces you to route a 3.3V signal through a 1.5V bank due to pin assignment constraints?

---

## Q3: How would you approach debugging an FPGA design where the block RAM (BRAM) contents appear corrupted after configuration, but only on about 10% of production boards?

**Answer:** This intermittent, board-dependent failure suggests a hardware issue rather than a logic error in the RTL. I'd approach this systematically:

First, I'd verify the configuration process itself—check that the FPGA configures successfully on the failing boards (e.g., DONE pin goes high, no configuration CRC errors). If configuration succeeds, the BRAM initialization values should be loaded correctly from the bitstream.

Next, I'd examine the power supply for the FPGA's BRAM array. BRAM contents can be corrupted by voltage droops during or after configuration. I'd probe the FPGA core voltage rail on a failing board during power-up and compare it to a working board, looking for excessive ripple or undershoot below the minimum operating voltage.

I'd also check for temperature effects—if the failing boards run hotter, BRAM cells can become more susceptible to noise. I'd measure the junction temperature on both passing and failing boards.

Another possibility is a marginal timing issue in the BRAM read/write paths that only manifests on certain silicon or under certain conditions. I'd run the design through static timing analysis with derated models (worst-case slow/fast corners) to see if any paths are marginal. I'd also add a test mode that writes a known pattern to BRAM and reads it back, logging any errors to help correlate failures with operating conditions.

Finally, I'd check for electromagnetic interference or ground bounce that might affect the BRAM's sense amplifiers—this could explain why only some boards fail if there are PCB manufacturing variations.

**Possible follow-ups:** How would you distinguish between a BRAM initialization issue (contents wrong from the start) versus a corruption that happens during operation? What FPGA-specific debug features (like ChipScope or Signal Tap) would you use to capture the failure?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must be immune to single-event upsets (SEUs) for a radiation-tolerant application?

**Answer:** For SEU-immune FSM design, the goal is to prevent a single bit flip in the state register from causing an illegal state transition or a hang condition. I'd use a combination of techniques:

First, I'd implement triple modular redundancy (TMR) for the state register—three identical flip-flop banks with a majority voter on the output. The voter corrects any single-bit error automatically. The flip-flops themselves should be physically separated on the die (using placement constraints) to reduce the chance of a single ionizing particle affecting multiple flip-flops.

Second, I'd encode the state using a Hamming or other error-detecting/correcting code rather than one-hot or binary encoding. For example, a (7,4) Hamming code can correct single-bit errors and detect double-bit errors in a 4-bit state. This adds some logic but reduces the flip-flop count compared to full TMR.

Third, I'd include a watchdog timer that resets the FSM to a safe state if it remains in an illegal or unexpected state for too long. This catches cases where multiple bits are upset simultaneously, overwhelming the error correction.

Fourth, I'd use a "safe state" approach where the FSM's next-state logic explicitly maps all possible state vector combinations (including illegal ones) to a known safe state or to a recovery sequence. The synthesis tool's "full_case" and "parallel_case" directives should be avoided—instead, I'd write explicit default clauses in the case statement.

Finally, I'd add periodic scrub logic that reads and corrects the state register at regular intervals, even when no transition is occurring, to prevent error accumulation.

**Possible follow-ups:** How would you verify the SEU immunity of your FSM design in simulation? What trade-offs exist between TMR, error-correcting codes, and watchdog timers in terms of area, power, and reliability?

---

## Q5: Behavioral question — You're the lead engineer on a high-speed FPGA design project. During a design review, a junior engineer presents a simulation showing the design meets timing at the slow-slow process corner but fails at the fast-fast corner. The engineer suggests ignoring the fast-fast corner because "the chip will never actually run that fast." How do you handle this situation?

**Answer:** I would first acknowledge the engineer's observation—it's true that fast-fast corners can sometimes produce overly pessimistic results, especially for hold-time analysis. However, I would explain that we cannot simply ignore any timing corner without thorough justification.

I would walk through the reasoning: fast-fast corners represent the scenario where the silicon is at its fastest (high voltage, low temperature), which can cause hold-time violations because data arrives too quickly relative to the clock. These conditions can occur during cold startup, during low-power modes, or in specific operating environments. Ignoring them risks intermittent failures in the field that are extremely difficult to reproduce and debug.

I would then propose a structured approach: first, verify that the simulation setup is correct—are the constraints accurate? Is the clock jitter modeled appropriately? Second, check if the violations are real or if they're caused by unrealistic path combinations (false paths or multi-cycle paths that aren't properly constrained). Third, if the violations are genuine, we need to fix them—typically by adding delay to the data path (e.g., inserting buffer cells or adjusting routing constraints) or by reducing the clock frequency if the specification allows.

I would also use this as a teaching moment: explain that timing analysis must cover all relevant corners per the FPGA vendor's recommendations, and that we document any corners we intentionally exclude along with the engineering rationale. This builds good habits and ensures the design is robust across all specified operating conditions.

Finally, I'd suggest we run the fast-fast analysis again with realistic derating factors (e.g., using the FPGA vendor's recommended derating for on-chip variation) to see if the violations persist under more realistic assumptions. If they do, we fix them; if not, we document the analysis and move forward.

**Possible follow-ups:** How would you explain the difference between setup and hold timing to a junior engineer who confuses the two? What would you do if the project schedule doesn't allow time to fix all the fast-fast violations before the tape-out deadline?