# Schema-Level Comparison: Conceptual Diagram vs. RDF Export vs. CIDOC-CRM/CRMtex (v3)

**Sources compared:**
- `Ont_diagram_260519.svg` — the conceptual model
- `data_rdf_digipal_cidoc_20260827.rdf` — DigiPal RDB export, 169,959 `rdf:Description` resources, 142 distinct predicates
- CIDOC-CRM (current release, verified against cidoc-crm.org), CRMtex v2.0

Scope: **schema-level only** — every distinct `rdf:type` and property used in the RDF, checked against the diagram and against the official specifications. Individual instance data was not audited. This supersedes the earlier report run against the previous RDF export (`data_rdf_digipal_cidoc.rdf`); that export is no longer current and this document stands on its own.

**Note on currency (this sync pass)**: the conceptual model has moved substantially beyond what §§1–8 below describe, through an extended live-design phase covering P95, Hand/Writing/Attribute Assignment, the Annotation cluster, P56/Feature/Component, `arch:GraphComponent`, Text/Hand language routing, and more. That work is recorded in full in the companion report, `domain_range_compliance_v3.md`, and in an updated conceptual diagram, `Archetype_ontology_updated.drawio`. This document has been synced (§9) to reflect that work at the schema level — new/changed classes and properties — without duplicating the full conceptual reasoning, which stays in the companion report.

---

## 1. Summary of open findings, by severity

