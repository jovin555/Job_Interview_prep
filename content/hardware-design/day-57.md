# hardware-design — Day 57

## Q1: How would you approach selecting an op-amp topology for a photodiode-based sensor front-end that must measure low-level current with good linearity, and what trade-offs would drive the choice between a transimpedance amplifier and a simple voltage-follower configuration?

**Answer:** The starting point is recognizing that a photodiode is fundamentally a current source, so the front-end's job is to convert a small current into a usable voltage without letting the op-amp's own errors dominate. A transimpedance amplifier (TIA) is the natural fit: the photodiode feeds the summing node, the feedback resistor sets the transimpedance gain, and the op-amp holds the diode's cathode at a virtual ground so the diode operates in a low-capacitance, low-nonlinearity region. A voltage-follower across a load resistor is simpler, but it forces the diode to swing with the signal, which increases junction capacitance modulation and degrades linearity and bandwidth — usually unacceptable for precision photometry.

The real design work is in the TIA's stability and noise. The photodiode's junction capacitance plus the op-amp's input capacitance form a pole with the feedback resistor, and that pole can push the loop toward oscillation. A feedback capacitor across the transimpedance resistor introduces a zero that compensates the phase, and its value is chosen so the closed-loop response is critically damped rather than peaking. I'd estimate the total input capacitance from the diode datasheet plus layout parasitics, then size the feedback cap so the noise gain flattens before the op-amp's unity-gain crossover.

Op-amp selection then follows from the error budget: input bias current matters most because it flows directly into the summing node and appears as an offset current, so for very low currents a CMOS or JFET-input part with femtoamp-to-picoamp bias is preferable to a bipolar input. Input voltage noise and current noise both contribute, and which dominates depends on the source impedance — at high transimpedance, current noise multiplied by the feedback resistor can dominate, so a part with low current noise is worth the trade. Gain bandwidth must be high enough to keep the loop stable at the required closed-loop bandwidth, and I'd verify the phase margin with a simulation that includes the diode capacitance and a realistic feedback network.

**Possible follow-ups:**
- How would you separate the op-amp's own input current noise from the photodiode's shot noise when characterizing the front-end on the bench?
- If the required bandwidth increases, how does that change your feedback capacitor and op-amp selection?

## Q2: Walk me through how you would debug a circuit where a DC-DC converter's output voltage is correct under steady load but droops significantly during load transients, and the droop recovers slowly.

**Answer:** I'd start by separating the problem into three possible contributors: insufficient output capacitance, inadequate loop bandwidth, or a layout/parasitic issue. The recovery time is the key clue — a fast recovery points to the control loop, while a slow recovery points to bulk energy storage or a current-limit behavior.

First I'd capture the transient with a scope using a short ground lead and a current probe or sense resistor, looking at both the output voltage and the inductor current. If the inductor current slews quickly but the output still droops, the loop is responding but the output capacitor can't supply the initial charge — that's a capacitance or ESR problem. If the inductor current ramps slowly, the loop bandwidth or the current-limit threshold is the constraint.

For the capacitance angle, I'd calculate the charge the load step demands during the loop's response time and compare it to what the output cap can deliver within the allowed voltage deviation. ESR also matters: a high-ESR capacitor produces an immediate IR step before the loop reacts, so I'd check whether the initial droop is a step (ESR) or a ramp (capacitance). Adding a small ceramic in parallel with bulk electrolytic often fixes the ESR step without changing the loop.

For the loop angle, I'd look at the compensation network and the crossover frequency. If the crossover is too low, the loop takes many switching cycles to correct the error, producing a long recovery. I'd check the phase margin too — a marginally stable loop can ring or recover sluggishly. Before changing compensation, I'd confirm the feedback divider and the reference aren't introducing extra poles, and that the layout keeps the feedback trace short and away from the switch node.

**Possible follow-ups:**
- How would you distinguish a genuine loop instability from a load-step response that's simply underdamped?
- What bench measurements would you take to confirm the output capacitor's effective capacitance and ESR in-circuit?

## Q3: How would you approach designing the analog front-end for a sensor whose output impedance is high and varies with the measurand, and what would you watch for?

**Answer:** A high and variable source impedance is the central challenge because it interacts with everything downstream: the amplifier's input bias current, the input capacitance, and the ADC's sampling network. The first decision is buffering — a high-impedance sensor usually needs a unity-gain buffer or a non-inverting amplifier stage placed as close to the sensor as possible so the sensitive node stays short and shielded.

Op-amp selection is driven by input bias current and input capacitance. Bias current flowing through a high source impedance produces an offset that changes as the impedance changes with the measurand, which is a systematic error that can't be calibrated out with a single constant. A CMOS or JFET-input op-amp with low bias current minimizes this. Input capacitance, combined with the source impedance, forms a pole that can limit bandwidth and, in a feedback configuration, erode phase margin — so I'd add a small capacitor across the feedback resistor to introduce a compensating zero and keep the loop stable.

