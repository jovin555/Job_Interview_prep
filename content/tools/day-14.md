# tools — Day 14

## Q1: How would you approach setting up a multi-board firmware debugging environment where you need to debug firmware running on two different microcontrollers simultaneously, with a shared debugger connection?

**Answer:** For multi-core or multi-board debugging, I'd first clarify whether the two microcontrollers are on the same board or separate boards, and whether they share a single debug probe or have independent probes. If they share one probe (e.g., a multi-core MCU or a single J-Link with multiple target connections), I'd configure the debugger to support multi-target sessions — tools like Segger J-Link support connecting to multiple targets through a single probe using their multi-core debugging features, or through a JTAG chain if the devices support it.

If the MCUs are on separate boards with independent debuggers, I'd set up a coordinated debugging session using the IDE's multi-session support — for example, launching two debug sessions in parallel and using the debugger's synchronization features to pause/resume both targets together when needed. This is particularly important when debugging inter-processor communication, because halting one MCU while the other keeps running can cause timeouts or protocol errors that mask the real issue.

For the actual debugging workflow, I'd establish a consistent approach: start by verifying both debug connections independently, then set up synchronized breakpoints at the communication interface level (e.g., break on the SPI transaction start on both sides), and use trace or logging to correlate events across the two processors. If the debugger supports it, I'd also capture timestamped trace data from both targets to reconstruct the exact sequence of events leading up to a failure.

**Possible follow-ups:** How would you handle the case where halting one MCU causes the other to crash due to watchdog timeouts? What if the two MCUs use different debug interfaces (e.g., SWD on one and JTAG on the other)?

---

## Q2: How would you approach using a thermal imaging camera to validate the thermal design of a sealed enclosure containing multiple power-dissipating components, and how would you correlate those measurements with simulation results?

**Answer:** Thermal imaging is valuable for identifying hot spots and verifying that the thermal design behaves as expected, but it has limitations — particularly with sealed enclosures where you can't directly see the components. I'd approach this in phases.

First, I'd establish measurement points: place thermocouples on critical components (the hottest expected points, the most temperature-sensitive parts, and the enclosure surface) to get accurate absolute temperature readings. Thermal cameras measure surface temperature and can be affected by emissivity variations, so thermocouples provide ground truth for calibration. I'd also apply high-emissivity tape or paint to shiny metal surfaces that would otherwise reflect rather than emit.

For the thermal camera itself, I'd use it to get a spatial map of the enclosure surface temperature and, if there are any openings or if the enclosure is opened briefly, to image the PCB directly. The key is to compare the thermal gradient pattern — not just absolute values — against the simulation. If the simulation predicted a hot spot near a specific component but the camera shows it elsewhere, that indicates a thermal path issue (e.g., a thermal via array not working as intended, or a ground plane split disrupting heat spreading).

I'd also check the enclosure surface temperature against touch-temperature limits for medical devices, which is a regulatory concern. If the camera shows a localized hot spot on the enclosure surface, that might indicate a component is conducting heat through a mounting screw or standoff that wasn't modeled in simulation.

Finally, I'd run the device at multiple load conditions (e.g., standby, normal operation, maximum load) and compare the thermal response time — how quickly temperatures rise — against simulation. This validates the thermal mass and heat capacity assumptions in the model.

**Possible follow-ups:** How would you account for the emissivity of different component packages when interpreting thermal camera images? What would you do if the simulation and measurement disagree by more than 10°C at a critical component?

---

## Q3: How would you approach setting up a Git-based workflow for a firmware project that needs to support multiple hardware variants with different sensor configurations, while maintaining a single codebase?

**Answer:** The key is to separate hardware-specific configuration from the application logic. I'd structure the repository so that the core application code is hardware-agnostic, and hardware differences are handled through device tree overlays (if using Zephyr) or board-specific configuration files (if using a more traditional C project).

In Zephyr, the standard approach is to use the board directory structure: each hardware variant gets its own board definition directory containing the devicetree source file, Kconfig defaults, and board-specific pinmux configurations. The application code then uses devicetree aliases and API calls rather than hardcoded pin assignments. This way, building for a different hardware variant is just a matter of specifying a different board target in the west build command.

For version control, I'd keep the board definitions in the same repository as the application code, but organized so that shared code and board-specific code are clearly separated. I'd use Git branches for major hardware generations (e.g., a branch for the current production hardware and a development branch for the next revision), but within a single hardware generation, I'd avoid long-lived feature branches and instead use short-lived branches with frequent merges to main.

