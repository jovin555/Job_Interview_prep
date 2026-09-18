# high-speed-digital-fpga — Day 59

## Q1: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, double-data-rate (DDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?
**Answer:** The core problem is that the forwarded clock and the data lanes travel together but not identically, so the FPGA must re-align them before capturing. I'd start by characterizing the skew budget: the ADC datasheet gives a data-to-clock skew window (tSKEW or similar), and I'd add PCB trace-matching tolerance, connector skew, and the FPGA input delay uncertainty. That total window has to fit inside one bit period with margin left for setup/hold and jitter.

The standard approach is to use the FPGA's input delay elements (IDELAY/IDELAYE) or a dedicated source-synchronous capture primitive. I'd bring the forwarded clock into a global or regional clock-capable pin, route it through a BUFIO/BUFR or MMCM as appropriate, and then use per-lane delay taps to center the sampling point in the data eye. For DDR, the capture logic uses both edges of the forwarded clock, so I need to be careful about duty-cycle distortion on the forwarded clock itself — if the ADC's clock output has significant duty-cycle error, the two edges won't be evenly spaced and the effective eye shrinks.

For calibration, I'd implement a training pattern: the ADC (or a test mode) sends a known PRBS or a fixed pattern, and the FPGA sweeps the IDELAY taps per lane, measuring where the captured data is correct. The center of the passing region is the optimal tap. This is essentially the same idea as read-leveling in a DDR memory interface, applied to the ADC link. I'd also add a per-lane eye monitor if the FPGA supports it, so I can track drift over temperature and voltage.

One important detail: the forwarded clock and data must be routed as a matched group on the PCB, with the clock typically routed slightly longer or shorter depending on the FPGA's internal clock insertion delay. The board designer needs the FPGA's clock-to-data timing numbers to set that offset correctly.

**Possible follow-ups:**
- How would you handle the case where the ADC's forwarded clock has a non-50% duty cycle, and how does that affect your DDR capture?
- If the skew is large enough that a single IDELAY range can't cover it, what alternatives would you consider?

## Q2: How would you approach debugging an FPGA design where the transceiver link passes its built-in PRBS checker at the physical layer, but application-level data is occasionally corrupted, and the corruption only appears at full line rate?
**Answer:** The fact that PRBS passes tells me the physical layer — SerDes, CDR, equalization, clock recovery — is fundamentally working. The corruption is happening above the physical layer, in the datapath between the transceiver's parallel interface and the application logic. That narrows the search considerably.

First, I'd check the transceiver's internal FIFO and clock domain crossing. The transceiver's recovered clock domain and the FPGA fabric clock domain are asynchronous, so there's a CDC inside or immediately after the transceiver. If that CDC is marginal — for example, if the FIFO depth is too small for the phase drift between the two clocks, or if the CDC handshake is incorrect — errors will appear intermittently and correlate with traffic patterns. At full line rate, the FIFO fills faster and the phase relationship between the two clocks drifts more per unit time, which would explain why it only shows up at full rate.

Second, I'd look at the datapath's backpressure and flow control. If the application logic can't sustain the line rate, the transceiver's FIFO will overflow or underflow, and depending on how the overflow is handled, it may corrupt data silently. I'd check whether the transceiver's status flags (overflow, underflow, disparity error) are being monitored and whether they're being cleared correctly.

Third, I'd check the framing and alignment logic. If the application uses a packet or frame structure, a single bit error at the physical layer could cause a frame alignment error that propagates. But since PRBS passes, physical-layer bit errors should be rare — so I'd focus on the framing logic's handling of idle codes, comma characters, or alignment markers.

For debugging, I'd use the transceiver's built-in error counters and eye monitor, and I'd add a logic analyzer or embedded debug core to capture the datapath around the transceiver. I'd also try running at a reduced line rate to see if the corruption disappears — if it does, that strongly points to a timing or FIFO margin issue rather than a logic bug.

**Possible follow-ups:**
- How would you distinguish between a transceiver FIFO overflow and a CDC error in the datapath?
- What would you check in the transceiver's configuration if the error rate scales with line rate but not with data pattern?

## Q3: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 5 clock cycles at 400 MHz), while also being robust against single-event upsets (SEUs)?
**Answer:** These two requirements — strict latency and SEU robustness — pull in opposite directions, so the design has to be deliberate about where it spends its budget.

For latency, the FSM must be shallow. A one-hot or binary encoding with a small number of states, and combinational next-state logic that resolves in a single clock cycle, is the starting point. I'd avoid deep pipelines in the decision path and instead push complexity into parallel lookup structures (CAMs, BRAM-based tables) that can be accessed in one or two cycles. The FSM itself should be a simple sequencer: receive header, look up forwarding entry, emit decision. Five cycles at 400 MHz is 12.5 ns, which is tight but achievable if the FSM doesn't try to do too much per state.

For SEU robustness, the classic approach is triple modular redundancy (TMR) on the state register: three copies of the state, majority-voted on every clock. That adds area and a voter delay, but the voter is combinational and shallow, so it doesn't add pipeline stages. The alternative is a Hamming or SECDED code on the state register, which detects and corrects single-bit errors but adds encode/decode logic in the path — usually worse for latency than TMR.

