# behavioral-leadership — Day 4

## Q1: How would you approach convincing a regulatory affairs team to accept a hardware design change late in a medical device development cycle, when the change improves safety but introduces schedule risk?

**Answer:** I'd start by acknowledging their position — regulatory teams are rightly concerned about any late-stage change because it can trigger re-submission, re-testing, or documentation gaps that delay market access. Rather than framing the change as a request they need to approve, I'd present it as a shared problem to solve together.

First, I'd prepare a concise technical brief that clearly states: what the change is, why it improves safety (referencing specific IEC 60601 clauses or risk analysis findings), and what the minimum viable implementation looks like. I'd also include a preliminary impact assessment on the design history file — which documents need updating, whether any already-completed testing is invalidated, and whether the change affects the submitted 510(k) or equivalent regulatory filing.

Then I'd propose a structured evaluation: a small working session with regulatory, quality, and engineering to walk through the change's regulatory classification. Many late-stage changes fall into "does not significantly affect safety or performance" if scoped carefully, which may allow a streamlined change process rather than full re-submission. I'd come prepared with options — a full implementation versus a phased approach where the hardware change is made but the regulatory filing is updated in the next periodic submission.

The key is demonstrating that I've already done the homework to minimize their workload and risk, and that I'm asking for their expertise to find the path forward, not just their sign-off.

**Possible follow-ups:** How would you handle it if the regulatory lead still says no after your presentation? What if the safety improvement was discovered through a field complaint rather than internal testing?

---

## Q2: How would you approach leading a team through a post-mortem after a medical device project missed its delivery deadline by several months?

**Answer:** I'd structure the post-mortem to focus on systemic causes rather than individual blame, using a framework like the 5 Whys or a fishbone diagram to dig into root causes. The goal is to understand what in our processes, assumptions, or communication patterns allowed the delay to happen, so we can improve for next time.

I'd start by setting the tone explicitly: this is a learning exercise, not a performance review. Everyone in the room contributed their best effort given the information they had at the time. Then I'd walk through the project timeline chronologically, but instead of asking "what went wrong," I'd ask "where did our assumptions differ from reality?" and "at what point could we have known we were off track?"

Common areas to examine include: were requirements stable or did they change mid-project? Were technical unknowns identified early or discovered late? Did we have adequate prototyping and testing phases to catch integration issues? Were schedule estimates based on historical data or optimistic guesses?

I'd also look at decision points — were there moments where the team knew there was a problem but didn't escalate? If so, why? Was the culture not psychologically safe enough to raise concerns? Were there resource constraints that forced shortcuts?

The output should be a short list of actionable process improvements, not a novel. Maybe three to five specific changes — like adding a mid-project integration checkpoint, or requiring a formal risk review when schedule slips exceed 10%. I'd assign owners and follow up at the next project kickoff to ensure the lessons aren't forgotten.

**Possible follow-ups:** How would you handle a team member who becomes defensive during the post-mortem and insists the delay was caused by factors outside their control? What if the root cause analysis points to a decision you personally made?

---

## Q3: How would you approach integrating a new junior engineer into an ongoing medical device project where the documentation is incomplete and tribal knowledge is held by a few senior team members?

**Answer:** I'd treat this as both a ramp-up problem and a documentation improvement opportunity. The junior engineer needs to become productive, but the incomplete documentation is a risk for the whole team — so the onboarding process should simultaneously surface and capture that missing knowledge.

First, I'd create a structured onboarding plan with clear milestones for the first 30-60-90 days. The first week would focus on context: architecture overview, key design decisions and their rationale, regulatory requirements specific to this device, and the design history file structure — even if some sections are sparse, knowing what should exist helps them identify gaps.

Rather than handing them a stack of schematics and datasheets, I'd pair them with a senior engineer for specific tasks. For example, "Walk through the power supply section with Sarah. She'll explain why we chose that topology and what the trade-offs were." The junior engineer takes notes and creates a living document that captures the rationale that's missing from the formal documentation. This serves dual purposes: they learn the system deeply, and we fill documentation gaps.

I'd also give them a small, well-scoped task early — something like verifying a BOM against the schematic, or updating a test procedure — that gives them a concrete deliverable and a reason to ask questions. The key is making it safe to ask "dumb" questions; I'd explicitly say that any question they have is likely one someone else will have later, so documenting the answer helps everyone.

