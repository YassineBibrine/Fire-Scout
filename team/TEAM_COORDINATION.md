# Fire-Scout Team Coordination

## Ownership Matrix

| Team | Owner | Packages |
|---|---|---|
| Team 1 | Interfaces Lead | firescout_interfaces |
| Team 2 | Simulation Lead | simulation |
| Team 3 | Mapping + Monitoring Lead | mapping, monitoring |
| Team 4 | Exploration + Utils Lead | exploration, common_utils |
| Team 5 | Response Lead | response |
| Team 6 | Coordination + Bringup Lead | coordination, bringup, testing_tools |

## Current Project Status

- The interface contract is defined in `src/firescout_interfaces/config/interface_contract.yaml` and all msg/srv/action trees are present.
- Simulation, mapping, monitoring, exploration, response, coordination, bringup, and testing_tools all have implemented launch/config/test surfaces in place.
- `src/bringup/launch/full_system.launch.py` is the top-level orchestration entrypoint for the full stack.
- `src/response/launch/hybrid_pipeline.launch.py` is the profile-aware per-robot hybrid response entrypoint used by full-system bringup.
- `testing_tools` provides the dummy publishers and fault injection helpers used for integration runs.

## Single-Owner Artifacts

| Artifact | Primary Owner |
|---|---|
| Message/service/action definitions | Team 1 |
| Simulation worlds/models | Team 2 |
| TF tree policy | Team 3 |
| Global merged map topic | Team 3 |
| System-wide launch (`full_system.launch.py`) | Team 6 |
| Namespace lint and integration dummy tools | Team 6 |

## Engineering Rules

1. No direct imports between runtime packages.
2. Communication only through topics, services, and actions defined in `firescout_interfaces`.
3. Per-robot entities must be namespaced (`/robot1`, `/robot2`, `/robot3`).
4. Any global topic must use a global prefix (`/mapping`, `/mission`, `/coordination`, `/incidents`).
5. Interface changes require Team 1 approval and a version update in `interface_contract.yaml`.

## Coverage Notes

- Most packages have focused unit or launch tests already present.
- Monitoring has exporter coverage, response has hybrid pipeline and bridge coverage, and bringup has profile wiring coverage.
- Remaining gap: response planning nodes still do not have dedicated runtime integration tests.
