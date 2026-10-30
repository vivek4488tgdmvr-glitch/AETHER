# Suggested 2–3 minute demo script

Use only after you have run the project successfully and verified the real model integration.

**0:00–0:20 — Problem**
“Code review is slow when a developer must manually trace source files, explain a bug, propose a patch, and verify the change.”

**0:20–0:40 — What Aether Code does**
“Aether Code connects to an NVIDIA Nemotron model through Nebius Token Factory. It inspects a bounded repository context and produces evidence-backed findings and a reviewable unified diff.”

**0:40–1:20 — Live analysis**
Upload `examples/buggy-python-project` as a ZIP, ask Aether Code to review the correctness of the functions and tests, and show the findings with file evidence. Do not present generated findings as guaranteed truth.

**1:20–1:50 — Patch**
Generate a patch, inspect the diff, and download it. Explain that Aether Code does not silently overwrite the original upload.

**1:50–2:20 — Tests and safety**
If Docker is available, run the existing tests in the network-disabled sandbox and show the actual result. Explain that arbitrary dependency installation is intentionally disabled in this prototype.

**2:20–2:50 — Nebius integration**
Show the live model catalog, exact selected Nemotron model ID, and backend inference path. Do not show the API key.

**Closing**
“Aether Code makes the engineering process visible: inspect, explain, propose, test, and keep a human in control.”