A more subtle issue is that SEUs can hit the next-state logic, not just the state register. Full TMR of the FSM (state register, next-state logic, and output logic) is the standard for radiation-tolerant designs, but it triples the logic area. If the latency budget is too tight for full TMR, a compromise is to TMR only the state register and use a safe-state recovery mechanism: if the FSM ever enters an illegal state, it forces a reset to a known state. That doesn't prevent the error but bounds its impact.

I'd also consider whether the FSM needs to be SEU-robust at all in this context. If the device is in a radiation environment, yes. If it's a terrestrial application, SEUs are rare enough that a watchdog and periodic state check may be sufficient. The answer depends on the environment, and I'd want to clarify that before committing to TMR.

**Possible follow-ups:**
- How would you verify that the TMR FSM actually recovers from an injected SEU, and what would you inject?
- If the latency budget can't accommodate TMR, what alternative mitigation would you propose?

## Q4: How would you approach designing the decoupling and bulk capacitance network for an FPGA's transceiver power rails, where the rails have both high-frequency switching noise and slower, larger current transients, and how would you verify the network is adequate before committing to the layout?
**Answer:** Transceiver rails are among the most demanding on an FPGA board because they combine high-frequency switching noise from the SerDes output stages with slower, larger transients from the transceiver's internal PLLs and clock recovery circuits. The decoupling network has to handle both.

I'd start by separating the two frequency regimes. For high-frequency noise — the kind that comes from the SerDes output drivers switching at the line rate — the decoupling capacitors need to be as close to the FPGA's power pins as possible, with minimal loop inductance. That means small-case-size ceramic capacitors (0201 or 0402) with low ESL, placed on the same side of the board as the FPGA, with short, wide traces to the power and ground planes. The goal is to keep the impedance of the power delivery network low at the frequencies where the transceiver draws its switching current.

For slower transients — the kind that come from the transceiver's PLLs locking or from the device entering and leaving low-power states — bulk capacitance provides the charge reservoir. The bulk capacitors can be further away because the transient is slower, but they still need to be connected with low-impedance traces or planes. The value and number of bulk capacitors depend on the transient magnitude and the acceptable voltage droop, which I'd estimate from the transceiver's current profile in the datasheet.

The verification step is where a lot of designs go wrong. Before committing to layout, I'd model the PDN as an impedance network — the FPGA's current draw as a current source, the decoupling capacitors as their equivalent series RLC, and the voltage regulator as its output impedance. I'd simulate the impedance versus frequency and check that it stays below a target (typically derived from the allowable ripple and the current transient) across the frequency range of interest. If there's a peak in the impedance at a frequency where the transceiver draws current, that's a problem.

After layout, I'd verify with a vector network analyzer or a PDN analyzer if available, measuring the actual impedance of the assembled board. If that's not possible, I'd at least measure the voltage ripple on the rail under realistic transceiver traffic and check it against the datasheet's tolerance.

**Possible follow-ups:**
- How would you determine the target impedance for the transceiver rail, and what factors would you include?
- If the measured ripple exceeds the specification, what would you change first — the bulk capacitance, the high-frequency decoupling, or the regulator?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?
**Answer:** This is a classic CDC violation, and the engineer's reasoning — that the signal is stable long enough — is exactly the kind of assumption that leads to intermittent, hard-to-debug failures in the field. I'd handle it in a way that corrects the design without discouraging the engineer.

First, I'd acknowledge that the intuition isn't unreasonable: if the signal really is stable for many cycles of the destination clock, a direct connection will often work. The problem is that "often" isn't a specification. Metastability is a probabilistic phenomenon — the flip-flop can enter a metastable state if the input changes within the setup/hold window, and while the probability is low, it's not zero. Over millions of boards and years of operation, that probability becomes a real failure rate. And the failure mode is nasty: the destination logic may see a value that's neither 0 nor 1, or may resolve differently on different paths, leading to inconsistent behavior.

Second, I'd explain the correct approach. For a single-bit control signal, a two-flop synchronizer is the standard solution: the signal is captured by the first flip-flop in the destination domain, then by a second flip-flop, and the second flip-flop's output is used by the destination logic. The first flip-flop may go metastable, but the second flip-flop gives the metastability time to resolve before the signal is used. For a multi-bit bus, a two-flop synchronizer per bit isn't enough — the bits can resolve on different cycles, producing a corrupted value. That requires a handshake, a FIFO, or a gray-coded counter, depending on the data.

Third, I'd make it a teaching moment rather than a criticism. I'd ask the engineer to walk through what happens if the signal changes exactly at the destination clock edge, and let them reason through the metastability scenario. Often, engineers who haven't encountered metastability firsthand don't realize it's a real effect, not a theoretical one. I'd also point them to the FPGA vendor's CDC guidelines and the synthesis tool's CDC checks, which can catch these violations automatically.

Finally, I'd make sure the fix is verified. I'd ask the engineer to add the synchronizer, re-run the CDC checks, and if possible, add a test that exercises the CDC under conditions that would expose metastability — though in practice, metastability is hard to reproduce in simulation, so the verification is mostly about ensuring the synchronizer is correctly implemented and the CDC tool reports no violations.

**Possible follow-ups:**
- How would you explain the difference between a two-flop synchronizer and a handshake-based CDC to an engineer who's new to the concept?
- What would you do if the engineer pushed back, arguing that the synchronizer adds latency that the design can't afford?