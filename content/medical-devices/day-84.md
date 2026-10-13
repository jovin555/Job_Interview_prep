# medical-devices — Day 84

## Q1: How would you approach designing the analog front-end for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the baseline drift is orders of magnitude larger than the signal, so a single DC-coupled gain stage would either saturate or waste most of the ADC's codes on the baseline. I'd structure the chain in stages. First, an instrumentation amplifier or a low-noise differential front-end with high common-mode rejection, because much of the "baseline" is common-mode in nature and rejecting it early keeps later stages from having to handle it. Second, a high-pass stage or AC-coupling with a corner frequency chosen well below the signal band but high enough to track the drift — the trade-off is that too high a corner distorts the low-frequency content of the signal, so I'd set it from the signal's actual spectral content, not by habit. Third, gain and anti-alias filtering ahead of the ADC, with the ADC's reference and input range matched to the post-filter signal swing so I'm using as many codes as possible.

Verifiability is a design constraint, not an afterthought. I'd define the accuracy budget up front — noise, offset, gain error, drift over temperature, and ADC quantization — and allocate a portion to each stage so the total is provably within spec. That means specifying the front-end in terms of input-referred noise and input-referred offset, because those are the numbers that actually determine whether the accuracy limit is met. I'd also make sure the design can be characterized: a test injection point at the input, and a way to measure the chain's transfer function and noise floor independently of the sensor. If the sensor itself is the dominant error source, no amount of front-end cleverness fixes it, so I'd want to know early which side of the budget dominates.

**Possible follow-ups:**
- How would you decide between AC-coupling and a DC servo loop to handle the baseline drift?
- How would you verify the input-referred noise spec on the bench without a specialized low-noise source?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended clinical function and its classification, not from a keyword search of standard titles. The general standard, IEC 60601-1, always applies. The collateral standards — 60601-1-2 for EMC, 60601-1-6 for usability, 60601-1-8 for alarms, 60601-1-11 for home healthcare, and so on — apply based on the environment and features the device has. The particular standards in the 60601-2 series apply based on what the device actually is and does. For a combined-function device, it's common for more than one particular standard to apply, and the honest answer is that you may need to comply with both, taking the more stringent requirement where they overlap.

Resolving conflicts is a documentation exercise as much as a technical one. I'd build a requirements matrix that lists each applicable clause from each standard, maps it to the design feature or test that satisfies it, and flags any place where two standards appear to demand different things. Where they genuinely conflict, the particular standard typically takes precedence over the general standard for that specific aspect, but I wouldn't assume that — I'd confirm with the test lab or a regulatory specialist, and record the rationale. The key is that this analysis happens during design input, not during test, because discovering a second applicable particular standard after the design is frozen is expensive. I'd also keep the applicability rationale in the DHF so a reviewer can see why each standard was included or excluded.

**Possible follow-ups:**
- How would you handle a case where a particular standard's test method doesn't map cleanly onto your device's architecture?
- Who would you involve in making the final call on applicability, and how would you document it?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd design against is the risk file that gets written backwards — after the design is done, to satisfy an auditor. That produces a file that's technically complete but disconnected from the actual engineering decisions, and it tends to miss hazards that were quietly designed around. So I'd treat the risk management file as a living artifact that's updated at the same cadence as the design, with each design review touching the risk analysis.

Structurally, I'd keep it traceable in both directions. Each hazard links to the harm it could cause, the foreseeable sequence of events, the risk estimate, the risk control measure, and the verification that the control is effective. Each risk control links back to a design input or a specific test, so there's a thread from "we identified this hazard" to "here's the evidence the control works." I'd use a consistent identifier scheme so cross-references stay stable as the design changes, and I'd version the file so it's clear what was known at each design stage.

The practical discipline is to make the risk review part of every design change, not a separate gate. When a design decision changes — a component swap, a firmware behavior change, a new use environment — the question "does this introduce or retire a hazard?" gets asked in the same meeting. I'd also keep the residual risk acceptance explicit and signed off, because that's the part auditors scrutinize most. And I'd avoid over-engineering the file: a risk entry that's too granular to maintain gets abandoned, so I'd aim for a level of detail that a new engineer could actually keep current.

**Possible follow-ups:**
- How would you handle a hazard that's identified late, after the design is largely frozen?
- How do you keep the risk file consistent with the DHF without duplicating content in both?

## Q4: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band, reproducible failure is a strong clue — it points to a resonance or a specific coupling path rather than a general susceptibility problem. I'd start by characterizing the failure precisely: what exactly malfunctions, at what field strength, with what orientation of the device relative to the field, and with what cabling configuration. The orientation and cable setup matter enormously, because a narrow-band failure often depends on the effective antenna formed by a cable or a board trace at that wavelength.

From there I'd work the coupling path. Is it conducted in through a cable, or radiated directly onto the board or into an enclosure seam? I can often separate these by testing with cables dressed differently, with ferrites added temporarily, or with the enclosure partially shielded. If the frequency corresponds to a quarter-wave or half-wave resonance of a cable or a trace, that's a strong indicator. On the board, I'd look at whether the frequency aligns with a resonance of a ground plane, a decoupling network, or a signal loop.

The fix depends on the mechanism. If it's a cable acting as an antenna, common-mode chokes, ferrites, or a change in cable routing or shielding may resolve it. If it's direct coupling into a sensitive node, filtering or layout changes at that node — shortening loops, improving return paths, adding a small filter — are more appropriate. If it's a firmware-visible malfunction, I'd also consider whether the firmware can detect and recover from the upset, but that's a mitigation, not a substitute for reducing the coupling. I'd verify the fix at the specific failing frequency first, then re-run the full sweep to make sure I haven't shifted the problem elsewhere.

**Possible follow-ups:**
- How would you distinguish a resonance in the cable from a resonance on the PCB?
- If the fix requires a board change, how would you decide whether to respin or to mitigate with an enclosure or cable change?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first move is to understand what problem the clinical team is actually trying to solve, because the requested change is often one solution to a need that might have other solutions. I'd ask what clinical scenario drove the request, how often it occurs, and what the consequence is if it isn't addressed. That tells me whether this is a safety-relevant usability issue, a workflow efficiency issue, or a preference — those have very different weights.

Then I'd assess the cost honestly and in options, not as a single yes/no. A hardware revision that pushes submission by months is one option; a firmware-only change that addresses most of the need is another; a change to labeling, training, or the user interface within the existing hardware is a third; deferring to a post-market update is a fourth. I'd bring those options back to the clinical team and to the project leadership with the trade-offs stated plainly — schedule, cost, regulatory impact, and residual clinical risk if we don't act.

The decision itself isn't mine alone to make, and I'd be clear about that. If the change addresses a genuine use-related hazard, that's a risk management input and it may need to happen regardless of schedule. If it's a usability improvement without a safety dimension, it's a business and schedule trade-off that the project owner and clinical stakeholders should decide with full information. What I'd avoid is either silently absorbing the change and blowing the schedule, or reflexively refusing it and leaving a real clinical need unaddressed. I'd document the decision and its rationale either way.

**Possible follow-ups:**
- How would you tell the difference between a usability preference and a use-related safety hazard?
- If the decision is to defer the change, how would you make sure it's captured and tracked rather than lost?