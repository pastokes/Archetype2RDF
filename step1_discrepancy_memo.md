# Step 1 — Discrepancy Memo: Reports vs. Actual RDF/Code State

Checked `ontology_rdf_schema_comparison_v2.md` and `domain_range_compliance_v2.md` against
`data_rdf_digipal_cidoc.rdf` (174,176 resources) and `creation_rdf_float_id_fixed.py`.
Below: only items where the report's stated status doesn't match what the RDF/code
actually show. Everything not listed here was verified as accurate (e.g. E52 Time-Span
hyphen fix, F3→F5 Item fix, classicmayan/Idiomcat removal, arch:Stroke absence, P198i
removal, P148_has_component swap, Annotation→Graph hasBody link, Description→E31
Document/P70, GraphComponent creation, float-ID int() wrapping — all confirmed as
described).

## A. Report is stale — code/RDF are actually *further along* than stated

1. **`ontology_rdf_schema_comparison_v2.md` #2 — `P45_consits_of` misspelling.**
   Report status: "Open (cosmetic)". Actual: RDF has **0** occurrences of
   `P45_consits_of` and 93 correctly-spelled `P45_consists_of`. Code (line 541) uses
   the correct spelling, and the file's own header changelog even notes the fix
   (line 4: `consits_of -> consists_of`). **This is resolved, not open.**

2. **`domain_range_compliance_v2.md` #1 — P95 has formed direction.**
   Report status: "Fix agreed and drafted... not yet re-verified in an export."
   Actual: RDF shows the correct direction throughout (subject = `InstiFoundation_<id>`
   typed `E66_Formation`, predicate `P95_has_formed`, object = `Institution_<id>`).
   Code confirms: `E8_Acquisition` is only used once, as a dead subClassOf schema
   declaration (no instances); refoundation events are typed `E66_Formation`
   throughout (not dual-typed); founder/reformer are linked via role-qualified
   `P14_carried_out_by_founder` / `P14_carried_out_by_reformer`, exactly as the
   agreed design describes. **This fix is implemented and verified in the current export.**

3. **`domain_range_compliance_v2.md` #7 (partial) — Historical Item Date evidentiary data.**
   Report says the `HistoricalItemDate` evidentiary trail is "unexported... deferred to
   the next stage." Actual: the `historicalitemdate` loop (code ~line 641) already
   captures `hist_date['evidence']` via `P3_has_note` on the `E13_Attribute_Assignment`
   node (`HistItemDate_<id>`), along with `vernacular`/`addition`/`dubitable` as `EX:`
   literals. **This part of the data-loss finding is resolved, not deferred** — worth
   splitting from the still-genuinely-unexported parts (Hand's `dateevidence`, and
   `ItemOrigin`'s evidentiary data — see B.1 below).

## B. Report claims resolution that code doesn't fully show

1. **`domain_range_compliance_v2.md` #3 & #7 — ItemOrigin not actually unified onto E13 Attribute Assignment.**
   Report §2.3 says the P50 Archive→Place bug was "resolved... unified with
   `ItemOrigin` onto `E13 Attribute Assignment`," and §2.7 describes Historical Item's
   date/place uniformly going via `E13 Attribute Assignment`. Actual code shows two
   *different* patterns:
   - The `archive` loop (~line 325) **is** migrated: creates `Archive_<id>` typed
     `E13_Attribute_Assignment`, with `P140_assigned_attribute_to` → historical item and
     `P141_assigned` → place. This part matches the report.
   - The separate `itemorigin` loop (~line 487) is **not** migrated: it still writes to
     an untyped `Writing_<historical_item_id>` resource via `P7_took_place_at` (place)
     and `P11_had_participant` (institution) — the older pattern, not `E13 Attribute
     Assignment`, and the resource still has no `rdf:type` at all.
   So only one of the two originally-conflated tables (Archive) is unified; ItemOrigin
   still needs the same treatment. Worth confirming whether this was an intentional
   staging (Archive first) or an oversight.

2. **`domain_range_compliance_v2.md` #7 — untyped `Writing_<id>` resources still present.**
   Report describes the agreed design as "Writing moves to Hand-level (`TX2 Writing`
   for Scribe/Item Part)," and code even has a commented-out block (~line 662) that
   would type these as `CRMtx.TX2_Writing` keyed by `historicalitemdate.id`. But the
   *live* code (in the `itempartitem` and `itemorigin` loops) still builds
   `Writing_<historical_item_id>` — keyed by Historical Item, not Hand — and never
   types it at all. This looks like the report is describing a design that's agreed
   but not yet wired into the live code path (consistent with your process — proposed
   in step 1/discussed, to be implemented in step 2) rather than a contradiction, but
   flagging it since the report's phrasing ("Consolidated design agreed") could be read
   as "done."

## C. Minor / cosmetic, not affecting report accuracy

- **Dead schema declarations for dropped classes.** `E92_Spacetime_Volume` and
  `E65_Creation` each appear twice in the RDF — but only as class-hierarchy scaffold
  triples (e.g. `E4_Period rdfs:subClassOf E92_Spacetime_Volume`, `E65_Creation
  rdfs:subClassOf E63_Beginning_of_Existence`), not as instance data. Zero real
  instances of either class exist, which matches the reports' "dropped to 0" claims.
  Not a defect, but worth a note for the later OWL-formalisation step (#8 in the phase
  plan) — do we want the standalone OWL file to still declare classes that have no
  role in the current model, or prune them?
- **P56_bears_feature count**: RDF shows 8,603 uses vs. the report's "9,514+" — plausibly
  just from other fixes shifting counts since the report was written; not itself a
  concern, flagging only for completeness.

## Suggested next step

Given A.1–A.3 are straightforward status corrections and B.1–B.2 are real open gaps,
I'd suggest updating both reports to reflect this memo (fold A items into "Resolved,"
split B.1 into "Archive: resolved / ItemOrigin: still open," and clarify B.2 as
"design agreed, not yet implemented") before moving to Step 2 (proposing the remaining
code changes). Let me know if you want me to make those edits now, or if you want to
verify any of the above against the source data first.
