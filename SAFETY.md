# Safety Guidance

## Introduction

The LightBurn and MillMage APIs are intended to support integrations, workflow automation, and interoperability with supported versions of LightBurn and MillMage.

Improper use of software, automation, remote access systems, or machine integrations may create risks including equipment damage, material loss, fire, personal injury, or property damage.

This document provides general guidance for safe API usage. It does not replace machine manufacturer recommendations, local regulations, workplace safety requirements, or professional judgment.

---

## Operator Responsibility

Users remain responsible for the safe operation of all equipment connected to or used with LightBurn or MillMage.

Before operating any machine, users should ensure that:

- The machine is in good working condition.
- Safety systems are functioning correctly.
- Emergency stop devices are accessible.
- The work area is free from unnecessary hazards.
- Appropriate fire prevention measures are in place.
- Machine manufacturer recommendations are being followed.

---

## Supervision

Machine operation should be supervised by a responsible operator who can immediately respond to unexpected behavior, machine faults, fire risks, material issues, or other unsafe conditions.

The availability of API functionality, automation tools, cameras, monitoring systems, or remote interfaces should not be considered a substitute for operator supervision.

---

## Remote Operation

LightBurn Software does not recommend using the APIs to remotely operate lasers, CNC machines, or other machinery.

Remote access systems can introduce additional risks, including:

- Network failures.
- Communication delays.
- Loss of video feeds.
- Software faults.
- Unauthorized access.
- Inability to respond quickly to unsafe conditions.

Users who choose to implement remote workflows should carefully evaluate the associated risks.

---

## Unattended Operation

Do not rely on the APIs to facilitate unattended machine operation.

The existence of automation, monitoring, notifications, cameras, sensors, dashboards, or remote controls does not eliminate the need for direct supervision.

Machines capable of generating heat, sparks, smoke, motion, or cutting operations should be monitored appropriately while operating.

---

## Cameras and Monitoring Systems

Cameras and monitoring systems can be useful tools but should not be considered safety systems.

Video feeds may be delayed, interrupted, obscured, misconfigured, or unavailable when needed.

Operators should not assume that camera visibility alone is sufficient to safely monitor machine operation.

---

## Automation and Integrations

Before using an integration in a production environment:

- Verify that the integration behaves as expected.
- Test with non-critical projects where practical.
- Validate inputs and outputs.
- Confirm version compatibility.
- Review any automation logic carefully.

Changes to software versions, API versions, operating systems, network environments, or third-party applications may affect integration behavior.

---

## Security Considerations

The APIs are primarily intended for use on trusted local networks.

If API access is exposed outside a local network, users should carefully evaluate:

- Authentication controls.
- Network security.
- Access permissions.
- Remote access methods.
- Potential attack surfaces.

Users are responsible for protecting their own systems and credentials.

---

## Unsupported Functionality

Only publicly documented API functionality should be considered supported.

Undocumented, internal, experimental, or reverse-engineered functionality may behave unexpectedly and may change without notice.

Reliance on unsupported functionality may increase operational and safety risks.

---

## Emergency Preparedness

Operators should always be prepared to:

- Stop machine operation immediately if necessary.
- Disconnect power when appropriate.
- Follow manufacturer emergency procedures.
- Respond to fire, smoke, equipment faults, or other hazardous situations.

Emergency response procedures should be established before running production workflows.

---

## Final Reminder

The APIs are designed to support useful integrations and workflows.

They are not safety systems, supervision systems, or replacements for responsible machine operation.

Users remain responsible for evaluating risks, supervising equipment, and ensuring that their workflows are appropriate for their environment and use case.