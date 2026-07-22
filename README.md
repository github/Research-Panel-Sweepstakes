# Research-Panel-Sweepstakes

- [Research Panel Sweepstakes Official Rules](https://github.com/github/Research-Panel-Sweepstakes/blob/1128c66f3bb6be5865a34eda3886ad128562712d/GitHub%20Universe%20Customer%20Research%20Sweepstakes%20Official%20Rules.docx.pdf)
- [GitHub Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement)

## How to Conduct a Research Sweepstakes

1. Download or make a copy of an existing Sweepstakes Official Rules document. The [Open Source Community Happiness Study Sweepstakes Official Rules](https://github.com/github/Research-Panel-Sweepstakes/blob/main/Open%20Source%20Community%20Happiness%20Study%20Sweepstakes%20Official%20Rules%202026.pdf) is the pre-cleared template to work from. A plain-text version with fill-in placeholders lives at [`templates/official-rules-template.md`](templates/official-rules-template.md).
2. Rename the document to a title relevant to your study and edit **only** the customizable fields: entry period timing, eligibility audience, link to the study, incentive amount, and winners list. Leave all other legal language exactly as written. Comb through the language carefully — a second pair of eyes is recommended.
3. Open a pull request that adds your document to this repository (instead of committing straight to `main`). The **Official Rules Review Gate** runs automatically and posts a PASS or FLAG comment. Navigate to the repository's main page, click the **Add file** dropdown button, then select **Upload files**, drag and drop your document, and choose *"Create a new branch and start a pull request."*
4. Add the appropriate verbiage to your survey or email copy, such as: *"For official sweepstakes rules, please see the following details here."*
5. Link the new file to your survey or email copy using the URL from your browser. **Make sure you are linking the correct file for your specific study.**

## Agent Review Gate (replaces per-study CELA review)

The Official Rules are pre-cleared legal boilerplate plus a small set of per-study fields. An automated gate ([`.github/workflows/validate-official-rules.yml`](.github/workflows/validate-official-rules.yml)) checks every Official Rules document added or edited in a pull request against the approved template:

- ✅ **PASS** — you changed only the allowed per-study fields and left the boilerplate intact. **No fresh CELA review is required**; you can publish.
- 🚩 **FLAG** — the document changed fixed legal language, dropped a required section, is missing "No Purchase Necessary", uses a prohibited word ("raffle"/"lottery"), or signals a paid entry. **Route to CELA** for review before publishing, or fix the document to match the template.

**Allowed per-study fields:** title, entry period start/end, eligibility audience, survey/study URL, prize description and ARV, number of winners, and the Winners List contact/subject/window.

**Fixed (do not edit):** Sponsor, Definitions, the employee-exclusion and "Void in …" sentences, "No Purchase Necessary", winner-selection mechanics, prize warranty/substitution/tax language, Odds, Release of Liability, Use of Your Entry, and Governing Law.

The conformance rules are defined in [`templates/rules-spec.json`](templates/rules-spec.json). To check a document locally: `python scripts/validate_official_rules.py "Your Rules 2026.pdf"`.

## Watch Outs

- Double-check all customized fields (entry period, eligibility, study link, incentive amount, winners list). Review the document multiple times.
- Make sure to pay the winner within the timeline specified in your rules.
- Participants may reach out to find out who won, so have that information ready and ensure you've listed yourself as the point of contact in the Winners List section.
