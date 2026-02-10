
---
title: GDPR compliance
description: Research and actionable guidance for association apps
---

# GDPR compliance — guidance for association management apps

Executive summary
- Short, actionable guidance for building privacy-first association software. Covers architecture, data minimization, user rights, retention, and developer checklist based on CNIL guidance.

Scope
- Applies to web and mobile applications that store or process member personal data, payment metadata, and any data revealing sensitive attributes.

Sources
- CNIL Developer's Guide: https://lincnil.github.io/Guide-RGPD-du-developpeur/
- CNIL Guide for Associations: https://www.cnil.fr/sites/cnil/files/atoms/files/cnil-guide_association.pdf

## Principles (Privacy by Design)
- Minimize data collection: collect only what's necessary for the purpose.
- Secure by default: safe defaults for profiles, opt-ins unchecked, least privilege access.
- Transparency and portability: provide clear notices and data export tools.

## 1. Architecture & technology choices

- Use proven, actively maintained frameworks and libraries. Track versions and apply security patches promptly.
- Prefer EU-hosted infrastructure or ensure lawful data transfers (SCCs or adequacy decisions) when using non-EU providers.
- Audit dependencies regularly (Dependabot, `npm audit`, Snyk).

Security controls
- Transport: enforce TLS for all traffic and HSTS for web apps.
- At rest: encrypt sensitive fields (financial identifiers) where feasible.
- Authentication: never store plaintext passwords; use Argon2 or bcrypt with appropriate parameters.
- Authorization: implement RBAC/ACL so roles (member, volunteer, admin) have minimal privileges.

## 2. Data minimization and collection

Collect only data required for membership or legal obligations. Example guidance:

| Data | When to collect | Recommendation |
| ---: | --- | --- |
| Identity (name, email) | Required for membership & communication | Keep; restrict access |
| Date of birth | Only if age affects eligibility or pricing | Collect only when needed |
| Family situation | Rarely required | Do not collect by default |
| Financial data (card numbers) | Never store card PANs | Use PCI-compliant payment providers; store only transaction IDs/status |

## 3. User rights (implementation suggestions)

- Right of access: provide a data export (CSV/JSON) from the user area.
- Right to rectification: allow profile updates in the UI and keep an edit audit trail.
- Right to erasure: implement either soft-delete plus anonymization or full deletion where legally permitted. Keep accounting records for statutory periods (see retention table).

Anonymization example: replace identifying fields with `Deleted User #<id>` and remove direct contact information from non-accounting tables.

## 4. Retention policy

Automate retention with scheduled jobs and logs showing actions taken.

| Data category | Retention period | Notes |
| ---: | ---: | --- |
| Active member profile | While active | Update on status change |
| Former member (archived) | 3 years after last contact | Then delete or anonymize |
| Accounting / donation records | 10 years | Preserve as required by law; anonymize elsewhere |

## 5. Sensitive data and DPIA

If membership implies political, religious, or other special-category processing (Article 9 GDPR), treat all related data as sensitive:
- Apply stricter access logging, encryption, and consider a DPIA.

## 6. Operational recommendations

- Backups: encrypt and limit access; keep a recovery plan and retention schedule.
- Logging: log access to sensitive data and rotate logs securely.
- Incident response: maintain a breach response plan and procedures for notifications.

## 7. Developer checklist
- [ ] Review DB schema: remove unnecessary personal fields.
- [ ] Forms: default to opt-out privacy-safe settings (newsletter unchecked).
- [ ] Authentication: enforce strong password hashing and MFA for admin roles.
- [ ] Transport security: TLS + HSTS + secure cookies.
- [ ] CSP and security headers configured.
- [ ] Payment handling: delegate to PCI-compliant providers; do not store PANs.
- [ ] Retention jobs: implement cron tasks with logs and soft-delete/anonymization logic.
- [ ] Documentation: maintain RoPA and records of processing activities.

What to do next
- Assign an owner to maintain the RoPA and implement the retention cron jobs. Consider a quarterly dependency/security review.

---

References
- CNIL developer resources and association guide (links above).
