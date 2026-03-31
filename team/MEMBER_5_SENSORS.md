# Member 5: Response and Incident Handling Lead

## Package Ownership
- `src/response`

## Responsibility
Own fire/human detection and incident prioritization pipelines, including rescue/suppression planning interfaces.

## Files and Folders
- `src/response/response/`
- `src/response/launch/`
- `src/response/config/`
- `src/response/test/`
- `src/response/package.xml`
- `src/response/setup.py`

## Implementation Tasks
- [ ] Implement fire detection runtime node
- [ ] Implement human detection runtime node
- [ ] Implement suppression planning node
- [ ] Implement rescue planning node
- [ ] Maintain global incident fusion/prioritization behavior

## Configuration Tasks
- [ ] Maintain `config/fire_detection.yaml`
- [ ] Maintain `config/human_detection.yaml`
- [ ] Maintain `config/prioritization.yaml`

## Testing Tasks
- [ ] Maintain `test/test_fire_detection_pipeline.py`
- [ ] Maintain `test/test_human_detection_pipeline.py`
- [ ] Maintain `test/test_incident_priority.py`

## Done Criteria
- [ ] Detection topics publish valid outputs per robot namespace
- [ ] Prioritization behavior is deterministic and documented
- [ ] No direct dependency on non-interface runtime packages
- [ ] Response tests pass in CI
