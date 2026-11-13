# EX: Properties Alignment — Standardization Review (Phase 2, Step 6)

Companion to `ontology_rdf_schema_comparison_v3.md` and `domain_range_compliance_v3.md`. Kept as a separate report by request, to avoid the other two growing too long to follow. Covers the review of the project's ~100 custom `EX:` catch-all properties: which can be aligned to existing standards (CIDOC-CRM's own properties, Dublin Core Terms, SKOS), which are genuinely custom domain facts needing only a formal `owl:DatatypeProperty` declaration, and which are application/interface plumbing that shouldn't be part of the formal ontology at all.

This work was prompted by a broader question about what it would take to produce a standalone OWL file (the next major deliverable after the current RDF/code error-fixing pass). Two things became clear in scoping that: (1) most of the script's existing class-hierarchy scaffold is already effectively a first draft of the OWL TBox, just interleaved with instance data rather than separated out; (2) the ~100 `EX:` properties are the biggest concrete gap — no `owl:DatatypeProperty`/`owl:ObjectProperty` declarations, no `rdfs:domain`/`rdfs:range`, and (per this review) roughly a fifth of them could be upgraded to standard vocabulary terms rather than formalized as custom properties, gaining real LOD interoperability rather than just RDF-DL correctness. See `domain_range_compliance_v3.md` §7 for the fuller OWL-file discussion this grew out of.

---

## 1. Summary of the triage

All ~100 distinct `EX:` properties currently used in the script, sorted into four buckets. This is not a per-property domain/range check the way the other two reports do for CRM properties — it's a classification pass, since the volume makes individual scrutiny of every property impractical and mostly unnecessary (most are simple literal-valued facts with no ambiguity).

| Bucket | What it means | Approx. count | Action |
|---|---|---|---|
| **1 — Standard vocabulary match** | A clean, honest fit exists in Dublin Core Terms, SKOS, or CIDOC-CRM's own `P3 has note` | ~18 properties, 9 target predicates | Swap the predicate, keep everything else the same. Real interoperability gain, near-zero cost. Being done now, one predicate at a time. |
| **2 — Interface/application plumbing** | UI rendering parameters, internal ordering, file paths, technical identifiers — not facts about manuscripts | ~20+ properties | Exclude from formal ontology entirely. No mapping, no diagram presence. Some are worth a separate question about whether they belong in the export at all (out of scope for this pass). |
| **2b — Explicitly internal** | Textually similar to Bucket 1 candidates but deliberately marked "internal only" (curatorial working notes) | 2 properties (`internal_note`, `internal_notes`) | Exclude from any public-facing mapping, for a different reason than Bucket 2 (privacy/scope, not technical irrelevance) |
| **3 — Genuine relationships / bigger modelling opportunities** | Not a simple vocabulary swap — either a real class-to-class relationship never modelled, or a recurring pattern worth documenting once | ~5–6 properties/patterns | Needs the project lead's judgement, not a mechanical fix. Logged individually below, not yet actioned. |
| **4 — Genuinely custom** | Domain-specific facts (physical measurements, boolean flags, counts) with no honest external match | ~50 properties | Keep as `EX:`, just add a formal `owl:DatatypeProperty` + `rdfs:domain`/`rdfs:range` declaration when the OWL file is built. No individual scrutiny needed — not part of this review's remaining work. |

Plus two small cleanup items outside the bucket system entirely (§4 below).

---

## 2. Bucket 1 — Standard vocabulary matches, in progress

