# Phase 2 Task Checklist

Tracking table for Phase 2 hybrid solution work.

Legend:
- Status: `Not Started`, `In Progress`, `Blocked`, `Done`
- Priority: `Hard`, `Normal`, `Simulation`

| Owner | Priority | Task | Status | Deadline |
|---|---|---|---|---|
| Member 1 (Interfaces) | Hard | Freeze hybrid message contract (`FireSensorAlert`, `VisionDetectionArray`, `FusionDecision`) | Not Started | 2026-05-10 |
| Member 1 (Interfaces) | Hard | Add strict interface versioning/migration rules in `interface_contract.yaml` | Not Started | 2026-05-12 |
| Member 1 (Interfaces) | Hard | Add schema/QoS validation tests for critical hybrid topics | Not Started | 2026-05-14 |
| Member 2 (Simulation) | Simulation | Add fire entities in `src/simulation/worlds/*.sdf` with repeatable ignition zones | Not Started | 2026-05-11 |
| Member 2 (Simulation) | Simulation | Add human entities/scenarios in `src/simulation/worlds/*.sdf` | Not Started | 2026-05-12 |
| Member 2 (Simulation) | Simulation | Enhance robot model `.sdf` sensor mounting and collision realism | Not Started | 2026-05-14 |
| Member 2 (Simulation) | Simulation | Add launch toggles for fire/human scenario packs | Not Started | 2026-05-15 |
| Member 2 (Simulation) | Simulation | Add tests for fire/human spawn validity + namespace safety | Not Started | 2026-05-16 |
| Member 3 (Mapping/Monitoring) | Normal | Add high-risk fire zone annotation support for fusion context | Not Started | 2026-05-13 |
| Member 3 (Mapping/Monitoring) | Normal | Extend monitoring topics to include sensor heartbeat + camera latency | Not Started | 2026-05-14 |
| Member 3 (Mapping/Monitoring) | Normal | Add hybrid timing alarm test and camera TF consistency check | Not Started | 2026-05-16 |
| Member 4 (Exploration/Utils) | Normal | Update exploration scoring with hazard-aware fusion input | Not Started | 2026-05-13 |
| Member 4 (Exploration/Utils) | Normal | Add confidence-weight helper utilities in `common_utils` | Not Started | 2026-05-14 |
| Member 4 (Exploration/Utils) | Normal | Add tests for auction/frontier behavior under fusion hazard flags | Not Started | 2026-05-16 |
| Member 5 (Response) | Hard | Implement response gating (sensor-only alert vs sensor+vision confirmed incident) | Not Started | 2026-05-12 |
| Member 5 (Response) | Hard | Add temporal/confidence filters for camera-only false positives | Not Started | 2026-05-14 |
| Member 5 (Response) | Hard | Add dedicated rescue/suppression planning tests for hybrid inputs | Not Started | 2026-05-16 |
| Member 5 (Response) | Hard | Implement deterministic multi-incident conflict resolution | Not Started | 2026-05-18 |
| Member 6 (Coordination/Bringup) | Hard | Integrate hybrid bringup flow in `full_system.launch.py` | Not Started | 2026-05-12 |
| Member 6 (Coordination/Bringup) | Hard | Add `hybrid_sim`, `hybrid_robot`, `hybrid_debug` launch profiles | Not Started | 2026-05-14 |
| Member 6 (Coordination/Bringup) | Hard | Implement failover modes (camera timeout, sensor timeout, safe-stop) | Not Started | 2026-05-16 |
| Member 6 (Coordination/Bringup) | Hard | Improve `cmd_vel` safety with fusion risk input + faster avoidance | Not Started | 2026-05-18 |
| Member 6 (Coordination/Bringup) | Hard | Add E2E latency/observability tests and metrics | Not Started | 2026-05-20 |

## Coordination Milestones

| Milestone | Owner(s) | Status | Deadline |
|---|---|---|---|
| Phase 2 interface freeze | Member 1 + Member 6 | Not Started | 2026-05-12 |
| Simulation scenario ready (fire + human) | Member 2 | Not Started | 2026-05-15 |
| Hybrid integration dry run | Members 2, 5, 6 | Not Started | 2026-05-18 |
| Full Phase 2 system validation | All members | Not Started | 2026-05-21 |
