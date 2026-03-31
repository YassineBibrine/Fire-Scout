# Fire-Scout Team Coordination (Optimized)

## Package Ownership Matrix

| Team | Owner | Packages |
|---|---|---|
| Team 1 | Interfaces Lead | `firescout_interfaces` |
| Team 2 | Simulation Lead | `simulation` |
| Team 3 | Mapping+Monitoring Lead | `mapping`, `monitoring` |
| Team 4 | Exploration+Utils Lead | `exploration`, `common_utils` |
| Team 5 | Response Lead | `response` |
| Team 6 | Coordination+Bringup Lead | `coordination`, `bringup`, `testing_tools` |

## Single-Owner Critical Artifacts

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
2. Communication only through topics/services/actions defined in `firescout_interfaces`.
3. Per-robot entities must be namespaced (`/robot1`, `/robot2`, `/robot3`).
4. Any global topic must use a global prefix (`/mapping`, `/mission`, `/coordination`, `/incidents`).
5. Interface changes require Team 1 approval and version update in `interface_contract.yaml`.

## Git Workflow

1. `main` stays releasable.
2. Team branches map to ownership matrix.
3. PR merge requires:
   - tests added/updated
   - launch smoke success
   - no namespace violations
   - interface impact declaration

## Weekly Integration Procedure

1. Monday: interface freeze for the week.
2. Midweek: integration dry-run with `testing_tools` dummy stack.
3. Friday: full 3-robot integration run and report.

## Definition of Done (All Teams)

- [ ] Node logic implemented
- [ ] Launch integrated
- [ ] Config added/updated
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Docs updated
