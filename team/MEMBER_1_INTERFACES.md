# Member 1: Interfaces Contract Lead

## Package Ownership
- `src/firescout_interfaces`

## Responsibility
Own and govern all ROS interfaces (`msg`, `srv`, `action`) as the single source of truth for inter-package communication.

## Files and Folders
- `src/firescout_interfaces/msg/`
- `src/firescout_interfaces/srv/`
- `src/firescout_interfaces/action/`
- `src/firescout_interfaces/config/interface_contract.yaml`
- `src/firescout_interfaces/test/`
- `src/firescout_interfaces/CMakeLists.txt`
- `src/firescout_interfaces/package.xml`

## Implementation Tasks
- [ ] Define and maintain all custom messages for mapping, exploration, response, and coordination
- [ ] Define and maintain all services for tasking, fault handling, and map control
- [ ] Define and maintain all actions for long-running operations
- [ ] Enforce naming, field semantics, and versioning policy in `interface_contract.yaml`
- [ ] Validate no redundant or overlapping interfaces

## Configuration and Validation Tasks
- [ ] Keep `config/interface_contract.yaml` aligned with current APIs
- [ ] Add generation checks for messages/services/actions
- [ ] Add serialization compatibility checks
- [ ] Add contract validation tests for required fields and naming consistency

## Testing Tasks
- [ ] Maintain tests in `test/test_msg_generation.py`
- [ ] Maintain tests in `test/test_srv_generation.py`
- [ ] Maintain tests in `test/test_action_generation.py`
- [ ] Review integration breakages caused by interface changes

## Done Criteria
- [ ] All interfaces generate successfully
- [ ] Contract file is updated and reviewed
- [ ] No downstream package blocked by interface ambiguity
- [ ] Interface tests pass in CI