| Standard predicate | Covers | Status |
|---|---|---|
| `dcterms:description` | `Decoration.description`, `Current_Item.description`, `Appearance.description`, `HandDescription.description` | **Proposed, not yet implemented.** Confirmed against the Django model: all four are genuine `TextField`/`CharField` content fields. `Image.caption` was initially considered for this too but reclassified to Bucket 2 (see §3) |
| `dcterms:rights` | `Repository.copyright_notice` | Not yet started |
| `dcterms:bibliographicCitation` | `Reference.full_reference` | Not yet started |
| `dcterms:subject` | `Image.keywords_string` | Not yet started. Currently a single comma-separated string rather than multiple values — a data-shape question to flag when this is picked up, not a blocker to the predicate swap itself |
| `dcterms:date` | `date` (generic, several tables), `Institution.foundation`, `Institution.refoundation` | Not yet started. For `foundation`/`refoundation` specifically, this is a fallback — the better fix is putting the date on the `E66_Formation` event itself via `P4_has_time-span`, not a bare literal on `Institution`; flagged as the *preferred* fix, with the DC mapping as a lesser interim one if that's not pursued now |
| `skos:altLabel` | `Repository.short_name` | Not yet started |
| `P3_has_note` (CIDOC-CRM, already an established pattern in this export, e.g. `Date`'s evidence text) | `comments` (several tables), `Owner.evidence` | Not yet started |
| `rdf:value`, on the existing `E42 Identifier` resources | `HistoricalItem.cataloguenumber` | Not yet started. Already correctly wrapped in a proper Identifier resource (`P1_is_identified_by`) via the `CatalogueNumber_<id>` pattern — this only changes the literal's own predicate, not the surrounding structure |
| `dcterms:identifier` | `Date.legacy_reference`, `HistoricalItem.legacy_reference`, `Scribe.legacy_reference`, `Hand.ker`, `Hand.scragg` | Not yet started. These are genuine alternate reference-numbering schemes (Ker's catalogue, Scragg's numbering, older/legacy shelfmarks) — same conceptual shape as `cataloguenumber`, same treatment |

---

## 3. Corrections made during triage (worth recording, since they reversed an initial read)

- **`Image.caption` — moved from a Bucket 1 candidate to Bucket 2.** Initially considered for `dcterms:description`. Checked against the Django model directly: the field carries its own comment, *"no longer used, to be removed"* — explicitly deprecated by the DigiPal developers, not just low-value. Confirmed by the project lead: it's auto-generated from the image filename, used only to give a human-readable label in the admin interface. No mapping; stays exactly as it is, `EX.caption`, Bucket 2.
- **`Annotation.holes` — moved from an assumed Bucket 4 candidate ("holes in the parchment," a codicological fact) to Bucket 2.** Checked against the model: the field is annotation-rendering data (*"the holes to draw on the image thumbnail on the frontend"*), not a fact about the physical manuscript. Confirmed by the project lead: used to exclude a region from within an annotation shape — e.g. excluding a decorative border from the annotated text region. Interface/rendering plumbing, not domain data.

Both corrections came from checking the Django model directly rather than guessing from the field name alone — the same discipline used throughout the other two reports.

---

## 4. Two small items outside the bucket system

- **`name`, `style`, `text`** appear as separate `EX:` properties in a few places, but in most of those same places the value is *also* copied straight into `rdfs:label`. These should probably just **be** `rdfs:label`, dropping the redundant `EX:` duplicate — a cleanup, not a vocabulary question. Not yet actioned.
- **`summary`** — already confirmed dead in `domain_range_compliance_v3.md` §2.11 (never populated in practice, on the `Description` table). Worth dropping from any future formalization pass rather than mapping it to anything. Not yet actioned.

---

## 5. Bucket 3 — Genuine relationships / bigger modelling opportunities (not yet actioned, needs judgement)

- **`shelfmark`** (`Current_Item`) — a genuine identifier (a library shelfmark functions exactly like a catalogue number), a strong candidate to become a real `P1_is_identified_by`/`E42 Identifier` link, the same treatment `cataloguenumber` already has, rather than staying a bare literal.
- **`locus`/`selected_locus`** (`Image`, `Hand`) — "where within the item" (e.g. "fol. 3r") is a genuine CIDOC-CRM concept (`E46 Section Definition`/`P59 has section`), not just descriptive text.
- **`transcription`** (`Image`) — given the CRMtex apparatus already built out in this project (`TX1`/`TX2`/`TX7`...), this arguably belongs in that structure (`TX6 Transliteration`) rather than as a flat literal.
- **`url`** (`Reference`, `Text`, `Repository`, `Source`, `CatalogueNumber`) — currently a string literal; more properly an actual `URIRef` resource linked via `dcterms:source`/`rdfs:seeAlso`, not a datatype property at all.
- **The `dubitable` pattern** — recurs across every `E13 Attribute Assignment` node built in this project (`Archive`, `ItemOrigin`, `HistoricalItemDate`, `HandDate`/`HandPlace`). No clean existing CRM predicate for "this assertion is doubted" as a simple boolean. Worth documenting and diagramming **once**, as a named pattern, rather than per-occurrence — and worth checking whether CRMinf (the CIDOC-CRM Argumentation extension) has something better suited before settling for custom.

---

## 6. Future work

- Complete the remaining Bucket 1 swaps (§2).
- `name`/`style`/`text` → `rdfs:label` cleanup, and `summary` removal (§4).
- Work through the Bucket 3 items with the project lead (§5) — each is a real design decision, not a mechanical fix.
- Once Buckets 1–3 are settled, formalize Bucket 4 (~50 properties) with `owl:DatatypeProperty` + `rdfs:domain`/`rdfs:range` declarations as part of building the standalone OWL file.
- Revisit whether any Bucket 2 properties (interface plumbing) should be dropped from the export entirely, separate from the vocabulary question — not addressed in this pass.
