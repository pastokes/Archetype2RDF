# Datatype Properties — Full Batch Review (Phase 2, Step 8)

Companion to `ex_properties_alignment_v1.1.md` and `OWL_Formalisation_Log.md`. Covers the remaining ~80 custom `archetype:` properties still live in `creation_rdf.py` (v7) that haven't yet been individually resolved (`name`/`style`/`text`, `vernacular` and `HistoricalItemDate` already settled — see the log).

**Method:** rather than reading each property off the code alone, every property below was checked empirically against the RDF export — actual domain (subject `rdf:type`), actual range (literal datatype), and sample/distribution of real values. Originally run against v7 (`data_pstokes_turtle_202609211051.rdf`, 1,080,127 triples); §1's findings have since been resolved and implemented across v8 and v9 (`data_pstokes_turtle_202609211831.rdf`, 1,017,702 triples), each verified against the export as usual.

---

## 1. New issues found — resolved (2026-09-21)

| Property | Domain | Finding | Resolution |
|---|---|---|---|
| `Item_Part.pagination` | `Item_Part` | Boolean (1,635 `false` / 40 `true`), not pagination-scheme text. | **Resolved.** Confirmed genuine domain fact: `true` = numbered by pages, `false` = numbered by folios. Kept as-is (`archetype:pagination`, `xsd:boolean`, domain `Item_Part`); semantics to be spelled out in an `rdfs:comment` on the OWL declaration rather than renaming the property. |
| `HandInstance.num` | `HandInstance` | Mostly sensible small sequential numbers but with garbage outliers up to 2,146,985,176. | **Resolved.** Confirmed this is purely an interface display-numbering idiom, not a domain fact ("very similar to sort_order"). Reclassified from a candidate genuine property to **Bucket 2** (interface plumbing) — excluded from the OWL file, kept in the export as-is. The garbage outliers are no longer a concern since the property won't be formalized. This comparison to `sort_order` reopens §2's `sort_order` question — see below. |
| `Image.image` | `E36_Visual_Item` (Image) | 612/995 values were the literal string `"x"`, 249 empty, only ~130 real paths. | **Resolved — confirmed junk.** Dropped from the export and the model entirely (implemented in v8, verified: 995 triples removed, nothing else moved). |
| `Image.size` | `E36_Visual_Item` (Image) | All 995 values in DigiPal are exactly `0`, but the field is genuinely populated in Models of Authority (unlike `Image.image`, which is junk everywhere). | **Partially resolved.** Confirmed low research value (it's a file size in bytes) even where populated. Still open: whether to drop it from the export entirely (as was done for `Repository.url`, despite having some real data) or exclude it from the OWL's formal model only while leaving it in the export as raw data (Bucket 2 style). Awaiting your call. |
| `Layout.multiple_sheet_rulling` | `E18_Physical_Thing` (Layout) | Zero triples in the export — every value null. | **Resolved — confirmed dead.** Dropped from the export and the model entirely, including a second usage site in the Layout "has any content" check that I'd missed in my own review (implemented in v8, verified: 0 triples affected directly, but the second site was also corrected). |
| `Annotation.illustration_ductus` | `Annotation` | All 18 values were empty strings. | **Resolved — confirmed dead.** Dropped from the export and the model entirely (implemented in v8, verified: 18 triples removed). |
| `Annotation.display_note` vs. `HandInstance.display_note` | `Annotation` (60,910 triples) vs. `HandInstance` (517/519 triples) | Same name, very different situations, same pattern as `vernacular`: `Annotation.display_note` was 99.9% empty plus 59 literal `"undefined"` strings (a JS artifact); `HandInstance.display_note` had real scholarly content but was also ~97% empty-string noise. | **Resolved — kept, bug fixed on both.** `Annotation.display_note`: guard extended to exclude empty strings and the literal `"undefined"` (v8, verified: 60,908 triples removed, 2 genuine notes survive). `HandInstance.display_note`: guard extended to exclude empty strings (v9, verified: 501 triples removed, 18 genuine notes survive across both domains, 0 left empty). Kept as a genuine property, domain `Annotation` and `HandInstance` (two legitimately distinct usages, same as `vernacular`'s resolution — not one property needing a single domain). |

---

## 2. Properties with more than one domain (beyond the already-resolved `vernacular`)

| Property | Domains | Notes |
|---|---|---|
| `sort_order` | `E55_Type` (278), `E4_Period` (155, i.e. `Date`), `Ontograph` (37), `Appearance` (37) | **Resolved — moved to Bucket 2.** Confirmed interface plumbing, not a core-model fact: sort order is always specific to a given controlled vocabulary, so it belongs with that vocabulary (the planned future SKOS layer) rather than in the Archetype core OWL model — a substantive reason, not just "same idiom as `num`." Excluded from the OWL file; kept in the export as-is. |
| `display_note` | `Annotation`, `HandInstance` | **Resolved** — see §1. Kept as a genuine property with two legitimately distinct domain usages, same resolution shape as `vernacular`. |

---

## 3. Everything else — proposed classification

For the remaining properties, empirical domain + range were used to write a first-pass `owl:DatatypeProperty` declaration. Grouped by proposed treatment; **flag anything you'd move between groups**.

### 3a. Genuine domain facts — propose declaring as-is

| Property | Domain | Range |
|---|---|---|
| `eastings`, `northings` | `E53_Place` | `xsd:integer` |
| `lines`, `columns` | `E18_Physical_Thing` (Layout) | `xsd:integer` |
| `bilinear_ruling`, `insular_pricking` | `E18_Physical_Thing` (Layout) | `xsd:boolean` |
| `leaves`, `front_flyleaves`, `back_flyleaves` | `E18_Physical_Thing` (Collation) | `xsd:integer` |
| `fragment` | `E18_Physical_Thing` (Collation) | `xsd:boolean` |
| `illustrated`, `decorated`, `illuminated` | `E18_Physical_Thing` (Decoration) | `xsd:boolean` |
| `num_colours`, `num_inks` | `E18_Physical_Thing` (Decoration) | `xsd:integer` |
| `colours`, `inks`, `style` | `E18_Physical_Thing` (Decoration) | `xsd:string` |
| `catalogue_references` | `E18_Physical_Thing` (Decoration) | `xsd:string` — flagged for future proper structuring, kept as-is for now per earlier decision |
| `weight` | `E4_Period` | `xsd:decimal` (genuinely fractional — midpoint dates like 887.5; confirmed not a float-typo bug) |
| `min_weight`, `max_weight` | `E52_Time-Span` | `xsd:decimal` — checked pairwise, always `min ≤ max` across all 157 records, confirmed correct |
| `post_conquest`, `s_xi` | `E4_Period` | `xsd:boolean` |
| `band`, `additional_band` | `E4_Period` | `xsd:integer` |
| `neumed` | `Historical_Item` | `xsd:boolean` |
| `annotated`, `rebound` | `E13_Attribute_Assignment` (Owner) | `xsd:boolean` |
| `gloss_only`, `latin_only`, `relevant`, `imitative`, `membra_disjecta`, `scribble_only` | `HandInstance` | `xsd:boolean` |
| `num_glosses`, `num_glossing_hands` | `HandInstance` | `xsd:integer` |
| `ker`, `scragg` | `HandInstance` | `xsd:string` — candidates for `dcterms:identifier` per `ex_properties_alignment_v1.1.md` (not yet actioned); kept as `archetype:` datatype properties for now, migrate later if that mapping goes ahead |
| `em_title` | `HandInstance` | `xsd:string` |
| `pagination` | `Item_Part` | `xsd:boolean` — resolved (§1): `true` = paginated (by page), `false` = foliated; needs an `rdfs:comment` spelling this out, since the name alone doesn't make the boolean's meaning clear |
| `display_note` | `Annotation`, `HandInstance` | `xsd:string` — resolved (§1/§2): two distinct legitimate usages, both genuine now that both are bug-fixed (18 total real notes) |
| `unicode_point` | `Character` | `xsd:string` (mixed content — hex codepoints and literal characters both appear; string is the honest type) |
| `text` | `Appearance` | `xsd:string` (already resolved, keep) |
| `nesting_level` | `Ontograph` | `xsd:integer` |
| `comma`, `british_isles` | `E74_Group` (Repository) | `xsd:boolean` |
| `name`, `priority`, `label_slug`, `label_styled` | `E31_Document` (Source) | `xsd:string`/`xsd:integer` (`name`, `label_slug`, `label_styled` → string; `priority` → integer) |
| `folio_side` | `E36_Visual_Item` (Image) | `xsd:string` |
| `width`, `height` | `E36_Visual_Item` (Image) | `xsd:integer` — technical image metadata rather than codicological fact, but genuinely populated and potentially useful for IIIF; propose keeping |

### 3b. Proposed as interface/application plumbing — exclude from the OWL file (Bucket 2, per `ex_properties_alignment_v1.1.md`'s existing convention)

| Property | Domain | Why |
|---|---|---|
| `caption` | Image | Already confirmed "no longer used" in the Django model (earlier report) |
| `custom_label`, `iipimage`, `quire`, `page_boundaries` | Image | IIP-image-server technical references / UI labelling, not codicological facts |
| `cutout`, `geo_json`, `rotation`, `vector_id` | Annotation | OpenLayers/front-end shape-drawing metadata (image crop URLs, GeoJSON polygon coordinates, OpenLayers internal vector IDs) |
| `display_message`, `permission` | `E30_Right` (MediaPermission) | Already resolved in `ex_properties_alignment_v1.1.md` — the human-readable form is on `rdfs:label`; these are UI text / an internal numeric code |
| `num` | HandInstance | **Resolved (§1):** confirmed pure interface display-numbering, not a domain fact. Excluded from the OWL file; stays in the export unchanged. Prompted the (now also resolved) `sort_order` question in §2. |
| `sort_order` | `E55_Type`, `E4_Period`, `Ontograph`, `Appearance` | **Resolved (§2):** vocabulary-specific ordering, belongs with the future SKOS layer rather than the core OWL model. Excluded; stays in the export unchanged. |

### 3c. Confirmed dead, dropped from export and model entirely

`Image.image`, `Layout.multiple_sheet_rulling`, `Annotation.illustration_ductus` (implemented in v8) and `Repository.digital_project` (confirmed hopelessly out of date — pre-2010 data — and not used by other Archetype-based projects; implemented in v11, 217 triples removed, nothing else moved) — all resolved and verified against the regenerated RDF export.

`Allograph.hidden`, `Allograph.illustration` — confirmed unused, meaning unclear. `Allograph.default` — also confirmed unused, and additionally judged **vocabulary-specific** (which allograph counts as "default" depends on the vocabulary in use, not a fact of the Archetype core model) — if ever reinstated, it belongs in the vocabulary layer, not here. All three: dropped from export and model — implemented in v12, verified (247 triples removed: 121 `default`, 121 `hidden`, 5 `illustration`; nothing else moved).

`HandInstance.surrogates` — confirmed always empty (100% of 1,478 values), and confirmed via `models.py` directly to be a dead field inherited from the pre-Django "StewartDB" legacy database, never used in practice. Dropped from export and model — implemented in v13, verified (1,478 triples removed, nothing else moved).

`summary` (Description) and `full_reference` (Reference — deferred pending the Reference/Source question) remain excluded as before, unchanged from `ex_properties_alignment_v1.1.md`.

**`Image.size` — resolved.** Zero values (the entire DigiPal population) are now excluded at export via an `!= 0` guard, implemented and verified in v10 (995 triples removed, nothing else moved). Kept as a genuine property — domain `E36_Visual_Item`, range `xsd:integer` — since it's genuinely populated in Models of Authority.

---

## 4. Not covered here

- `has_evidence_note` — already declared (`rdfs:subPropertyOf crm:P3_has_note`), a datatype property (range is a literal), included in the deferred batch per the original scope note in `archetype_ontology_0.1.ttl`'s header. Domains: `E13_Attribute_Assignment` (Owner, Date) and `E31_Document` (Date's evidence-document pattern) — two domains, but this is the established, deliberate evidentiary-note pattern (§6 of `ex_properties_alignment_v1.1.md`), not a new issue.
- `sort_order`, `display_note`, `vernacular` — see §2 above / already resolved.
- `characterised_by` — already declared as the one object property.

---

**All items in this report are resolved and verified.** The full batch is ready to be written into `archetype_ontology_0.1.ttl`.
