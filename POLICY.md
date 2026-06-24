# API Policy

## Purpose

The LightBurn and MillMage REST APIs exist to support interoperability, workflow automation, third-party integrations, and data exchange with supported versions of LightBurn and MillMage.

The APIs are intended to provide a documented and supported mechanism for applications to communicate with LightBurn and MillMage without requiring modification of the software.

This Policy describes the project's goals, expectations, and support boundaries. It is provided for informational purposes only and does not replace the API EULA or any other legal agreement.

---

## Public Specification

The API specification is publicly documented to encourage interoperability and third-party development.

The availability of documentation does not imply that the LightBurn or MillMage implementations are open source.

LightBurn and MillMage remain proprietary software. The API implementation, internal functionality, and associated software components remain the property of LightBurn Software, Inc.

Example code may be released under separate licenses as identified within the repository.

---

## Safety

LightBurn Software considers safe machine operation more important than convenience, automation, or feature availability.

The APIs are intended to assist workflows and integrations. They are not intended to replace operator judgment, supervision, or established safety procedures.

Users remain solely responsible for the safe operation of all equipment connected to or controlled through LightBurn or MillMage.

---

## Remote Operation

LightBurn Software does not endorse, recommend, support, or encourage the remote operation of lasers, CNC machines, or other machinery.

The existence of API functionality, network connectivity, companion applications, pendant-style interfaces, or third-party integrations should not be interpreted as approval for remote machine operation.

Any person choosing to operate machinery remotely assumes all associated risks and responsibilities.

---

## Unattended Operation

The APIs are not intended to facilitate unattended machine operation.

Users should not assume that network connectivity, monitoring systems, cameras, automation platforms, remote interfaces, or third-party software eliminate the need for direct operator supervision.

Machines should be operated in accordance with manufacturer recommendations, applicable regulations, and accepted safety practices.

---

## No Endorsement of Remote Machine Control

The availability of API functionality should not be interpreted as certification, approval, or validation of any workflow involving remote machine control.

LightBurn Software does not certify that any API-based solution is suitable for operating machinery without a qualified operator present and able to respond immediately to unsafe conditions.

Users who implement such solutions do so entirely at their own risk.

---

## Safety-Sensitive Functionality

Not all functionality available within LightBurn or MillMage will necessarily be exposed through the public APIs.

LightBurn Software may choose to restrict, withhold, redesign, or remove access to functionality that could present safety concerns, security concerns, reliability concerns, or excessive support burdens.

Examples may include machine control functions, camera systems, safety-related features, or other sensitive capabilities.

The existence of functionality within the software does not imply that a public API will be provided.

---

## API Stability and Versioning

The APIs evolve alongside LightBurn and MillMage.

Endpoints, authentication methods, request formats, response formats, and available functionality may change between software releases.

LightBurn Software will generally attempt to maintain compatibility where practical and may provide migration guidance or replacement functionality when appropriate. However, backward compatibility cannot be guaranteed.

Developers are encouraged to test integrations against the software versions they intend to support.

---

## Supported Interfaces

Only publicly documented API functionality should be considered supported.

Undocumented, internal, experimental, reverse-engineered, or otherwise non-public interfaces are unsupported and may change or be removed without notice.

LightBurn Software does not guarantee compatibility, support, or continued availability for integrations that depend on unsupported functionality.

---

## Security

Security vulnerabilities should be reported privately in accordance with SECURITY.md and DISCLOSURE.md.

Researchers and developers are encouraged to follow responsible disclosure practices and allow a reasonable opportunity for investigation and remediation before publicly disclosing security-related issues.

Good-faith security research is appreciated.

---

## Community Contributions

Feedback, bug reports, documentation improvements, examples, and integration ideas are welcome.

LightBurn Software may review and consider community contributions but is under no obligation to implement, support, maintain, or continue any proposed feature, behavior, endpoint, or enhancement.

---

## Support Expectations

LightBurn Software may provide support for documented API functionality at its discretion.

Third-party applications, custom integrations, automation systems, and derivative tools remain the responsibility of their respective developers.

Support should not be expected for undocumented functionality, reverse-engineered interfaces, modified implementations, or unsupported workflows.

---

## Future Development

The APIs will continue to evolve alongside LightBurn and MillMage.

Functionality may be added, modified, restricted, licensed separately, deprecated, or removed based on technical, safety, security, business, or support considerations.

The goal of the APIs is to encourage useful integrations while maintaining the safety, reliability, and usability standards expected by the LightBurn and MillMage communities.