The variable impedance also affects settling. If the sensor is multiplexed into an ADC, the RC time constant changes with the measurand, so the acquisition time must be sized for the worst-case (highest) impedance, or a buffer must isolate the ADC's sampling capacitor from the sensor. I'd also watch for cable capacitance if the sensor is remote — it adds to the input capacitance and can cause peaking or oscillation, so a series resistor at the amplifier input or a guard/shield driven at the same potential can help.

Finally, noise: a high source impedance means the sensor's own thermal noise (Johnson noise) may dominate, and the amplifier's current noise multiplied by the source impedance can exceed its voltage noise. I'd build a noise budget that includes both, and choose the op-amp based on which term dominates at the actual source impedance.

**Possible follow-ups:**
- How would you verify on the bench that the front-end's settling time is adequate across the full range of source impedances?
- If the sensor is remote and connected by a cable, how would you handle the cable's capacitance and any ground potential differences?

## Q4: How would you approach selecting a shunt resistor and current-sense amplifier topology for measuring a bidirectional motor current of up to 1A, where the measurement must be accurate to ±2% over temperature and the shunt must not dissipate excessive power?

**Answer:** The shunt value is a trade-off between signal amplitude and power dissipation. A larger shunt gives a bigger differential voltage, which improves signal-to-noise and reduces the relative impact of the amplifier's offset, but it dissipates more power and drops more voltage in the motor path. At 1A, a 10 mΩ shunt dissipates 10 mW and produces 10 mV — a reasonable starting point. If the motor supply is low, even that drop may be unacceptable, so I'd check the allowable insertion loss first.

For a bidirectional measurement, the amplifier must handle both polarities of differential input, so I'd use a dedicated current-sense amplifier rather than a generic difference amplifier, because these parts are designed with matched internal resistors and specified common-mode range that includes the motor supply rail. The topology choice — high-side versus low-side — depends on whether the load's ground reference must be preserved. High-side sensing keeps the motor ground clean but requires the amplifier to tolerate the full supply as common mode; low-side sensing is simpler but breaks the ground path, which can be a problem if other circuits share that node.

Accuracy over temperature comes from three sources: the shunt's own temperature coefficient, the amplifier's offset voltage and its drift, and the gain error of the amplifier's internal resistor network. I'd pick a shunt with a low TCR (metal-element or a good alloy rather than a cheap thick-film) and an amplifier with low offset drift and a specified gain error over temperature. The ±2% budget should be allocated across these terms, and I'd verify that the worst-case sum stays within budget rather than assuming typical values.

Layout matters too: the shunt's Kelvin sense connections must be taken from inside the pad area so trace resistance doesn't add to the measured drop, and the differential pair to the amplifier should be routed tightly together and away from the switching node.

**Possible follow-ups:**
- How would you calibrate out the amplifier's offset in production, and would you do it at one temperature or multiple?
- If the motor current has significant ripple from PWM, how would you filter the sense signal without adding unacceptable phase lag to the control loop?

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review the mechanical engineer proposes moving a temperature sensor from the PCB to a location closer to the patient-contact surface, arguing it will give a more accurate reading of the actual patient temperature. You're concerned that the new location is electrically noisy and mechanically difficult to route, and that the sensor's own self-heating and the thermal mass of the new location may actually degrade accuracy. How would you handle this disagreement?

**Answer:** I'd treat this as a measurement-accuracy question rather than a turf question, and try to reframe the discussion around what "accurate" means for the clinical requirement. The mechanical engineer's instinct — that measuring closer to the patient gives a truer reading — is reasonable, but it assumes the sensor's own error sources don't change with location, which is exactly what's in question.

My approach would be to propose a structured evaluation rather than argue from opinion. First, I'd ask what the actual accuracy requirement is and over what range, because that determines how much margin we have. Then I'd lay out the specific concerns: the new location's proximity to switching regulators or motor drive traces could couple noise into a high-impedance sensor node; the thermal mass of the new location could slow the sensor's response to real temperature changes; and the sensor's self-heating, which is normally dissipated by the PCB copper, might not have the same thermal path in the new location, so the sensor could read its own temperature rather than the patient's.

I'd propose a bench experiment: mount the sensor in both locations, apply a known thermal stimulus, and compare the readings against a calibrated reference. That converts the disagreement into data. If the new location genuinely performs better, I'd support it and work on the routing and shielding to address the noise concern. If it performs worse, the data settles the question without anyone losing face.

Throughout, I'd keep the conversation focused on the patient-safety and regulatory implications — the design history file needs a defensible rationale for the sensor location, and "it seemed closer" isn't sufficient. I'd also loop in the quality/regulatory function early so the decision is documented properly.

**Possible follow-ups:**
- If the bench experiment is inconclusive, how would you decide?
- How would you handle it if the mechanical engineer's proposal would also require a change to the enclosure that affects other subsystems?