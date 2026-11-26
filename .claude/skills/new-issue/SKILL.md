---
name: new-issue
description: File a GitHub issue (epic, story, task, bug or tech debt) whose body the repo's auto-labeler and issue-linker can parse. Use whenever creating an issue in this repo with `gh`.
---

`gh issue create` skips the issue forms in `.github/ISSUE_TEMPLATE/`, but two workflows read the body the forms
would have produced: `auto-labeler.yml` turns `### <field>` sections into labels, and `issue-linker.yml` makes
the issue a sub-issue of whatever `Parent Story #N` / `Parent Epic #N` names. A free-form body silently loses both.

1. **Pick the template.** `02_story` for a user-facing feature, `03_task` for technical work (usually under a
   story), `04_bug`, `05_technical_debt`, and `01_epic` only when the user asks for one. Read the chosen `.yml`
   now: its fields change.

2. **Title**: the template's `title` prefix (`[TASK] `, `[STORY] `, …) followed by a short summary.

3. **Body**: one section per `body` entry, in template order, skipping `type: markdown` entries:

   ```text
   ### <attributes.label>

   <value>
   ```

   - Dropdowns: one of the `options` strings, verbatim (`1. difficulty : medium`, with its odd spacing).
   - Optional fields left empty: `_No response_`.
   - Parent fields: `#<N>`. Leave them `_No response_` when no parent fits, and expect that issue-linker
     run to fail (it requires a parent). The failure is harmless.
   - Fill every `required: true` field. Ask the user for anything you cannot infer, such as priority.

4. **Create**: write the body to a file in the scratchpad, then
   `gh issue create --title "<title>" --label "<template labels>" --body-file <file>`, adding `--assignee @me`
   when the user is about to work on it.

5. **Check**: `gh issue view <N> --json labels` should show the dropdown labels within a minute. If they are
   missing, the body format is off: fix it with `gh issue edit <N> --body-file <file>`.
