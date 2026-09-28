# tools — Day 69

## Q1: How would you approach setting up a test and measurement bench for bring-up of a new mixed-signal medical device prototype, deciding which instruments to dedicate versus share, and how would you keep the setup repeatable across multiple engineers?

**Answer:** I'd start by listing the measurement domains the bring-up actually needs — power rails, digital buses, analog front-end noise, RF/EMI pre-checks, and thermal — then map instruments to those domains rather than buying "one of everything." A dedicated bench typically needs a 4-channel mixed-signal oscilloscope with adequate bandwidth and a good differential/active probe set, a bench DMM with decent resolution, a programmable DC supply with accurate current readback and logging, and a logic analyzer or MSO digital channels for protocol work. Shared or booked resources — spectrum analyzer with near-field probes, thermal camera, LCR meter, SMU — make sense because they're used in bursts, not continuously.

The repeatability piece matters more than the shopping list. I'd standardize probe types and grounding accessories at each station (ground springs, not long ground leads), label instruments with calibration due dates, and keep a bench log or checklist so a second engineer can reproduce a measurement without guessing which probe or coupling setting was used. For anything that will feed a regulatory or design-review conclusion, I'd want the instrument settings, probe model, and firmware version recorded alongside the data — otherwise the measurement isn't defensible later. I'd also physically separate the "noisy" side (switching supplies, motor drivers) from the sensitive analog measurement area to avoid contaminating low-level measurements before they even reach the scope.

**Possible follow-ups:**
- How would you decide the minimum oscilloscope bandwidth for a design with a 100 MHz clock and fast switching edges?
- What would you put in a bench setup checklist to make sure two engineers get comparable measurements?

## Q2: How would you approach configuring a Segger J-Link for a Zephyr RTOS target where an automated test harness needs to flash the device, run a test sequence, and capture a crash dump without manual intervention — and what failure modes would you design around?

**Answer:** The goal is a headless, scriptable flow, so I'd drive the J-Link through its command-line/scripting interface rather than the IDE GUI. The harness would: reset and halt the target, flash the built image (using the same artifact the release process produces, not a locally rebuilt one), reset and run, then either poll for a completion signal or wait a bounded time before reading back results. For crash capture, I'd configure the debugger to halt on fault and dump the relevant memory regions — fault status registers, stack, and any RAM-resident log buffer — to a file the harness can archive.

The failure modes are where the real design work is. Connection failures (target not powered, SWD pins repurposed, clock not running) need a retry with a hard power-cycle rather than an infinite hang. Flash failures need verification after programming, not just a "success" return code. A target that never reaches the expected state needs a timeout that still captures whatever state it's in — a hung target is often more informative than a clean pass. And the harness must not silently pass when the debugger itself failed to attach; that's the classic false-positive. I'd also make sure the flow is idempotent so a re-run after a failure doesn't depend on leftover state, and log the J-Link firmware/driver version since that can change behavior between machines.

**Possible follow-ups:**
- How would you distinguish a genuine firmware crash from a debugger attach failure in the captured data?
- What would you change if the same harness had to run against several hardware revisions with different memory maps?

## Q3: How would you approach using a power integrity simulation workflow for a mixed-signal PCB where a high-current switching regulator and a precision analog front-end share the same power distribution network, and how would you decide which results are trustworthy enough to act on?

**Answer:** I'd treat it as a two-part problem: the DC/IR-drop side and the AC/impedance side. First, model the power distribution network — copper pours, plane splits, via arrays, and the regulator's output network — and run a DC analysis to find resistive drop and current-density hotspots, especially where the high-current path and the analog supply share copper. Then run an AC impedance sweep of the PDN from the regulator output to the analog load, looking for resonances where the impedance peaks. The switching regulator's ripple and its harmonics are the excitation; if a PDN resonance lines up with a switching harmonic, that's a coupling path worth fixing before layout is frozen.

Deciding what to trust is the harder judgment. Simulation results are only as good as the stackup, material properties, and component models — so I'd validate the model against a measurement on a known-good board or a test coupon before acting on marginal results. I'd act confidently on gross problems (a clear IR-drop violation, a resonance well inside the regulator's harmonic band) and treat anything within a few dB of the target as "verify on the bench." I'd also cross-check with a simpler hand calculation or a rule-of-thumb decoupling estimate — if the simulation and the back-of-envelope disagree wildly, the model is probably wrong, not the physics.

**Possible follow-ups:**
- How would you decide where to place bulk versus high-frequency decoupling once the PDN impedance curve is known?
- What measurement would you use on the first prototype to confirm or refute the simulation?

## Q4: How would you approach setting up a cross-probe workflow between OrCAD Capture and Cadence Allegro so a layout review can move efficiently between schematic and PCB, and what would you check to confirm the link actually works before relying on it in a review?

**Answer:** Cross-probing depends on the two tools sharing a consistent design database and matching reference designators, so the first step is confirming the schematic and layout are from the same netlist revision — a stale link is worse than no link because it silently points at the wrong part. I'd set up the cross-probe preferences so a selection in Capture highlights the corresponding component, net, or pin in Allegro, and vice versa, and decide up front whether the review will drive from the schematic (find a net, inspect its routing) or from the layout (click a part, jump to its schematic page).

Before the review, I'd run a quick sanity check: select a known component in Capture and confirm Allegro highlights the correct footprint, then select a net in Allegro and confirm Capture jumps to the right page and net. I'd also verify that net highlighting propagates correctly across the whole net, not just the pin, since a partial highlight can mislead a reviewer into thinking a connection is missing. If the link is flaky — wrong part highlighted, no response — I'd stop and fix it rather than push through, because a review that trusts a broken cross-probe will miss real issues. Having the netlist and design revision pinned for the review session keeps everyone looking at the same thing.

**Possible follow-ups:**
- What would you do if cross-probing works for components but not for nets?
- How would you run a review where some participants only have the schematic and others only the layout?

## Q5: (Behavioral) Imagine you're leading a project where a junior engineer has set up the Altium Designer output job configuration for a medical device PCB release, and you discover the fabrication outputs are missing the drill table and the assembly drawings reference an outdated revision of the schematic. The board house is expecting the files tomorrow, and the engineer is confident the outputs are complete because "the Gerbers look fine." How would you handle this situation?

**Answer:** First I'd separate the two problems: the immediate release risk and the process gap that let it happen. On the immediate side, I'd verify exactly what's wrong — confirm the drill table is genuinely absent from the fabrication package and check which schematic revision the assembly drawings actually reference against the current released revision. Then I'd fix the outputs and re-run the output job, treating "the Gerbers look fine" as insufficient evidence: Gerbers alone don't carry drill data or assembly documentation, so the check has to be against the full release checklist, not one file type.

On the people side, I'd avoid framing this as the engineer's failure in front of the team. The more useful conversation is "here's what a complete release package contains and how we verify it," because the gap is almost certainly that no one had shown them the full checklist — a junior engineer optimizing for "the Gerbers render correctly" is doing what they were taught. I'd walk through the output job together, show what each output is for, and add a verification step to the release process so the package is checked against a defined list before it goes out, not against one engineer's confidence. If the schedule genuinely can't absorb a full re-verification, I'd at least confirm the drill data and assembly revision are correct before the files go out, and flag the rest for a follow-up review — but I wouldn't ship a package I know is incomplete just because the deadline is tight, especially on a medical device where the documentation is part of the deliverable.

**Possible follow-ups:**
- How would you build a release checklist that catches this class of error without becoming a bottleneck?
- If the board house had already started fabrication on the incomplete package, what would your next steps be?