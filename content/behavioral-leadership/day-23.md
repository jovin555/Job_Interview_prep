# behavioral-leadership — Day 23

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between hardware and firmware teams. The first step is to gather as much field data as possible — device logs, error codes, environmental conditions at time of failure, and any patterns in when the issue occurs. I'd look for discriminating evidence: does the problem correlate with temperature, battery state, or device age (suggesting hardware), or with specific firmware versions, operating modes, or timing patterns (suggesting software)?

Once we have data, I'd design targeted experiments to separate the two hypotheses. For example, if the sensor hardware were at fault, we'd expect to see the raw ADC readings deviate from expected ranges before the filtering stage. If the filtering algorithm were at fault, raw readings would look correct but the processed output would be wrong. I'd work with the firmware team to add temporary diagnostic logging that captures both raw and filtered values, and with the hardware team to characterize sensor behavior under controlled conditions.

I'd also apply a structured root-cause framework — 5 Whys or fishbone — to map out all plausible failure paths systematically rather than jumping to the most likely culprit. The key is to avoid anchoring on one hypothesis too early. I'd document everything we try and what we learn, because in a medical device context, that investigation trail becomes part of the corrective action record.

If the two teams are already polarized, I'd make it explicit that we're not assigning blame — we're collecting evidence. I'd set a review cadence where we present findings, not opinions, and I'd make sure both teams have equal input into the test plan so neither feels their concerns were dismissed.

**Possible follow-ups:**
- How would you decide when you have enough evidence to commit to one root cause versus continuing to investigate?
- What if the field data is sparse and you can't reproduce the issue in the lab — how would you proceed?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a "shared resources, multiple priorities" mindset. I'd start by assessing the current skill matrix across the team — who has deep expertise in what, and where there are adjacent skills that could be developed. I'd then map the upcoming projects against that matrix to identify where we have critical dependencies on single individuals and where cross-training would have the highest impact.

I'd structure the roadmap in phases. First, establish shared infrastructure — common design guidelines, reusable hardware blocks, standardized documentation templates — so that engineers moving between projects don't have to reinvent processes. Second, implement a deliberate cross-training program where each engineer spends time on a secondary project, starting with low-risk tasks and gradually increasing responsibility. Third, create a knowledge-sharing cadence — technical brown bags, design review participation across projects, and pair design sessions — so expertise transfers naturally rather than through formal documentation alone.

A critical piece is managing the transition without overloading people. Deep specialists can't become generalists overnight, and forcing it would degrade quality. I'd identify "T-shaped" growth paths — maintaining depth in one area while building working breadth in another — and set realistic timelines. I'd also work with project managers to ensure staffing plans account for the learning curve; you can't put a power supply specialist on a firmware task and expect the same velocity.

Finally, I'd make the benefits visible. Multi-project flexibility isn't just about organizational efficiency — it's about career growth for the engineers. Being the only person who understands a critical subsystem can be flattering, but it's also a career trap. I'd frame cross-training as professional development, not just a business need.

**Possible follow-ups:**
- How would you handle an engineer who resists cross-training because they feel it dilutes their expertise?
- How would you measure whether the transition is actually working, beyond just project delivery dates?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a risk characterization problem rather than a design conflict. Both teams have legitimate concerns — the firmware team sees an opportunity for meaningful battery life improvement, and the hardware team is worried about a real failure mode: analog settling time after power state transitions. The right response is to design a test strategy that directly addresses the hardware team's concern while giving the firmware team the data they need to validate their approach.

First, I'd define the specific failure modes we're worried about. When the device wakes from sleep, what happens to the sensor reference voltage? How long does it take for the ADC to produce stable readings? Is there a risk of corrupted data being logged or displayed during the settling window? I'd work with both teams to define acceptance criteria — for example, sensor readings must be within specified accuracy within X milliseconds of wake-up, and no data outside that window should be used for clinical decisions.

Then I'd design a multi-phase test plan. Phase one would be bench-level characterization: using a scope and data logger to capture the actual wake-up transient behavior across temperature and battery voltage ranges. Phase two would be a firmware-level test where we deliberately vary the settling delay and observe the impact on measurement accuracy. Phase three would be a system-level test simulating real usage patterns — repeated sleep/wake cycles over days — to catch any cumulative effects like capacitor drift or charge pump instability.

