# Member 1: Interfaces Contract Lead - Documentation

## Responsabilités
- Gouverner toutes les interfaces ROS2 (msg, srv, action) comme source unique de vérité
- Maintenir le contrat d'interface et la politique de versioning
- Assurer la compatibilité entre les packages

## Package: firescout_interfaces

### Messages (16)
| Message | Description | Utilisé par |
|---------|-------------|-------------|
| RobotHealth | État de santé du robot | Monitoring, Coordination |
| Frontier | Frontière d'exploration | Exploration |
| FrontierArray | Tableau de frontières | Exploration |
| FireDetection | Détection d'incendie | Response |
| HumanDetection | Détection de personne | Response |
| TaskAssignment | Assignation de tâche | Coordination, Exploration |
| Incident | Événement incident | Response, Coordination |
| FaultEvent | Événement de panne | Coordination |
| MissionState | État de la mission | Coordination |
| MapMergeStatus | Statut de fusion de cartes | Mapping |
| NodeStatus | Statut des noeuds | Monitoring |
| AuctionAnnouncement | Annonce d'enchère | Exploration |
| AuctionBid | Offre d'enchère | Exploration |
| AuctionResult | Résultat d'enchère | Exploration |
| ReferenceTrajectory | Trajectoire de référence | Navigation |
| SensorData | Données capteur génériques | Response |

### Services (10)
| Service | Description |
|---------|-------------|
| AssignTask | Assigner une tâche à un robot |
| StartMapping | Démarrer la cartographie |
| StopMapping | Arrêter la cartographie |
| SetRobotMode | Changer le mode du robot |
| AckTask | Accuser réception d'une tâche |
| GetRobotState | Obtenir l'état du robot |
| ReportFault | Signaler une panne |
| RequestAssistance | Demander de l'assistance |
| ResolveIncident | Résoudre un incident |
| SetMapMergeEnabled | Activer/désactiver fusion de cartes |

### Actions (2)
| Action | Description | Durée typique |
|--------|-------------|---------------|
| SuppressFire | Suppression d'incendie | 30-120 secondes |
| RescueHuman | Sauvetage de personne | 60-180 secondes |

## Contrat d'Interface
Le fichier `config/interface_contract.yaml` définit:
- Conventions de nommage
- Politique de versioning sémantique
- Règles de validation

## Tests
- ✅ test_msg_generation.py - Vérifie tous les messages
- ✅ test_srv_generation.py - Vérifie tous les services  
- ✅ test_action_generation.py - Vérifie toutes les actions

## État
- [x] Toutes les interfaces définies
- [x] Tests passent (10/10)
- [x] Documentation complétée
- [x] Contract à jour

## Dépendances
- std_msgs
- geometry_msgs
- builtin_interfaces
- action_msgs

## Validation
```bash
# Vérifier les messages
ros2 interface list | grep firescout_interfaces/msg

# Vérifier les services  
ros2 interface list | grep firescout_interfaces/srv

# Vérifier les actions
ros2 interface list | grep firescout_interfaces/action

### Mettre à jour le README principal

```bash
# Ajouter votre section dans le README
cat >> README.md << 'EOF'

## 🔌 Interfaces Package (Member 1 - Ali)

Le package `firescout_interfaces` contient toutes les interfaces ROS2 du projet:

- **16 Messages** : Communication de données entre nodes
- **10 Services** : Requêtes/réponses synchrones  
- **2 Actions** : Tâches longues avec feedback

### Vérification rapide
```bash
# Compiler les interfaces
colcon build --packages-select firescout_interfaces

# Lister toutes les interfaces
ros2 interface list | grep firescout_interfaces

## Phase 2 - Hybrid System Tasks 

Hybrid target: Jetson + fire sensors + ROS 2 fusion.

- Define and freeze new hybrid interface contract for sensor-driven fire alerts and vision detections:
	- `FireSensorAlert.msg` (flame/smoke/gas/temp raw + normalized + timestamp + source id)
	- `VisionDetectionArray.msg` (class, confidence, bbox, camera id, frame id)
	- `FusionDecision.msg` (`fire_confirmed`, `human_confirmed`, `risk_level`, `recommended_action`)
- Add strict versioning rules in `src/firescout_interfaces/config/interface_contract.yaml` for backward compatibility across microcontroller gateway, Jetson AI node, and fusion node.
- Add schema validation tests for all hybrid messages/services and reject invalid payload ranges (NaN, out-of-range confidence, invalid namespace).
- Define QoS profiles and reliability rules for critical topics (`/fire_sensor_alert`, `/camera_detections`, `/fusion_decision`, `/emergency_stop`) and document required publish rates.
- Provide migration notes from Phase 1 interfaces to Phase 2 hybrid interfaces so all teams can upgrade without breaking runtime nodes.