I'd also establish a tagging convention for releases — for example, tagging firmware builds with both the firmware version and the hardware revision they support, so that field issues can be traced back to the exact code and hardware combination. This is critical for medical devices where traceability is a regulatory requirement.

For the build system, I'd use CMake or the Zephyr build system to generate build artifacts with a naming convention that includes the target board, so there's no ambiguity about which binary goes on which hardware.

**Possible follow-ups:** How would you handle the case where a hardware bug fix requires changes to both the board definition and the application code? How would you manage the transition when a new hardware revision is introduced but the old revision is still in production?

---

## Q4: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** USB enumeration failures that are host-dependent and intermittent often point to timing margin issues — the device is right at the edge of the USB specification's timing requirements, and some hosts are more tolerant than others. I'd approach this systematically.

First, I'd capture the full enumeration sequence on both a host that works and one that fails, using a logic analyzer with USB protocol decoding. The key is to capture the entire sequence from connect detection through the final configuration request, not just the failing transaction. I'd look for differences in timing between the two captures — things like the delay between the host sending a SETUP packet and the device responding with an ACK, or the timing of the device's response to a GET_DESCRIPTOR request.

USB 2.0 has specific timing requirements for device response times — for example, the device must respond to a SETUP packet within a certain window, and the inter-packet gap has defined limits. I'd measure these parameters against the specification to identify which ones are marginal.

I'd also look at the electrical characteristics — the logic analyzer can show signal integrity issues like ringing or slow rise times on D+ and D- that might be marginal on some hosts due to differences in their receiver thresholds or termination. If the logic analyzer has analog capability, I'd use that to examine the waveform shape, not just the digital transitions.

If the timing measurements show margin issues, I'd investigate the firmware's USB stack configuration — for example, checking whether the device is using the correct endpoint sizes, whether the descriptor values match the actual hardware capabilities, and whether the firmware is adding unnecessary delays in its response path. I'd also check the clock source — a crystal with too much tolerance or a PLL that's not settling fast enough can cause timing jitter that manifests as intermittent failures.

Finally, I'd set up a stress test that repeatedly enumerates the device across multiple hosts to characterize the failure rate and determine whether the issue is truly random or correlated with specific conditions (e.g., temperature, cable length, or hub topology).

**Possible follow-ups:** How would you distinguish between a firmware timing issue and a hardware signal integrity issue from the logic analyzer captures? What specific USB timing parameters would you measure first?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the lab test equipment for an upcoming EMC pre-compliance test. On the day before the test, you discover that the engineer has configured the spectrum analyzer with the wrong resolution bandwidth and detector mode for the test standard you're targeting, and the engineer is confident the settings are correct based on a tutorial they watched online. The test is scheduled for tomorrow morning, and the lab time is expensive and non-refundable. How would you handle this situation?

**Answer:** The immediate priority is to correct the test setup before tomorrow, but I'd also want to address the underlying issue of the engineer's confidence in incorrect information. I'd start by having a direct conversation with the engineer, not to assign blame, but to walk through the test standard's requirements together. I'd ask them to show me the specific section of the standard that specifies the resolution bandwidth and detector settings, and I'd have the standard open on my screen as well.

If the standard clearly specifies different settings than what the engineer configured, I'd point to the specific clause and explain why the settings matter — for example, that using too wide a resolution bandwidth can miss narrowband emissions, or that using peak detector instead of quasi-peak can overestimate emissions and cause unnecessary design changes. I'd frame it as a learning opportunity: "This is exactly the kind of detail that separates a good test from a wasted lab session."

I'd then work with the engineer to correct the setup together, using this as a teaching moment. I'd have them reconfigure the instrument while I verify each setting against the standard, so they build the skill of cross-checking their work against the actual requirement rather than relying on tutorials.

After the test, I'd schedule a brief debrief to discuss what happened and establish a checklist for future test setups — a pre-test verification checklist that includes confirming the test standard, the applicable frequency range, resolution bandwidth, and detector mode before booking lab time. I'd also suggest that the engineer create a reference card for the test standards we commonly use, so they have a reliable resource to consult.

The key is to correct the immediate problem without damaging the engineer's confidence, while also putting systems in place to prevent the same mistake from happening again. I'd also make sure the engineer understands that asking for help or verification is always acceptable — especially for expensive, time-sensitive activities like EMC testing.

**Possible follow-ups:** How would you handle the situation if the engineer had already run some preliminary scans with the wrong settings and recorded results that you now need to disregard? How would you approach the conversation if the engineer becomes defensive and insists their settings are correct?