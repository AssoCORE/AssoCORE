---
paths:
  - "back/app/**"
  - "docker-compose.yml"
  - "k8s/**"
---

# GDPR (non-negotiable)

AssoCORE processes members' personal data, so the association running it is a data controller under the GDPR
and the French *Loi Informatique et Libertés* (CNIL guidance applies). Personal data is anything about an
identifiable person: names, usernames, emails, phone numbers, birth dates, messages, attachments, payments,
donations, IPs, and free text that mentions someone. A change that cannot meet these rules is not merged.

## Every PR that adds or changes personal data

A table, column, file, log line, form field or call to an external service. The PR must:

1. **Purpose and lawful basis** (art. 5, 6, 30): state them in the PR, and add or update the processing's entry
   in the register `docs/src/content/docs/reference/gdpr-register.mdx` (purpose, basis, data, recipients,
   retention).
2. **Minimise** (art. 5(1)(c)): collect only what that purpose needs. Every field answers to today's purpose,
   and optional stays optional.
3. **Retention** (art. 5(1)(e)): define how long the data lives and implement the purge in the same PR, as a
   poller in the background worker (`core/worker.py`). Every piece of data has an end date. The only longer
   periods are legal obligations, such as accounting documents and payments (10 years, Code de commerce
   L123-22), and they are cited in the register.
4. **Access and portability** (art. 15, 20): include the data in the user's export (`GET /user/me/export`, JSON).
5. **Erasure** (art. 17): `DELETE /user/me` and `DELETE /user/{id}` delete it or anonymise it irreversibly.
   Data kept under a legal obligation is detached from the account (foreign key → NULL, keeping only the fields
   the law requires) and still purged when that period ends. Deleting an account leaves *other* people's data
   intact.
6. **Rectification** (art. 16): the user can correct it, or it is derived from data they can correct.
7. **Privacy by default** (art. 25): every visibility setting defaults to the most private option, and members
   see only the minimum about each other (the member directory, for example, exposes no email or phone).
8. **Processors** (art. 28): personal data leaves AssoCORE only to services listed in the register under a
   data-processing agreement (Stripe, the SMTP relay, …), and only the fields that service needs. Analytics,
   tracking CDNs, error trackers and AI APIs receive none.
9. **Security** (art. 32): access is checked on the server on every route, admins get least privilege (an admin
   reads only the DMs they are in), and secrets are encrypted at rest as `core/crypto.py` does.
10. **Tests** prove the data appears in the export, disappears on account deletion, and is purged at the end of
    its retention period.

The register, the export endpoint and the worker may not exist yet: the first PR that needs one creates it.

## Code rules

- **Logs carry IDs, never personal data.** Write `user %d`, never a username, email, name, message body, search
  term or token. Request logs stay path-only, without the query string. Log retention is bounded at the infra
  level (CNIL recommends 6–12 months).
- **MariaDB `log_bin` and `general_log` stay off** in compose and k8s. They would record every write, including
  the rows that anonymous polls (F8) keep deliberately unlinked; enabling either breaks that guarantee and has to
  be in the register.
- **Cookies are only the strictly necessary ones**: today, the httpOnly auth cookies, which need no consent. Any
  analytics or tracking needs a consent mechanism first.
- **Emails**: every non-transactional email (newsletters) carries an unsubscribe link and a `List-Unsubscribe`
  header. Transactional mail (password reset, receipts) contains nothing promotional.