Weekly check-ins would focus on what they've learned and what's still confusing, rather than just task progress. I'd also introduce them to the other senior team members one-on-one for informal knowledge transfer sessions, rather than expecting them to absorb everything in a single design review.

**Possible follow-ups:** How would you handle it if the senior engineers are too busy to dedicate time for pairing? What if the junior engineer is reluctant to ask questions because they don't want to appear unprepared?

---

## Q4: How would you approach resolving a situation where two engineering teams — hardware and firmware — disagree on whether a system-level bug is caused by a timing issue in the I2C communication or by noise on the physical bus lines?

**Answer:** I'd start by framing this as a shared problem that needs data, not opinions. Both teams have valid perspectives, and the goal is to isolate the root cause systematically rather than argue about which domain is at fault.

First, I'd convene a short meeting to agree on the observable symptoms and the conditions that trigger the bug. What exactly happens? Is it reproducible? Under what specific conditions (temperature, power state, bus load, firmware version, hardware revision)? Getting everyone aligned on the facts prevents the conversation from drifting into hypotheticals.

Then I'd propose a structured debug plan with parallel workstreams. The hardware team can scope the I2C lines with an oscilloscope or logic analyzer to check for noise, glitches, or signal integrity issues — looking at rise times, undershoot, and whether the noise correlates with the failure. The firmware team can add debug logging or toggle a GPIO to timestamp when each I2C transaction starts and completes, to see if there's a timing violation or if the firmware is attempting to communicate while the bus is busy.

The key is to design experiments that can rule out one hypothesis or the other. For example, if the hardware team can show clean waveforms during the failure, that points toward firmware timing. If the firmware team can show that transactions complete within spec but the data is corrupted, that points toward noise. If both look clean, the issue might be at a higher level — perhaps a buffer overflow or a race condition in the firmware state machine.

I'd also suggest a controlled test: run the system with a known-good hardware setup (e.g., a development board with short, shielded I2C lines) to see if the bug persists. If it disappears, that strongly suggests a hardware layout or noise issue. If it remains, the firmware team needs to dig deeper.

Throughout, I'd keep the tone collaborative — "let's prove or disprove each theory together" rather than "prove me right." And I'd document the findings as we go, so the resolution becomes part of the design history file for future reference.

**Possible follow-ups:** What if the bug is intermittent and neither team can reproduce it reliably? How would you decide when to stop debugging and implement a workaround instead?

---

## Q5: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** I'd approach this as a process and culture change that needs to happen gradually, not through a single mandate. The goal is to shift from "risk management as paperwork" to "risk management as a design tool that makes our products safer and reduces late-stage surprises."

First, I'd identify a champion — ideally someone from quality or regulatory who already understands the value — and partner with them to pilot a different approach on one upcoming project or feature. Trying to change the entire team's workflow at once is overwhelming and likely to meet resistance.

For that pilot, I'd integrate risk management activities directly into existing design reviews rather than treating them as separate meetings. For example, during a schematic review, we'd explicitly ask: "What happens if this resistor fails short? What happens if this capacitor drifts in value over temperature? What's the worst-case voltage at this node?" These questions are already good engineering practice — we're just formalizing the documentation of the answers.

I'd also introduce the concept of "risk discovery" early in the design phase. Before committing to a topology or component selection, we'd do a quick informal FMEA at the block-diagram level. This doesn't need to be formal documentation yet — it's a whiteboard exercise to identify hazards early, when changes are cheap. The output feeds into the formal risk management file later.

To make the value tangible, I'd track metrics that matter to engineers: how many design iterations were avoided because a risk was identified early? How many late-stage test failures were prevented? How much rework time was saved? Engineers respond to efficiency arguments — if I can show that spending two hours on risk analysis upfront saves two weeks of debugging later, that's a compelling story.

Finally, I'd make it easy to do the right thing. If the current risk management template is cumbersome, I'd work with quality to simplify it or create a quick-start guide. If engineers don't know how to write a good hazard analysis, I'd run a lunch-and-learn session with examples from our own products. The goal is to remove friction, not add more.

**Possible follow-ups:** How would you handle a senior engineer who insists that risk management is "quality's job" and refuses to participate? What if the pilot project shows that risk analysis actually does slow down the early design phase — how would you justify the investment?