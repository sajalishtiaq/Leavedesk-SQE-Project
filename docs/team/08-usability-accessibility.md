# 08. Usability and Accessibility

## 8.1 Automated tasks (Playwright)
* Workflow A task: `UC1-E1` / `UC1-E2` open the form, submit a value the rule rejects, assert that the message tells the user what to fix, correct it, assert the confirmation "Request sent...".
* Workflow B task: `UC2-E1` (reject without note -> message -> correct -> success).
* Keyboard test `KB-1` (`e2e/tests/a11y.spec.ts`): focus order Leave type -> Start date -> End date -> Reason -> Send request, then Enter submits the form.

## 8.2 Tools and procedure
1. `cd e2e && npm run a11y:before` -> axe-core (WCAG 2.0/2.1 A + AA + best-practice) on login, apply form, my leave, approvals; JSON in `evidence/a11y/axe_before_*.json`.
2. `LABEL=before npm run lighthouse` -> Lighthouse accessibility, best practices, SEO on the logged-in screens; JSON in `evidence/lighthouse/`.
3. Merge duplicates: an issue found by both tools counts once (same element + same underlying problem). Fill the table below from the JSON.
4. Fix ONE screen (see 8.4), run `npm run a11y:after` and `LABEL=after npm run lighthouse`, compare.

## 8.3 Findings table (fill from the reports)
| # | Screen | Element | Rule (tool) | User impact | Proposed fix | Priority |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
Prioritise by axe impact (critical > serious > moderate > minor) x number of users affected (login and apply form are used by everybody).
Hints from the source worth checking first: icon-only buttons without accessible names, form errors not linked with `aria-describedby`, colour contrast of badges/status pills, missing `<main>` landmark/page title per route, modal focus trap and focus return.

## 8.4 Before / after
| Metric | Before | After |
|---|---|---|
| axe violations (serious+critical) on the fixed screen | | |
| Lighthouse accessibility score | | |
Fix location: the chosen component in `frontend/src` (commit it on a branch + PR so the CI gate runs).
Status: **not yet executed** - browsers cannot be downloaded in the authoring environment; run the commands above on your laptop.