I'd also build in a fail-safe: regardless of test results, the firmware should have a "data valid" flag that gates when sensor readings are used, so even if settling time varies with temperature or aging, the system never acts on unstable data. This turns the disagreement into a design requirement rather than a compromise.

**Possible follow-ups:**
- How would you handle it if the test results show the sleep mode causes marginal but acceptable instability — how would you decide whether to proceed?
- How would you ensure the test strategy itself doesn't add significant schedule risk to the project?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by separating the technical debate from the interpersonal dynamics. The architect has made a deliberate choice, and the senior engineers have legitimate concerns — my job is to ensure the decision is made on evidence, not on who argues most persuasively.

First, I'd ask the architect to walk through the rationale for the modular approach: what drove the decision? Likely reasons might include isolation of safety-critical functions, independent firmware development tracks, or specific performance requirements that a single processor can't meet. Then I'd ask the skeptics to articulate their concerns concretely: is it about reliability (more interconnects, more failure points), complexity (more code to integrate, more debugging effort), or something else?

The key is to convert opinions into testable criteria. I'd propose we evaluate both architectures against a defined set of requirements: safety integrity, worst-case latency for critical functions, power consumption, development effort, testability, and long-term maintainability. Where possible, I'd suggest prototyping or simulation to resolve specific uncertainties — for example, if the concern is CAN-FD bus loading, we can model the traffic and measure worst-case latency.

I'd also consider the regulatory angle. In a medical device, the architecture affects the risk management file, the fault tree analysis, and the verification strategy. A modular design might actually simplify safety certification if it allows independent fault containment — or it might complicate it if the communication protocol introduces new failure modes. I'd bring in the quality/regulatory perspective early rather than treating this as a purely technical decision.

If the disagreement persists after the analysis, I'd make a call based on the evidence and document the rationale thoroughly — including the dissenting views. In a medical device context, the decision record matters as much as the decision itself. I'd also set a checkpoint: if the chosen architecture hits specific problems during development, we revisit the decision with the data we've gathered.

**Possible follow-ups:**
- How would you handle it if the architect is more senior than you and resistant to having their decision challenged?
- What specific criteria would you use to decide between the two architectures, and how would you weight them?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is fundamentally about psychological safety, and it has to be modeled from the top. Engineers won't raise concerns if they've seen people dismissed or penalized for doing so. I'd start by being explicit about expectations: in design reviews and project meetings, I'd state that raising a concern — even a vague one — is not just acceptable but expected. I'd thank people for raising concerns, even when they turn out to be unfounded, because the cost of a false alarm is far lower than the cost of a missed issue.

I'd also create structured mechanisms that lower the barrier to speaking up. For example, a "concern log" where anyone can anonymously or openly register a worry about a design decision, with a commitment that each entry gets a response — even if the response is "we considered this and here's why we're proceeding." This is particularly useful for junior engineers who might feel intimidated in a room full of senior people.

For gut feelings specifically, I'd teach a framework for converting intuition into testable hypotheses. A gut feeling usually has an underlying technical basis — maybe the engineer has seen a similar design fail before, or something about the approach feels off even if they can't articulate why. I'd encourage them to ask questions like "What would we expect to see if this concern were valid?" or "What test would give us confidence this isn't an issue?" This turns the conversation from "I have a bad feeling" to "I think we should verify X."

I'd also watch for the opposite failure mode — concerns raised so late that they cause significant rework. The goal isn't just to let people speak up; it's to catch issues early. I'd reinforce that raising a concern at the concept stage is more valuable than raising it at the verification stage, and I'd celebrate early catches publicly.

Finally, I'd be careful about how senior people respond to challenges. If a senior engineer dismisses a junior's concern, I'd address that directly — not by embarrassing the senior engineer, but by modeling a curious response: "That's an interesting point — let's explore what might be behind it." Over time, this sets the norm that all concerns get a thoughtful response.

**Possible follow-ups:**
- How would you handle a situation where someone raises the same concern repeatedly after it's been addressed, and the team is starting to find it disruptive?
- How would you balance encouraging people to speak up with keeping design reviews efficient and on schedule?