| # | Finding | Status |
|---|---|---|
| 1 | No `P43_has_dimension` anywhere — E54 Dimension (1,324 instances) still linked to its Historical Item only implicitly, via a shared numeric ID embedded in both URIs, never by an explicit triple | **Resolved (Step 2 — implemented and verified in export).** Root cause found: the code already had a `P43_has_dimension` block, but it was guarded on `layout.item_part_id`, a field confirmed (via the Django model and live SQL data) to be never populated in DigiPal — `Layout` only ever links via `historical_item_id` in this dataset, so the block was dead code from the start. Fixed by adding a parallel branch keyed on `historical_item_id`: `Historical_Item_<id>` now gets both `P46_is_composed_of` → `Layout_Historical_Item_<id>` and, where any of `page_height`/`page_width`/`frame_height`/`frame_width`/`tramline_width` is present, `P43_has_dimension` → `Dimension_Historical_Item_<id>`. Confirmed in the export: 295 `P43_has_dimension` triples, all Historical Item → Dimension; all 1,324 Layout resources now have an incoming `P46_is_composed_of` link (initial spot-check misreported 1,323 due to a line-scanning artifact — recounted directly and confirmed no gap). The original `item_part_id` branch is kept as-is, unused in DigiPal but retained as a fallback for other Archetype-based projects that may populate it differently — confirmed via the Django model that no other class (`ItemPart`, `Hand`, `Component`, etc.) carries any dimension/measurement field of its own in the current schema. **Follow-up — two further, deliberate data-quality decisions made and implemented after the fix above:** <br>• **Empty-row filtering.** Investigating the fix surfaced that ~78% of `Layout`/`Dimension` pairs (1,029 and 1,004 of 1,324 respectively) carried no real content at all — only `rdf:type`/`rdfs:label`, or a handful of default-value `False` booleans with nothing else. Per the project lead: a `False` boolean flag is only a meaningful assertion when at least one other field on the row is also populated; on a row with nothing else, it's unset-default noise, not a scholarly claim. A `has_content` guard was added so rows with no real content (all measurement/structure fields null or zero, all boolean flags null or `False`) are skipped entirely rather than generating empty resources — confirmed in the export: `Layout`/`Dimension` counts dropped from 1,324 to 302 each, with the incoming `P46_is_composed_of` link count matching exactly (no orphans). `P43_has_dimension` correspondingly dropped from 295 to 253 — confirmed this is not a regression: the old guard only checked `notna()`, so a small number of rows with a dimension field equal to exactly `0` (implausible as a real measurement) and nothing else were previously still exported; these are now correctly excluded, with zero leftover `0`-valued dimension literals anywhere in the export. <br>• **`on_top_line` excluded from the export entirely, as unreliable source data.** Every populated row in `digipal_layout.on_top_line` is `False` (0 `True`, 1 `NULL`) — but DigiPal's data is predominantly pre-11th-century, and the "above top line"/"below top line" scribal-practice shift this field records is dated in the literature to the early-to-mid 13th century (Ker 1960, *"From 'Above Top Line' to 'Below Top Line': A Change in Scribal Practice,"* Celtica; refined by Roberts 2005 to c. 1220 and Brown 2008 to 1220–1240) — centuries after DigiPal's normal range. All-`False` for this field is therefore scholarly-implausible and symptomatic of the field being unpopulated/defaulted rather than genuinely observed, not a real finding that "below top line" ruling was in fact used throughout. Confirmed not used by any other Archetype-based project known to the project lead. Excluded from the export by decision (commented out, not deleted, with the rationale recorded in the code) — a deliberate point of omission for the record, in the same spirit as the earlier P198i/patron-saint exclusion. **A separate, unrelated bug was also fixed while in this code**: `insular_pricking` had been mistakenly written under the `EX.columns` predicate (a copy/paste error, colliding with the real `columns` field), now corrected to its own `EX.insular_pricking` predicate (301 triples, confirmed in the export). |
| 2 | `crm:P45_consits_of` — misspelled predicate (should be `consists_of`), 93 uses | **Resolved, confirmed** — 0 occurrences of the misspelling in the current export; all 93 uses now `P45_consists_of` (code, line 541; changelog line 4). *(Status corrected in Step 1 review — the earlier "Open" status was stale.)* |
| 3 | `E52_Time_Span` (underscore) used throughout instead of the official CIDOC-CRM URI `E52_Time-Span` (hyphen) | **Resolved and verified** — confirmed fixed in the `data_rdf_digipal_cidoc_20260828.rdf` export (§8.5) |
| 4 | classicmayan.org `Graph → Ontograph` subclass edge still present, despite an earlier decision to drop it — now joined by two more classicmayan-namespaced classes (`Sign`, `Sign_Function`) | **Resolved by removal, confirmed.** All four `subClassOf` declarations (Graph→Ontograph, Sign→E33, Sign_Function→E33, and a second Graph→E33), plus the now-unused `Idiomcat` namespace binding and `seeAlso` link, removed from the code — six lines total, self-contained, nothing else references them. **Conceptual rationale kept on record, not just "dropped as unhelpful"**: Idiomcat was the closest existing ontology found addressing sign *function*, included to (a) potentially align Archetype with related projects, and (b) mark that Archetype itself has no treatment of sign function at all, as a hook for any future project wanting to model that. Dropped from the RDF specifically because it was never actually used, not because the underlying idea was rejected — could be revisited as a genuine cross-project alignment effort later. |
| 5 | `frbroo:F3_Item` — 1,675 real instances (matching Item_Part's count exactly), not a real FRBRoo class, never declared in the subclass hierarchy | **Confirmed error** — should be `frbroo:F5_Item` |
| 6 | E65_Creation has dropped from 602 real instances to 0; a new pattern had appeared with the same cardinality, `HistoricalItem —[P196i is defined by]→ E92 Spacetime Volume` | **Resolved**: E92 Spacetime Volume dropped (its joint date+place uncertainty mechanism isn't needed — never reflected in the data); Historical Item's date/place now handled via `E13 Attribute Assignment` instead. Production vs. Creation made moot. Full design in `domain_range_compliance_v3.md` §2.7. **Step 1 verification note**: confirmed 0 real instances of both classes in the current export; two leftover class-hierarchy scaffold triples remain for each (`E4_Period rdfs:subClassOf E92_Spacetime_Volume`, `E92_Spacetime_Volume rdfs:subClassOf E1_CRM_Entity`; `F28_Expression_Creation rdfs:subClassOf E65_Creation`, `E65_Creation rdfs:subClassOf E63_Beginning_of_Existence`/`E7_Activity`) — schema-only, not instance data, but flagged for a decision at the OWL-formalisation stage (prune vs. keep for reference) |
| 7 | `P196i is defined by` used (602 triples, see #6) rather than `P170i time is defined by`, the property discussed earlier for the "période estimée"/estimated time-span issue | **Moot** — superseded along with #6. `P196i`/E92 Spacetime Volume is dropped entirely in the target design, not merely re-routed to `P170i`; Historical Item's date/place now goes via `E13 Attribute Assignment` instead of any Time-Span-defining property |
| 8 | ~64,000 `oa:Annotation` / `arch:Graph` instances plus associated image-region fields (`geo_json`, `rotation`, `cutout`, `vector_id`, etc.) — a large, entirely new data category | **Resolved.** Fully assessed and designed against the diagram — see §9.3 and `domain_range_compliance_v3.md` §2.10. `Annotation` deliberately kept outside CIDOC-CRM (Web Annotation vocabulary throughout: `oa:hasTarget`, `oa:hasBody`), `arch:Graph` unaffected |
| 9 | `arch:Stroke` — still 0 occurrences anywhere (no `rdf:type`, no `subClassOf`) | Confirmed expected, not a defect |

Properties that remain entirely absent from the RDF: P62 depicts, P91 has unit, P99 dissolved, frbr:R3 is realised in, idiomcat:* (namespace no longer appears at all).

**Also confirmed fixed in code, not yet re-verified in RDF:** all hyphenated CIDOC-CRM class names — `E22 Human-Made Object`, `E24 Physical Human-Made Thing`, `E25 Human-Made Feature`, `E71 Human-Made Thing`, `E52 Time-Span`, etc. — were previously exported with underscores throughout (`E22_Human_Made_Object` rather than `E22_Human-Made_Object`) due to a Python/rdflib syntax constraint (hyphens aren't valid in attribute-access identifiers); resolved by switching to `Namespace[...]` item-access syntax. Should be checked in the next RDF export.

Resolved issues from the previous review round are listed in §5 for the record, but are not carried forward as open items.

---

## 2. Classes: diagram vs RDF `rdf:type` usage

### 2.1 CIDOC-CRM classes in use

| Class | RDF URI | Instances | Note |
|---|---|---|---|
| E18 Physical Thing | `E18_Physical_Thing` | 4,183 | ✓ |
| E26 Physical Feature | `E26_Physical_Feature` | 2,077 | ✓ new/expanded usage |
| E42 Identifier | `E42_Identifier` | 1,504 | ✓ |
| E54 Dimension | `E54_Dimension` | 1,324 | ✓ present; still only implicitly linked (§1.1) |
| E36 Visual Item | `E36_Visual_Item` | 995 | ✓ newly real (previously schema-only) |
| E39 Actor | `E39_Actor` | 993 | ✓ newly real |
| E74 Group | `E74_Group` | 800 | ✓ |
| E92 Spacetime Volume | `E92_Spacetime_Volume` | 602 | New — see §1.6 |
| E31 Document | `E31_Document` | 601 | ✓ |
| E62 String | `E62_String` | 427 | ✓ newly real |
| E53 Place | `E53_Place` | 359 | ✓ |
| E55 Type | `E55_Type` | 333 | ✓ |
| E21 Person | `E21_Person` | 278 | ✓ |
| E73 Information Object | `E73_Information_Object` | 180 | ✓ |
| E52 Time-Span | `E52_Time_Span` | 158 | URI naming issue — see §1.3 |
| E4 Period | `E4_Period` | 158 | ✓ |
| E66 Formation | `E66_Formation` | 36 | ✓ newly real |
| E56 Language | `E56_Language` | 20 | ✓ |
| E8 Acquisition | `E8_Acquisition` | 10 | ✓ newly real |
| E57 Material | `E57_Material` | 6 | ✓ |
| E30 Right | `E30_Right` | 5 | New, not in diagram |
| E58 Measurement Unit | `E58_Measurement_Unit` | 1 | ✓ newly real |

### 2.2 arch:/CRMtex classes now real (previously schema-only or absent)

`arch:Graph` (64,028 — see §1.8), `arch:Idiograph` (9,657), `arch:Hand` (1,478), `Item_Part` (1,675), `Historical_Item` (1,553), `Current_Item` (1,490), `arch:Scribe` (576), `TX7 Written Text Segment` (459), `TX1 Written Text` (385), `arch:Feature` (134), `TX3 Writing System` (132), `arch:Allograph` (121), `arch:Character` (67), `arch:Component` (47), `arch:Script` (37), `arch:Ontograph` (37), `TX10 Style` (23), `TX2 Writing` (17), `TX13 Script` (4).

**Still absent as real instances:** `arch:Stroke` (confirmed expected, §1.9), `Element_of_Style` (present in the class hierarchy only, 0 real instances).

### 2.3 Class hierarchy (`rdfs:subClassOf`)

101 `subClassOf` triples now present (up from 29), and the hierarchy is substantially fuller than before — it now includes most of the core CIDOC-CRM backbone (E1 CRM Entity down through E7 Activity, E39 Actor, E90 Symbolic Object, etc.), not just the arch:/CRMtex extension classes. The `Historical_Item`/`Current_Item`/`Item_Part` URIs used for typing now match their `subClassOf` declarations exactly (previously a mismatch — see §5).

Two things worth noting structurally:
- `Historical_Item` and `Item_Part` are now each declared `⊑ frbr:F5_Item` **and** `⊑ frbr:F3_Manifestation`.
- `frbr:F3_Manifestation` is itself now declared `⊑ E55_Type`.

Neither of these is flagged as a problem here — they weren't part of the original report's scope and haven't been discussed — but they're new structural facts worth being aware of before the diagram/Manifestation discussion resumes.

---

## 3. Properties: diagram vs RDF predicates

**Implemented, CRM/CRMtex-compliant naming:** P1 is identified by (1,553), P2 has type (13,908), P3 has note (427), P4 has time-span (158), P7 took place at (268), P8 took place on or within (1,340), P11 had participant (173), P14 carried out by (28), P22 transferred title to (7), P33 used specific technique (763), P46 is composed of (7,687), P48 has preferred identifier (implicit via P1 chain), P50 has current keeper (2,663), P56 bears feature (9,514), P70 is documented in (2,077) / P70i is documented in (680), P72 has language (231), P74 has current or former residence (3,104), P89 falls within (183), P95 has formed (46), P104 is subject to (42), P106 is composed of (64,028), P108 has produced (401), P138 represents (76,024), P148 has component (154), P196i is defined by (602 — see §1.7), P198i is held or supported by (41), TXP1 used writing system (132), TXP4 has segment (459), TXP12 has style (495), TXP16 employs script (132).

**Implemented, non-compliant naming (typos/mislabelling — already fixed on your end for the next export):** `P45_consits_of` (93 — see §1.2), `P92_brought_into_existance` (1,675), `P107_is_current_or_former_member_of` (123).

**Not implemented anywhere:** P62 depicts, P91 has unit, P99 dissolved, frbr:R3 is realised in, arch:prescribes visual item, arch:operates within script style, idiomcat:has sign function, idiomcat:is Graph Of.

---

## 4. Implementation-only fields (expected, not a problem)

A large number of `digipal.eu/ontology#` literal predicates exist purely as flat database columns with no CRM/diagram equivalent, consistent with normal RDB-flattening — e.g. `shelfmark`, `pagination`, `columns`, `vernacular`, `neumed`, `page_height`/`page_width`, `frame_height`/`frame_width`, `num_inks`, `num_colours`, `legacy_reference`, `copyright_notice`, and (new in this export) a substantial set of image/annotation-specific fields — `geo_json`, `rotation`, `cutout`, `vector_id`, `iipimage`, `width`/`height`, `custom_label`, `keywords_string` — associated with the new `oa:Annotation`/`arch:Graph` dataset (§1.8). None of these appear to be misapplied CRM terms.

---

## 5. Resolved (for the record, not carried forward as open items)

- Historical_Item/Current_Item URI mismatch (subClassOf declarations vs. instance typing) — fixed, both now consistent.
- `Component`/`Generalised_Allograph` wrongly declared `⊑ E26_Visual_Item` — fixed, now correctly `⊑ E36_Visual_Item`.
- `P__LIEN_A_VOIR` placeholder predicate — removed entirely.
- Malformed CRMtex class URIs (missing `/` separator) — fixed.
- A large batch of previously-unimplemented diagram properties are now implemented (P1, P22, P33, P56, P92, P106, P107, P138, P148, TXP1, TXP12, TXP16 — see §3 for current naming status of each).

---

## 8. Regression check — RDF v3 (typo-fix pass, same file, same date)

Same file name and date as the export checked in §7 (`data_rdf_digipal_cidoc_20260827.rdf`), but different content (hash differs) — this reflects the round of "easy typo" fixes discussed after §7. Checked systematically against every item in §7 plus a full regression pass for anything new.

### 8.1 Confirmed fixed

| Item | Before | Now |
|---|---|---|
| Hyphenated CIDOC-CRM class names | `E22_Human_Made_Object` (underscore) | **Fixed** — `E22_Human-Made_Object`, `E52_Time-Span`, `E24_Physical_Human-Made_Thing`, `E25_Human-Made_Feature`, `E71_Human-Made_Thing` all now correctly hyphenated and confirmed as the actual `rdf:type` values in use |
| `P45_consits_of` | Misspelled | **Fixed** — `P45_consists_of`, same 93 uses |
| `P92_brought_into_existance` | Misspelled | **Fixed** — `P92_brought_into_existence`, same 1,675 uses |
| `P107_is_current_or_former_member_of` | Conflated code+inverse label | **Fixed** — `P107_has_current_or_former_member`, same 123 uses |
| `TX11_Grapheme_Occurance` | Misspelled | **Fixed** — `TX11_Grapheme_Occurrence` |
| `frbroo:F3_Item` (§7.3, confirmed error for F5_Item) | 1,675 instances of a non-existent class | **Fixed** — no longer appears anywhere; those resources are now correctly typed via `frbroo:F3_Manifestation` (1,675) and `frbroo:F5_Item` (2,362, up from 687 — now covering more of the Historical_Item/Item_Part/Current_Item family) |

### 8.2 New issues introduced by this round of fixes

1. **`P4 has time-span`'s URI is now malformed differently.** Previously `P4_has_time_span` (underscore, not matching official convention but not previously flagged as its own issue); now `P4_has_timespan` — **the underscore between "time" and "span" has been dropped entirely**, with no hyphen inserted either. Checked directly against the official CIDOC-CRM RDFS encoding rules: property names follow the same convention as class names (spaces → underscores, internal hyphens in the English name preserved), and the class this property is named after is `E52_Time-Span`. **The correct fragment should be `P4_has_time-span`** (hyphen, matching the pattern already correctly applied to the class names in §8.1). This looks like the same fix pattern applied inconsistently — likely a manual edit that dropped a character rather than converting underscore to hyphen.
2. **A new hyphen/underscore mismatch on E26 Physical Feature, in the class hierarchy only.** The two `subClassOf` declarations involving E26 (`E25_Human-Made_Feature ⊑ E26-Physical_Feature` and `E26-Physical_Feature ⊑ E72_Legal_Object`) now use a **hyphen between "E26" and "Physical"** (`E26-Physical_Feature`) — but every real instance of this class (2,077 of them) is correctly typed `E26_Physical_Feature` (underscore). Only 2 occurrences of the wrong form exist (both in the class hierarchy), but because the URIs don't match, **the E25→E26 and E26→E72 links in the subclass hierarchy are now silently broken** — the same category of bug as the Historical_Item/Current_Item URI mismatch fixed earlier in this project (schema report §5), just newly introduced here.

### 8.3 Also new, not a defect — worth confirming intentional

**Namespace change for all `arch:`/local extension classes**: every instance previously under `https://digipal.huma-num.fr/` (Historical_Item, Current_Item, Item_Part, Graph, Hand, Scribe, etc.) is now under **`https://digipal.eu/`** instead — and this has been applied consistently on both sides (both `rdf:type` instance data and the `subClassOf` hierarchy declarations use the new namespace together), so it does **not** reintroduce the URI-mismatch pattern from §8.2. Flagging this only because it's a real, visible change worth confirming is deliberate — any external tooling, saved queries, or links built against the old `digipal.huma-num.fr` URIs will no longer resolve.

**New class and hierarchy addition, not yet discussed**: `frbroo:F28_Expression_Creation` now appears, declared as a subclass of **both** `E12_Production` and `E65_Creation`, with `TX2_Writing` now declared `⊑ F28_Expression_Creation`. This wasn't part of the typo-fixing scope but showed up as a side effect. Now that E65 Creation/E92 Spacetime Volume has been resolved (§1 item 6; `domain_range_compliance_v3.md` §2.7 — Writing moved to Hand-level, Historical Item's date/place via Attribute Assignment), this F28_Expression_Creation hierarchy addition needs revisiting to confirm whether it still serves a purpose or is a leftover from the superseded approach.

Also unchanged: `Item_Part` and `Historical_Item` are now each additionally declared `⊑ frbroo:F3_Manifestation` (alongside their existing `⊑ F5_Item`) — new, not yet discussed.

### 8.5 Confirmed fixed (second pass, `data_rdf_digipal_cidoc_20260828.rdf`)

Both remaining items from §8.2 are now fixed, verified against a fresh export (two attempts — the first upload under this filename hadn't actually picked up the fix; the second did). A full predicate-set and type-set diff against the §8.1–8.4 export confirms these are the *only* two changes — nothing else shifted, no new regressions:

- **`P4 has time-span`** — now correctly `P4_has_time-span` (hyphen), matching the official convention.
- **E26 Physical Feature hierarchy mismatch** — now correctly `E26_Physical_Feature` (underscore) in both `subClassOf` declarations, matching the 2,077 real instances. The E25→E26→E72 chain is properly connected again.

The `digipal.huma-num.fr` → `digipal.eu` namespace change (§8.3) is confirmed as a deliberate, permanent fix, not something to revert — the old namespace "should never have been there."

No open items remain from the typo-fixing round. Everything else — the substantive domain/range issues and the annotation dataset — is exactly as recorded below. (The E65 Creation/Spacetime Volume discussion and the classicmayan.org classes referenced in earlier versions of this note have since been resolved — see §1 items 4 and 6, and `domain_range_compliance_v3.md` §2.7.)

### 8.6 Still open, unaffected by this round

- classicmayan.org classes — **resolved by removal**, see §1 item 4.
- `P43_has_dimension`, `P62_depicts`, `P91_has_unit`, `P99_dissolved`, `frbr:R3_is_realised_in` — still entirely absent.
- E65 Creation → E92 Spacetime Volume / P196i redesign — **resolved** (see §1 item 6). F28_Expression_Creation note from §8.3 needs revisiting in light of this.
- The ~64,000-record annotation/image-region dataset — still not assessed against the diagram.
- Every domain/range compliance finding (P95 reversed argument, P198i/patron data, P72 on Historical Item, P50 Archive→Place, the P65 violations, P108/Hand, untyped Writing events, reformer/E8 Acquisition dual-typing) — **completely unchanged**; see `domain_range_compliance_v3.md` §6 for the full regression check against that document.

---

## 9. Sync pass — schema-level summary of the extended design phase (Hand/Writing redesign through the updated diagram)

Everything below was worked out in `domain_range_compliance_v3.md` through extended live design discussion, not from a new RDF export — none of it has been re-verified against actual RDF instance data the way §§1–8 were, since (per project staging) it represents the agreed target design, with code changes applied incrementally as we went. Full reasoning for all of it lives in the companion report; this section exists so the schema-level facts (new/changed classes and properties) are captured here too, not only there.

### 9.1 New classes

- **`E13 Attribute Assignment`** — the mechanism now used throughout for scholarly dating/place/origin attribution (Hand's accepted date, Historical Item's date and place evidence, the unified Archive/ItemOrigin design), via `P140 assigned attribute to` / `P141 assigned`. Companion report §2.7, §2.3.
- **`arch:GraphComponent`** — a Graph's specific realization of a Component (paralleling `Idiograph`'s relationship to `Allograph`), `⊑ E36 Visual Item`. Replaces the old direct `Graph —P65→ Component` shortcut entirely (dropped, chain-only decision). Companion report §2.12.

### 9.2 Property changes

- **`P108 has produced`** — Hand's Scribe/production relationship moved to a per-Hand `TX2 Writing` (`TX2 Writing —P108→ Hand`, `—P14→ Scribe`), replacing the old `Hand —P108→ Scribe` domain/range violation. Companion report §2.7.
- **`P2 has type`** — now used for `Component —P2→ Feature` (was `P56`) and `GraphComponent —P2→ Feature` (was `P56` via the untyped `GraphCompo_<id>` bug); also for `Text_categories` (was entirely missing). Companion report §2.2, §2.12.
- **`P148 has component`** — now used for `Allograph/Character —P148→ Component` (was `P65`) and `Generalised Allograph —P148→ Component` at the diagram's class level. Companion report §2.6.
- **`P56 bears feature`** — now used for `Item Part —P56→ Hand` (newly made explicit; previously only implicit/buggy). Companion report §2.6.
- **`P70 documents` / `P70i is documented in`** — `Description` (retyped `E31 Document`, was `E26 Physical Feature`) now uses `P70 documents` for its Text/Historical Item links (was `P56 bears feature`) and correctly-suffixed `P70i is documented in` for its Source link (was a hybrid `P70_is_documented_in` matching neither real property). Companion report §2.11.
- **`TXP9 is encoded using` / `TXP6 encodes`** — new: `Text —TXP9→ (Text's own) TX3 Writing System —TXP6→ E56 Language`, and the same pattern added to Hand's existing Writing System. Both entities get independently-sourced language facts, not derived from one another. Companion report §2.2.
- **`TXP4 has segment`** — direction corrected (`Text —TXP4→ Segment`, was reversed). Companion report §2.2.
- **`P140 assigned attribute to` / `P141 assigned`** — new, see §9.1.
- **`oa:hasTarget` / `oa:hasBody`** (Web Annotation vocabulary, not CIDOC-CRM) — `Annotation —hasTarget→ Image`, `Annotation —hasBody→ Graph`, replacing `Image —P138 represents→ Annotation`. `dcterms:creator` was designed for Annotation's author but **not implemented** — logged as data loss (annotation authorship, and responsibility/attribution data generally, is systematically absent from the export). Companion report §2.10.
- **`P198i is held or supported by`** — removed entirely (patron-saint data dropped, confirmed invalid CIDOC-CRM for this use case). Companion report §2.4.

### 9.3 Also resolved: the ~64,000-record Annotation dataset (§1 item 8)

Fully assessed. `oa:Annotation` deliberately stays outside CIDOC-CRM's type system throughout — a project decision, not a gap (the "pure/technical" layer, with `arch:Graph` carrying the CRM-integrated, scholarly-identified side). Covers both graph-linked and "editorial"/authorial annotations without special-casing, since the design only depends on whether `graph_id` is populated. Two fields investigated and confirmed but deliberately not implemented: `author_id` (→ `dcterms:creator`, logged as systematic data loss) and `before_id`/`after_id` (Allograph-typed adjacency; confirmed genuine via the Django model, no CRM/CRMtex property fits, logged as lost data). Full detail: companion report §2.10.

### 9.4 Data quality, not modelling: source-data issue found

`Language.name` value `language_id = 7` ("Latin with Bounds") confirmed, via two spot-checked instances cross-referenced against LangScape and eSawyer, to cover genuinely different real situations under one label — not a modelling problem, a source-data correction needed before the language/vernacular unification (§9.5) can fully proceed. Out of scope to fix here per the project lead. Companion report §2.2.

### 9.5 Deferred, not yet implemented (see companion report §7 for full detail)

- Language/vernacular unification (`historicalitem.language`/`.vernacular`, `historicalitemdate.vernacular`, `hand.latin_only` → routed via each entity's own Writing System) — design fully settled (§9.2), consistency-checked (mapping confirmed correct, ~7% data-entry error rate found and needs correcting first).
- `component_features` (Component/Feature controlled vocabulary) — moving to a standalone SKOS file, sharing URIs with the core RDF; not yet built. Candidates flagged for the same treatment: `Ontograph`, `Allograph`.
- `dateevidence`/`HistoricalItemDate`/`ItemOrigin` evidentiary trails (who/reference behind each dating/origin claim) — target `E13 Attribute Assignment` shape settled, data not yet exposed in the export.
- Hand vs. Hand Instance (scribal identity vs. item-part-bound occurrence) — conceptual design agreed, not implemented.
- Systemic float-ID bug — **fully fixed for URI construction** (139 interpolations wrapped in `int()`, verified complete); the same issue in plain `Literal(...)` values not scanned, logged as lower-severity future work.
- `EX:` literal property review against core CIDOC-CRM — not yet done.
- SQL-to-RDF mapping report — deferred until modelling is fully finalised.

### 9.6 Updated conceptual diagram

A new version of the conceptual diagram, `Archetype_ontology_updated.drawio`, incorporates every change through §9.2 above (plus the classicmayan/E65-Creation resolutions from §1). Layout is auto-generated by conceptual cluster, not manually optimised — expect to need visual rearrangement. A handful of judgment calls extending confirmed patterns to parts of the diagram never explicitly discussed are flagged in the diagram itself for review (Stroke/Feature harmonisation, the `arch:Text` labelling choice, the new Annotation-cluster colour, and the Description/Source/Reference omission).

