# `src/runtime_env/`

Owner: dependency-free Python CLI implementation in [`cli.py`](cli.py).

It validates cross-file references, renders/checks profiles, manages host-local dotenv metadata safely, executes fixed workloads, creates explicit consumer projections, and verifies consumer staged state. It must not print secret values, accept generic trailing commands, or make consumer hooks depend on a sibling checkout.
