# DigiPal/CIDOC-CRM RDF Spot-Check Report

RDF source file: `data_rdf_digipal_cidoc_202609041816.rdf` (1,033,982 triples)

This report has two sections:
1. **Direct errors or omissions in the RDF** — things that are simply wrong or missing given the data as it stands.
2. **Notes for the future OWL ontology** — things implied by usage patterns in the RDF but not yet formally declared (domain/range, cardinality, class hierarchy, etc.), or open design questions to resolve with Peter.

---

## 1. Errors / omissions in the RDF

### 1.1 `Hand_1358` has empty `rdfs:label`, `ex:display_label`, and `ex:ker`
Unlike its sibling Hands (e.g. `Hand_57`, `Hand_67`, `Hand_68` — all attached to the same manuscripts group), `Hand_1358` (num=3, on Item_Part_203 "BL Stowe Ch. 38") carries three empty-string/blank fields where comparable Hands have populated values. Flagged for checking against the source DB — status: **noted, not yet confirmed as bug** (Stowe Ch. 38 multi-hand structure itself was confirmed fine by Peter).

### 1.2 `ex:relevant` field should not be exported at all
Peter has confirmed that `digipal:relevant` is not a field that belongs in this RDF export. It currently appears on 1,458 of 1,478 `Hand` individuals (all Hand instances except 20).
- **Action required:** remove all `ex:relevant` triples from `creation_rdf_pas.py` (Hand block).
- **Status:** confirmed by Peter, pending implementation. Per working protocol, will be proposed as a single one-line diff and verified against regenerated RDF before moving on.

### 1.3 `Hand.num` contains implausible large values
Distribution of `num` across all 1,478 Hands:

| Range | Count |
|---|---|
| 1–10 | 700 |
| 11–20 | 5 |
| 21–100 | 4 |
| 101–1,000 | 2 |
| 1,001–100,000 | 1 |
| >100,000 | 766 |

- The "large" values (766 of them) all fall strictly between 10^8 and 2^31−1 (2,147,483,647) — i.e. within the range of a signed 32-bit integer, with **none exceeding it**. This is a purely structural observation from the data (basic arithmetic on the retrieved values), not an inference about DigiPal internals.
- There is a near-total gap between ~1,000 and ~10^8 — the values are effectively bimodal: a normal small-ordinal group (1–~20) and a separate large-value group clustered just under the 32-bit signed integer ceiling.
- Peter has confirmed this is unexpected/implausible and will check against the source database.
- **Status:** logged, under investigation by Peter. Not yet altering the export — awaiting his diagnosis of the SQL-side cause before proposing a fix.
- **Full list of affected Hands (num > 1,000, n=767) for DB cross-checking:** see Appendix A below. These 767 Hands span 460 distinct Item_Parts/manuscripts — i.e. this is not localized to one document or one scribe, it's spread broadly across the dataset.

### 1.4 Idiograph identity invariant violated: 63 Idiographs linked to more than one Scribe
Initial lead: while spot-checking Scribe_9 ("Ker, Scribe K"), found that `Idiograph_13305` is shared between two of Scribe_9's own Hands (`Hand_405` and `Hand_624`, on different manuscripts). Per Peter, this alone is **not** an error: an Idiograph represents "the habitual way in which a Scribe normally writes an Allograph," so it may legitimately be shared across several Hands of the *same* Scribe. `Idiograph_13305` is a correct instance of this and is not logged as a problem.

However, Peter's stated invariant is that **one Idiograph should never be linked to more than one Scribe.** Checked this globally by tracing `Graph -[P65_shows_visual_item]-> Idiograph`, then `Graph`'s owning `Hand -[via Writing's P108_has_produced/P14_carried_out_by]-> Scribe`, grouped by Idiograph:

- **63 Idiographs (of 3,502 distinct Idiographs in the data) violate this invariant**, linked to between 2 and 9 distinct Scribes each.
- The violating Idiographs mostly carry **plain, generic labels** (e.g. "n", "e", "t", "o", "c", "b") rather than scribe-scoped labels (contrast with correctly-scoped Idiographs like `Idiograph_13305`, labeled "æ, Insular. Ker, Scribe K. saec. xi med."). This suggests two different Idiograph-creation patterns in the source data: properly scribe-scoped ones, and a separate generic/unscoped group that has ended up cross-linked between scribes.
- All 63 violations resolve to only **11 distinct Scribes** in total, recombined across different letters: `Scribe_9` (Ker, Scribe K), `Scribe_13` (Ker, Scribe O), `Scribe_124`, `Scribe_146` (DigiPal Scribe 36), `Scribe_166`/`167`/`168` (DigiPal Scribe 56/57/58), `Scribe_567` (Nero-Middleton Scribe), `Scribe_574`/`575`/`576` (G.366 Scribe 2/3, G.366B Scribe 1). This strongly suggests one systemic linkage issue affecting this specific cluster of Hands/Scribes, rather than 63 independent errors.
- **Full list in Appendix B.**
- **Status:** confirmed real invariant violation (distinguished from the `Idiograph_13305` false-alarm above, which is correct same-Scribe sharing). Pending Peter's DB-side investigation.

### 1.5 Likely missing export: pre-Graph-era Component/Feature data on orphaned Idiographs
Of 9,657 total Idiographs, 6,095 (63.1%) have no Graph referencing them at all (`P65_shows_visual_item`). All are well-formed (valid `P138_represents` link to an Allograph; ~98.7% carry proper scribe-scoped labels), so they are not corrupt records.

Checked whether any of these orphaned Idiographs carry Component/Feature data directly (rather than via a Graph): **across the entire dataset, `Idiograph` as a subject only ever uses three predicates — `rdf:type`, `P138_represents`, `rdfs:label`.** There is no `Idiograph → Component` or `Idiograph → Feature` path anywhere in the current export's schema; that data only ever flows through `Graph → GraphComponent → Component`/`Feature`.

Per Peter: some Idiographs were created at an earlier, pre-Graph stage of the DigiPal project and later imported — meaning it's plausible that Component/Feature data for these still exists in the source database, attached at the Idiograph level rather than via a Graph, from before the Graph concept existed. If so, the RDF export (`creation_rdf_pas.py`) — which by inspection only ever builds `GraphComponent` triples by iterating over `Graph` rows — would systematically miss this data, regardless of how many Graphs exist for that Idiograph. This cannot be confirmed or ruled out from the RDF alone, since (per Peter) this is very likely genuine missing export data rather than genuinely empty scaffolding.

- **Status: open question — to check against the source DB** (specifically: whether pre-Graph-era Component/Feature data exists at the Idiograph level, outside the Graph pathway, that the current export logic does not capture).
- **Corroborating case (2026-09-05 session):** the query "percentage of Graphs with Ascender having Feature 'short', for Hands with ACCEPTED Place containing 'Bath'" returned an empty denominator — no Graph in the RDF represents Component 'ascender' at all for any Bath-attributed Hand. Peter confirms he knows specific real cases of ascender data for Bath hands, and for glossing hands generally, that must be recorded at the Idiograph level and are simply not surfacing via the Graph pathway in this export. This is independent confirmation (from domain knowledge, not just structural inference) that real Component/Feature data is missing from the export for reasons connected to this issue.
- **Proposed fix (pending DB confirmation):** once the source DB check confirms Idiograph-level Component/Feature data exists outside the Graph pathway, `creation_rdf_pas.py` will need a second mapping path that builds `GraphComponent`-equivalent triples directly from `Idiograph`-level Component/Feature data, rather than only ever iterating over `Graph` rows as it does now. This would need its own design decision (e.g. whether such Idiograph-level features attach via a new predicate directly on the Idiograph, or via a synthetic Graph placeholder) rather than being a one-line change.

### 1.6 `Hand_1351` and `Hand_1352` missing `rdfs:label`
While compiling the list of 139 Hands with no ACCEPTED-type Date (§ query log, undated-Hands query), found that `Hand_1351` (Item_Part "CCCC 367, pt. ii, fols. 45–52") and `Hand_1352` (Item_Part "CCCC 389") have **no `rdfs:label` at all**, on top of lacking any date. Every other Hand in the dataset has at least a generic descriptive label (e.g. "Main Hand"). Flagged for checking against the source DB.
- **Status:** to be checked.

### 1.7 Period/Scribe evidentiary-documentation chain (`P70i_is_documented_in`) is almost entirely empty
While checking Dubitable-type Attribute Assignments (HandDate/HandPlace) documented in sources mentioning "Dumville," found that the underlying documentation chain is structurally very sparse:
- Only `E4_Period` and `Scribe` (not `E53_Place`) ever carry `P70i_is_documented_in` in this dataset — so Dubitable HandPlace assignments (targeting a Place) have no path to any Document at all, only Dubitable HandDate assignments (targeting a Period) do.
- Tracing that chain, only 172 distinct Documents (`Date_Document_N` / `Reference_N`) are reachable from Periods/Scribes at all, and of those, only **7 have any non-empty content** (mostly single-letter labels like "a"/"b"/"c", plus two short evidence notes). The remaining 165 are empty placeholder nodes.
- This is separate from the `Description_N` documents attached to `Historical_Item`s (bibliography/commentary notes), which are well-populated and do contain "Dumville" citations — those just aren't reachable from the Dubitable-assignment chain.
- Peter's assessment: likely not a bug, more likely a mismatch between his recollection of the intended documentation structure and what's actually populated — but flagged as worth a review pass.
- **Status:** logged for review — not yet investigated further.

### 1.8 No "Glossed Text" type found anywhere; possible naming confusion (Peter: likely misremembered)
When asked for "Hands with type GLOSSED TEXT," searched exhaustively (case-insensitive) for any resource labeled "Glossed Text" — none exists. `Hand`'s only `P2_has_type` targets are `Appearance_*` (e.g. "Appearance Gloss (inked)", "Appearance Gloss (scratched)") and `Category_*` (various "Glosses..." labels, none named "Glossed Text"). Separately, `Hand` has a boolean `gloss_only` literal property unrelated to any typed category.
- Peter's note: probably a misremembering of the actual property/vocabulary on his part, not a data issue.
- **Status:** to check — confirm what Peter actually meant to query, and note the naming mismatch in case it recurs.

### 2.1 No typed distinction between administrative-unit Places and site-level Places
`County` individuals (e.g. `County_39` "Worcestershire", `County_40` "Yorkshire", `County_41` "Yorkshire ER") carry `rdf:type crm:E53_Place` and **no other type** — there is no `County` class, and no `P2_has_type` (or equivalent) distinguishing them from ordinary site/settlement-level Places such as `Place_24` "Worcester" or `Place_46` "York". The only way to tell them apart currently is the `County_` URI-prefix convention and the label text itself.

- This is plausibly acceptable under CIDOC-CRM, which has no native "County" class and would typically model any administrative unit as an `E53_Place`.
- However, it means any query that filters Places by label substring (e.g. "Place containing 'Worcester'") will silently also match county-level Places, with no way to exclude them except ad hoc URI/label pattern-matching.
- **Open question for Peter:** should the formal ontology introduce an explicit typed distinction for administrative-unit Places (e.g. via `P2_has_type` pointing to a new `E55_Type` such as `arch:AdministrativeUnit`, or `arch:County` vs `arch:Settlement`), so that queries can filter by granularity of place explicitly rather than by string-matching labels/URIs?
- **Status:** raised during spot-check of Worcester/York place queries (2026-09-05 session); not yet resolved.

### 2.2 Graph→Component coverage is structurally patterned by Character (informational, expected behaviour)
94.4% of all Graphs (60,455 of 64,028) have no `GraphComponent` at all — expected, per Peter, given the scale of the annotation task. Checked the remaining 5.6% for pattern:
- **Majuscule (capital) letterforms have a hard 0% coverage, and it's structural**: every uppercase-letter Allograph (A–Z, WYNN, THORN, ETH, etc.) has zero `Component`s defined in its vocabulary (`P148_has_component`) at all, so it is structurally impossible for a majuscule Graph to ever carry a `GraphComponent` — a vocabulary-scope decision (echoing the earlier "hook never valid for æ" finding), not missing data.
- **Among minuscule letters**, component-coverage ranges from 0.2% ("ligature") to 33.6% ('q'), with higher coverage clustering on letters known for diagnostically distinctive allograph variants (q, p, æ, thorn, r, f, wynn, thæt, s: 10–34%) versus more visually uniform letters (a, o, i, u, n, l, m, c, d, h, b, y, g, eth, t, 7, ".": 1–3%). Plausibly reflects differential palaeographic research focus rather than a data issue.
- **Status:** logged as an interesting, expected observation — no action needed.

### 2.3 `E52_Time-Span` dating uses custom `min_weight`/`max_weight` rather than standard CIDOC-CRM date properties
`E52_Time-Span` individuals (158 total, one per `E4_Period` via `P4_has_time-span`) currently record their date range only via two custom datatype properties, `ex:min_weight` and `ex:max_weight` (e.g. `Date_Time_Span_23`: min_weight 1000, max_weight 1030), rather than CIDOC-CRM's standard time-span boundary properties (e.g. `P82a_begin_of_the_begin` / `P82b_end_of_the_end`, or the fuzzy-boundary `P81a`/`P81b` pair).

- Peter's note: there is likely a more standards-compliant way of recording these min/max dates within CIDOC-CRM's own vocabulary, and this should be looked into as a future step.
- Related: the paired `E4_Period` individuals also carry several custom numeric properties (`weight`, `band`, `additional_band`, `sort_order`) alongside the free-text `dc:date` label (e.g. "Saec. xi2/4 or xi3/4") — worth reviewing together with the Time-Span properties as part of the same future pass, since they all appear to serve date-sorting/approximation purposes that CIDOC-CRM may already have idioms for.
- **Status:** flagged for a future step — not yet investigated in depth.

### 2.4 139 Hands have no Date at all; pattern skews heavily toward Latin-only hands; possible semi-automatic completion path
Of 1,478 Hands, 139 (9.4%) have no `HandDate` attribute-assignment whatsoever — not merely lacking an ACCEPTED-type date, but lacking *any* date, ACCEPTED or otherwise (confirmed: zero of these 139 have even a `Type_Dubitable` date). They span 102 distinct manuscripts.

- **Pattern:** the great majority of these undated Hands carry labels containing "Latin" (e.g. "Latin Hand 1," "Main Latin Hand," "Latin Additions"), suggesting DigiPal's dating effort was concentrated on the Old English/vernacular material and largely skipped purely-Latin hands. Not confirmed as intentional scope vs. a gap — noted as an observation.
- **Future step (Peter's suggestion):** check how many of these 139 undated Hands are nonetheless associated with a dated `Historical_Item` (via the manuscript/Item_Part chain), or share an Item_Part with other Hands that *do* have a Date — either of which could provide a basis for semi-automatically inferring/completing a date range for the currently-undated Hand.
### 2.5 Repository → external authority linkage: VIAF is a feasible join key to Biblissima+ (and other LOD targets); Repository granularity (institution vs. library) needs normalizing first
While spot-checking the 14 Cambridge `Repository` individuals (via the Worcester/York place query earlier), tested whether DigiPal Repositories could be mechanically linked to external authority identifiers for LOD interoperability (a stated Biblissima+ project goal).

- **VIAF is highly feasible.** All 14 Cambridge institutions were matched to a VIAF cluster ID via a single web search each (search → land on the institution's Wikidata page → read the `VIAF cluster ID` statement). Coverage was complete and disambiguation was reliable (Wikidata separates same-named Cambridge/Oxford institutions as distinct items).
- **Biblissima+ authority IDs are not currently feasible to obtain directly** (no public SPARQL endpoint at time of testing), but this is expected to become straightforward once endpoint access is available: Biblissima's own institution entities already carry VIAF/ISNI/GND identifiers alongside their Biblissima ID, so **VIAF can serve as the join key** — querying the Biblissima+ endpoint by VIAF cluster ID once access is granted should resolve automatically, without needing Biblissima-specific search/disambiguation.
- **One normalization issue to resolve first:** DigiPal's `Repository` entities are modelled at the *institution* (college) granularity, but external catalogues/authorities sometimes cite the *library* specifically as the holding body (e.g. Biblissima's manuscript records cite "Corpus Christi College, Parker Library," a separate authority entity in Biblissima's system from "Corpus Christi College" itself, with its own distinct VIAF/Biblissima IDs). This is a one-time decision — whether `Repository` should point to the institution-level or library-level external ID where both exist — rather than a per-record problem, but needs deciding before automated linkage is run at scale.
- **Status:** methodology validated (VIAF path), pending (a) Biblissima+ endpoint access, and (b) the institution-vs-library normalization decision above.

### 2.6 Manuscript-level (Current_Item) shelfmark linkage to Biblissima+: mechanism works, but coverage is uneven and likely biased against DigiPal's core material
Tested whether individual `Current_Item` shelfmarks (not just Repositories) could be linked to Biblissima+ manuscript-level entities, using the 54 Current Items with `P50_has_current_keeper = Repository_41` (Trinity College) as a sample.

- **Where a Biblissima record exists, the match is clean and direct.** `Current_Item_1426` ("TCC R.17.1") matched `data.biblissima.fr/entity/Q134928` on the first search, with Biblissima's own "other attested titles" field listing the exact DigiPal shelfmark string as a variant. No disambiguation problem like the earlier Repository-level Jesus College case.
- **But coverage is uneven, and the gaps are not random.** `Current_Item_402` ("TCC B.10.4 (215)") — one of DigiPal's actual Anglo-Saxon manuscripts (cited via Dumville, Bishop, Keynes) — returned no Biblissima record at all despite trying several shelfmark variants. Looking at the pattern across all Trinity College hits found during this and the earlier Repository test, Biblissima's non-BnF holdings cluster heavily around manuscripts with **French-language content**, cross-referenced via *Jonas* (a database specifically of medieval French texts) and *Bibale* — rather than uniform shelfmark-by-shelfmark coverage of each institution's full collection.
- **Implication:** DigiPal's core material (Anglo-Saxon/Latin hands) sits outside Biblissima's apparent strongest-coverage zone, so a full automated shelfmark-matching pass would likely resolve a real but partial fraction of Current_Items, with the unresolved remainder skewing toward exactly the material DigiPal is most focused on. This can be measured precisely and cheaply once real endpoint access is available (a single batch shelfmark query would give the true hit rate, rather than the one-by-one web-search sampling used here).
- Peter's plan: if Biblissima+ is not able to match many DigiPal shelfmarks against existing entities, they may be willing to ingest DigiPal data and mint new Biblissima identifiers for currently-unrepresented manuscripts — to be confirmed directly with the Biblissima+ team.
- **Status:** mechanism validated; coverage rate unknown pending endpoint access — flagged as a real risk rather than assumed to be complete.

**Addendum — British Library Cotton collection (wider format range):** Repeated the test on 158 `Current_Item`s held at the British Library with "Cotton" shelfmarks (`Repository_104`), spanning both bound codices and single-sheet charters (the `Cotton Augustus ii.*` series).
- **Codices: partial coverage confirmed**, consistent with the Trinity finding — several Cotton Nero volumes matched directly (`Cotton MS Nero A II` → `Q203047`; `Nero A VII` → `Q203001`; `Nero C IV` → `Q272305`; `Nero C V` → `Q2302`; `Nero C VII` → `Q202862`; `Nero E V` → `Q149074`; `Tiberius B VIII` → `Q149076`). However `Cotton Nero A.i` itself — the actual DigiPal item (Wulfstan's manuscript) — found no match (only "Nero A.II" and "Nero A.x" did).
- **Charters: no coverage found at all.** Tested several `Cotton Augustus ii.*` single-sheet charters (ii.39, ii.40, ii.41, ii.69, etc.) — well documented in the British Library's own archives catalogue and DigiPal's own site, but none produced a Biblissima hit.
- **Sharper implication:** the coverage gap isn't just uneven by manuscript content — it appears to track genre. Biblissima's non-BnF aggregation (via Jonas/Bibale/IIIF book-digitization partners) looks oriented toward bound codices, with single-sheet charters (a documentary/diplomatic genre) essentially unrepresented. Since a substantial share of DigiPal's holdings are charters (Cotton Augustus ii, Stowe Ch., BL Additional Ch., etc.), this component of the collection is unlikely to resolve via shelfmark-matching regardless of endpoint access, and would depend on Peter's "mint new identifiers" fallback.

### 2.7 `scragg` and `ker` Hand literals should be remodelled as catalogue-number identifiers, matching the Historical_Item pattern
`Hand` currently carries `scragg` (Donald Scragg's numbering for Old English homiletic/vernacular texts — confirmed by Peter; 41 Hands have a value, e.g. "487", "78a") and `ker` (N.R. Ker's catalogue numbering) as bare datatype-property literals directly on the Hand resource.

This is inconsistent with how `Historical_Item` already models catalogue numbers: `Historical_Item —P1_is_identified_by→ CatalogueNumber_N (a E42_Identifier, rdf:value = "G. 700.2")` — a proper identifier node per catalogue reference, rather than a flat literal property named after the cataloguer.

- **Future work:** remodel `scragg` and `ker` on `Hand` using the same `P1_is_identified_by → E42_Identifier` structure already used for `Historical_Item`'s catalogue numbers, for consistency across the ontology. This would also make it straightforward to add a `P2_has_type` on each identifier distinguishing "Scragg number" from "Ker number" (and any other cataloguer-specific numbering later added), the way multiple catalogue systems are presumably already distinguished for Historical_Item's `CatalogueNumber_*` nodes.
- **Status:** logged as future ontology work — not yet implemented.

## Open questions for Peter

1. **Place typing (§2.1):** Should administrative-unit Places (Counties) get an explicit `P2_has_type` distinguishing them from site-level Places, to support granularity-aware queries without relying on label/URI pattern-matching?
2. **Pre-Graph-era Idiograph data (§1.5):** Does the source database hold Component/Feature data attached directly to Idiographs from before the Graph concept existed, which the current `creation_rdf_pas.py` export logic (routes Component/Feature only via Graph → GraphComponent) would be silently missing? If confirmed, this is data missing from the export, not empty scaffolding, and the export script would need a new mapping path for it.
3. **Missing labels on `Hand_1351`/`Hand_1352` (§1.6):** Why do these two Hands alone lack any `rdfs:label`, unlike every other Hand in the dataset?
4. **Semi-automatic dating of undated Hands (§2.4):** Of the 139 wholly-undated Hands, how many could have a date inferred from a dated `Historical_Item` on the same manuscript, or from other dated Hands sharing the same Item_Part? Worth a dedicated future pass.
5. **Sparse Period/Scribe documentation chain (§1.7):** Review why only 7 of 172 `Date_Document`/`Reference` nodes reachable via `P70i_is_documented_in` have any content — is evidentiary documentation for Dubitable dates/scribe-attributions expected to live elsewhere (e.g. the `Description_N` bibliography notes on Historical_Items), or is this a genuine gap?

---

## Working notes: efficiency suggestions and triple-store options for future sessions

Logged at the end of the 2026-09-05 session, for reference when resuming work on an updated RDF export in a new session.

### Why queries feel heavy, and how to reduce it
The 1.03M-triple dataset itself is small for a triple store — the overhead has been mostly on Claude's side, not the data:
1. **Store reload per query.** Each query runs in a fresh `bash_tool` call, which restarts Python and reloads the on-disk Oxigraph store before running anything — fixed overhead on every query regardless of complexity.
2. **Label→URI resolution sub-queries.** Most queries start with "which URI is Component labeled 'X'?" as a separate lookup before the real query can be written.
3. **Exploratory follow-up queries.** When a result looks unexpected, Claude tends to run 2–3 diagnostic queries to understand why before answering — good for accuracy, but multiplies store-loads per question.
4. One genuine query-planning cost was hit once (a `GROUP BY` with several `OPTIONAL`s and a label join timed out); a plainer query pattern resolved it instantly — not a data-scale issue.

**What would help most:**
- **Giving exact IDs when already known** (e.g. "Component_4" instead of "ascender") skips the resolution step — probably the single biggest lever available.
- **Batching related questions in one message** lets multiple lookups run in one Python invocation instead of one store-reload per sub-question.
- A **local vocabulary lookup cache** (Component/Feature/Character/Type labels ↔ URIs, built once per session) would remove the repeated resolution queries — not yet built this session, but straightforward to add at the start of a new one if useful.

### Options for a persistent, user-controlled triple store
If Peter wants to run his own store and have Claude write SPARQL against it (rather than Claude holding the store in its own sandbox each session):
- **Oxigraph** — what this session used (Rust, embeddable via `pyoxigraph` or a standalone server binary). No external dependencies; trivially handles this dataset size. Lowest-friction if comfortable with a single binary or light Python.
- **Apache Jena Fuseki** — the standard choice in the digital-humanities/CIDOC-CRM world. Java-based, self-contained server with a web UI and SPARQL endpoint out of the box; heavier than Oxigraph (JVM startup, more memory) but mature and well-documented.
- **QLever** (University of Freiburg) — notable because **this is what Biblissima+ itself switched to in April 2026** for its own backend (per Biblissima+'s SPARQL documentation). Built for scale and speed, with a usable web UI. Slightly more setup than Oxigraph.
- **RDF4J** (Eclipse Foundation) — another Java option, similar weight to Fuseki.

All four would load and query this dataset instantly; the deciding factor is tooling comfort (web UI vs. command line vs. embeddable-in-script) rather than performance. If Peter runs a local store with an exposed SPARQL HTTP endpoint, Claude could in principle query it directly in a future session (rather than losing interactivity entirely), if that's set up as a connected tool.

---

## Appendix A: Hands with num > 1,000 (n=767)

| Hand | num | Hand label | Item Part | Manuscript label |
|---|---|---|---|---|
| Hand_1489 | 5675 | "Main Hand" | Item_Part_826 | "BL Additional 47967" |
| Hand_872 | 106336884 | "OE Glosses ('several scribes')" | Item_Part_1079 | "BL Royal 7.D.xxiv, fols. 82–168" |
| Hand_1053 | 107062032 | "Main Hand (all except 2v, 12r–16v, 25r–33v, 34r1–4)" | Item_Part_1299 | "Bodleian Junius 85 and 86 (5196–7)" |
| Hand_1287 | 110438337 | "Main Hand" | Item_Part_1837 | "BL Harley 55, fols. 5–13" |
| Hand_143 | 111591549 | "Main Hand" | Item_Part_273 | "BL Campbell Ch. vii.1a" |
| Hand_672 | 112574900 | "Addition 2: Part of Papal Bull (fols. 69r5–69v)" | Item_Part_913 | "BL Cotton Otho C.i, vol. i" |
| Hand_1108 | 114904855 | "Interlinear Glosses" | Item_Part_1388 | "Salisbury 38" |
| Hand_1105 | 119698640 | "Addition (221v15–222)" | Item_Part_1366 | "JCO 154" |
| Hand_454 | 121024469 | "Latin Glosses" | Item_Part_620 | "JCC 59 (C.9)" |
| Hand_318 | 127488806 | "Latin Hand 2" | Item_Part_510 | "CCCC 163" |
| Hand_224 | 130454591 | "Main Hand" | Item_Part_402 | "BL Additional Ch. 19790" |
| Hand_1018 | 138982702 | "Latin Gloss" | Item_Part_1267 | "Bodleian Digby 174 (1775), fol. iii" |
| Hand_911 | 139576334 | "Scribble (Ða æfter æadgares cininges forðsiðe on ðam gewalce, 129v)" | Item_Part_1138 | "Lambeth 204" |
| Hand_948 | 143496315 | "OE Glossator (7v, 8v, 9r)" | Item_Part_1176 | "Bodleian Auctarium F.1.15 (2455), fols. 1–77" |
| Hand_535 | 152938536 | "Manumission Hand 1 (ca. fol. 8; Förster no. XXX and XXXIII)" | Item_Part_798 | "BL Additional 9381" |
| Hand_1074 | 154116845 | "Main Latin Hand (1v, 6v–44v22)" | Item_Part_1327 | "Bodleian Rawlinson C.570 (12415)" |
| Hand_894 | 154798834 | "Latin Hand" | Item_Part_1122 | "BL Stowe 2" |
| Hand_844 | 155273432 | "Latin Hand 2 (11rv)" | Item_Part_1060 | "BL Royal 5.E.xi" |
| Hand_826 | 157327164 | "Interlinear OE Glosses, etc." | Item_Part_1041 | "BL Royal 2.A.xx" |
| Hand_442 | 157414386 | "Latin Hand 1 (1r–32v)" | Item_Part_600 | "Pembroke 41" |
| Hand_106 | 160225691 | "Main Hand" | Item_Part_239 | "Exeter 2521, dorse" |
| Hand_511 | 160616229 | "Inscription (of searbyrig ic eom, i recto)" | Item_Part_702 | "TCD 174 (B.4.3), fols. 1–44, 52–6 and 95–103" |
| Hand_774 | 161227413 | "Latin Calendar Hand" | Item_Part_978 | "BL Cotton Vitellius E.xviii" |
| Hand_745 | 162863711 | "Interlinear OE Glosses" | Item_Part_955 | "BL Cotton Vespasian D.vi, fols. 2–77" |
| Hand_246 | 164922228 | "Supply Hand 2 (21rv; 18rv)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_1327 | 167335069 | "Degrees of Consanguinity (170v)" | Item_Part_1876 | "JCO 26" |
| Hand_1259 | 167964818 | "Additions 2 (pp. 308r7–319)" | Item_Part_1812 | "CCCC 190, pp. 295–319 and 351–364" |
| Hand_1146 | 175327200 | "OE Glosses (168r, 174v)" | Item_Part_1472 | "Arras, BM 764 (739), fols. 134–81" |
| Hand_413 | 176082442 | "Vision of Leofric (48v5–50)" | Item_Part_560 | "CCCC 367, pt. ii, fols. 45–52" |
| Hand_410 | 180721733 | "Latin Hand 1 (pp. 1–64)" | Item_Part_553 | "CCCC 326" |
| Hand_553 | 183395633 | "Scribbles (pp. iii–iv = fol. iirv)" | Item_Part_826 | "BL Additional 47967" |
| Hand_465 | 195169360 | "Latin Hand (126v/i/39–ii/11)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_1200 | 197193805 | "Seventeen OE Glosses" | Item_Part_1667 | "Schøyen 197" |
| Hand_245 | 199265414 | "Additions (incl. glosses)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_1337 | 199696959 | "Main Hand (incl. six glosses, 32r, 33r, 34v, 40v)" | Item_Part_1886 | "Bodleian Rawlinson c.641" |
| Hand_859 | 201318382 | "Latin Hand" | Item_Part_1073 | "BL Royal 6.C.i" |
| Hand_102 | 206126279 | "Main Hand" | Item_Part_235 | "Exeter 2518" |
| Hand_209 | 207040616 | "Main Hand" | Item_Part_387 | "BL Stowe Ch. 4" |
| Hand_544 | 208253671 | "Main Hand (Latin)" | Item_Part_813 | "BL Additional 34890" |
| Hand_481 | 213448891 | "Main Latin Gloss" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_741 | 215744031 | "Main Latin Hand" | Item_Part_949 | "BL Cotton Vespasian A.xiv, fols. 114–79" |
| Hand_1344 | 217105529 | "Names of letters (3v)" | Item_Part_1892 | "BL Stowe 57" |
| Hand_1061 | 217359252 | "Hand 10 (157r–160)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_1312 | 220392711 | "OE Alliterative verse (p. 202)" | Item_Part_1861 | "CUL Ff.1.27, pp. 1–40, 73–52" |
| Hand_1234 | 221624097 | "Latin Hand 3 (fols. 90–157)" | Item_Part_1732 | "BAV Reg.lat.1671" |
| Hand_328 | 222286410 | "Annotation; Signed Note (pp. 97?; 229)" | Item_Part_513 | "CCCC 178, pp. 1–270" |
| Hand_685 | 223549515 | "Main Hand (Tib. A.iii)" | Item_Part_921 | "BL Cotton Tiberius A.iii, fol. 178" |
| Hand_602 | 226889920 | "Manumission (47r)" | Item_Part_870 | "BL Cotton Domitian vii, fols. 15–45 (and added fols.)" |
| Hand_898 | 230326080 | "Relic List, Hand 3 (58v14–24)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_871 | 231422877 | "Scribe Z (additions and corrections)" | Item_Part_1078 | "BL Royal 7.C.xii, 4–218" |
| Hand_1215 | 232151831 | "Hand 2 (fol. 7)" | Item_Part_1694 | "BnF latin 8824" |
| Hand_676 | 232309468 | "Hand 4 (149–55v)" | Item_Part_914 | "BL Cotton Otho C.i, vol. ii" |
| Hand_1001 | 234371981 | "Donation Inscription (1r)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_914 | 235280872 | "OE Glosses (14r, 18r, 39v)" | Item_Part_1143 | "Lambeth 377" |
| Hand_759 | 239851540 | "Recipes, Hand 2 (82v–83)" | Item_Part_970 | "BL Cotton Vitellius C.iii, fols. 11–85" |
| Hand_93 | 241937183 | "Main Hand" | Item_Part_226 | "Canterbury Chart. Ant. E.206, Red Book, no. 13" |
| Hand_79 | 242917819 | "Main Hand" | Item_Part_212 | "Bodleian Eng. hist. a.2, no. viii a" |
| Hand_920 | 243612593 | "Hand 2 (20v–24v)" | Item_Part_1149 | "Lambeth 489" |
| Hand_1034 | 249160590 | "Running Titles" | Item_Part_1293 | "Bodleian Hatton 113 (5210)" |
| Hand_165 | 253070014 | "Endorsement Hand 3" | Item_Part_295 | "PRO 30/26/11" |
| Hand_882 | 258518394 | "Main Latin Hand 1" | Item_Part_1094 | "BL Royal 13.A.xv" |
| Hand_1303 | 260700379 | "Main hand (incl. Bede's Death-song, p. 281)" | Item_Part_1848 | "Bodleian Bodley 297 (2468)" |
| Hand_1006 | 263602267 | "Latin Additions (4r, 5r and 7v)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_204 | 264859712 | "Main Hand" | Item_Part_380 | "BL Stowe Ch. 29" |
| Hand_910 | 266169276 | "Glossator 3 (119v, 128v)" | Item_Part_1138 | "Lambeth 204" |
| Hand_1040 | 268198561 | "OE Church dedications  (246v)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_1209 | 272326967 | "Main Latin Hand" | Item_Part_1688 | "BnF latin 6401A" |
| Hand_378 | 272710911 | "Hand A: Directions for Confessor (pp. 72–83)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_572 | 273337530 | "Main Hand (Annals, etc.)" | Item_Part_851 | "BL Cotton Caligula A.xv, fols. 120–43" |
| Hand_206 | 273889535 | "Main Hand" | Item_Part_384 | "BL Stowe Ch. 32" |
| Hand_782 | 281174719 | "Hand 1 (fols. 1–7, 8–49r2)" | Item_Part_988 | "BL Harley 107" |
| Hand_508 | 285670880 | "Main Hand" | Item_Part_685 | "Canterbury Additional 20" |
| Hand_243 | 285771256 | "82 OE Glosses" | Item_Part_467 | "CUL Gg.5.35 (1567)" |
| Hand_1044 | 286084344 | "Main Hand (fols. 1–64, 66–139)" | Item_Part_1295 | "Bodleian Hatton 115 (5135), fols. 1–147" |
| Hand_269 | 290997585 | "Fourteen Glosses" | Item_Part_488 | "CUL Additional 3330" |
| Hand_855 | 291870409 | "Latin Hand(s) 1" | Item_Part_1068 | "BL Royal 6.A.vii, fols. 1 and 162v" |
| Hand_591 | 294841480 | "Hand 8 (58r12 – 58v)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_211 | 295380490 | "Main Hand" | Item_Part_389 | "Canterbury Chart. Ant. C.69, Red Book, no. 3" |
| Hand_723 | 300001173 | "OE Hand 3 (161v–62v)" | Item_Part_939 | "BL Cotton Tiberius C.i, fols. 43–203" |
| Hand_917 | 300095012 | "Alliterative Verse (183v)" | Item_Part_1145 | "Lambeth 427, fols. 1–202" |
| Hand_747 | 302519636 | "Hand 2, incl. cont. gloss (92v–157)" | Item_Part_957 | "BL Cotton Vespasian D.xii" |
| Hand_315 | 307147255 | "'Annotator'" | Item_Part_509 | "CCCC 162, pp. 1–138, 161–564" |
| Hand_1148 | 307369769 | "Records" | Item_Part_1492 | "Bern 671" |
| Hand_389 | 314063075 | "Glossator 9 (pp. 122, 136; Ker article c.ix)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_501 | 315874143 | "Latin Hand 3 (16r–23v)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_1257 | 319169351 | "Main Latin Hand" | Item_Part_1811 | "CCCC 9, pp. 61–458" |
| Hand_61 | 319691666 | "Main Hand" | Item_Part_200 | "BL Stowe Ch. 31" |
| Hand_6 | 320991107 | "Main Hand (bounds and first endorsement)" | Item_Part_6 | "BL Additional Ch. 19516" |
| Hand_1187 | 322619430 | "Main Hand" | Item_Part_1583 | "Kenneth Spencer Pryce C2 :2 (Y.104)" |
| Hand_1297 | 324085487 | "Chronicle Hand 1 (1–88v; annals to A.D. 1131)" | Item_Part_1843 | "Bodleian Laud 636" |
| Hand_1248 | 330091613 | "Hand A: Prayers to Cross, Prognostics (pp. 613–17, 713–21)" | Item_Part_1793 | "CCCC 391" |
| Hand_1090 | 331421343 | "Notice of dues (109r)" | Item_Part_1350 | "CCCO 197" |
| Hand_1059 | 332997586 | "Hand 8 (154r1–16)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_949 | 338981483 | "Donation Inscription (78r)" | Item_Part_1177 | "Bodleian Auctarium F.1.15 (2455), fols. 78–93" |
| Hand_183 | 341239228 | "Main Hand" | Item_Part_354 | "BL Stowe Ch. 33" |
| Hand_403 | 341789400 | "Latin Hand (pp. 1–74, 77–101 = fols. 119v–156r, 157v–69v)" | Item_Part_550 | "CCCC 320, fols. 117–70" |
| Hand_433 | 342275664 | "Scribble (... an letio iss. ..., 197r)" | Item_Part_574 | "CCCC 473" |
| Hand_1349 | 343698302 | "Main Hand (incl. Bede's Death-song, 176r)" | Item_Part_1896 | "TCD 492 (E.2.23)" |
| Hand_684 | 345448169 | "OE Hand" | Item_Part_920 | "BL Cotton Tiberius A.iii, fols. 174–7" |
| Hand_1172 | 346207682 | "Latin Hand(s)" | Item_Part_1534 | "Copenhagen, KB G.K.S.1595 (4º)" |
| Hand_480 | 347457670 | "Latin Hand 6 (5r19–23)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_940 | 353237005 | "Inventory of Donations (1r–2v)" | Item_Part_1173 | "Bodleian Auctarium D.2.16 (2719)" |
| Hand_755 | 353987762 | "Main Latin Hand" | Item_Part_969 | "BL Cotton Vitellius A.xix" |
| Hand_104 | 356789769 | "Main Hand" | Item_Part_237 | "Exeter 2520" |
| Hand_838 | 357619447 | "Added Charm (106v)" | Item_Part_1050 | "BL Royal 4.A.xiv, fols. 1–106" |
| Hand_479 | 364486610 | "Latin Hand 4 (30r24–30v1)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_148 | 368957219 | "Main Hand" | Item_Part_279 | "BL Cotton Augustus ii.38" |
| Hand_385 | 370864120 | "Glossator 5 (p. 60; Ker article c.v)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_1288 | 372999694 | "Main Hand" | Item_Part_1838 | "BL Royal 1.A.xiv" |
| Hand_1258 | 375447654 | "Additions 1 (pp. 295–308)" | Item_Part_1812 | "CCCC 190, pp. 295–319 and 351–364" |
| Hand_1214 | 375969624 | "Main Hand" | Item_Part_1694 | "BnF latin 8824" |
| Hand_252 | 375971851 | "Main Hand" | Item_Part_471 | "CUL Ii.2.11 (1744)" |
| Hand_1189 | 377595896 | "Main Latin Hand" | Item_Part_1585 | "Le Havre, BM 330" |
| Hand_189 | 384538415 | "Main Hand" | Item_Part_361 | "BL Cotton Augustus ii.83" |
| Hand_1037 | 385258437 | "Additions 1 (230r–35v, 242v–46v)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_944 | 385939080 | "OE Glosses" | Item_Part_1175 | "Bodleian Auctarium D.5.3 (27688)" |
| Hand_1073 | 386791037 | "Glossator (66v)" | Item_Part_1323 | "Bodleian Laud Misc.509 (942)" |
| Hand_300 | 387760834 | "B: Manumission 2 (Edric, 1r)" | Item_Part_505 | "CCCC 140" |
| Hand_533 | 394672457 | "Main Latin Hand" | Item_Part_790 | "Lincoln Cathedral 182 (C.2.8)" |
| Hand_1241 | 400511994 | "Latin Hand 1 (fols. 20–26)" | Item_Part_1742 | "Rouen, BM 1385 (U.107), fols. 20–6" |
| Hand_1155 | 401080601 | "Latin Glossator ('Additional Latin Glosses')" | Item_Part_1508 | "Boulogne BM 189" |
| Hand_1004 | 405022002 | "Manumissions, Hand 3 (377v)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_1128 | 407615867 | "OE and Latin Glosses" | Item_Part_1447 | "Worcester Q.5" |
| Hand_1032 | 408215912 | "Main Hand (fols. 1–144)" | Item_Part_1293 | "Bodleian Hatton 113 (5210)" |
| Hand_923 | 409198208 | "Hand 5 (47r–58v)" | Item_Part_1149 | "Lambeth 489" |
| Hand_1263 | 411018303 | "Calendar" | Item_Part_1815 | "TCC R.15.32 (945), pp. 13–36" |
| Hand_601 | 413301721 | "Three Earlier Glosses (31v, 34v)" | Item_Part_869 | "BL Cotton Domitian i, fols. 2–55" |
| Hand_1024 | 416933688 | "Latin Additions (mostly 47r, 189r–204r)" | Item_Part_1285 | "Bodleian Hatton 42 (4117)" |
| Hand_276 | 420743391 | "Main Hand" | Item_Part_497 | "CCCC 12" |
| Hand_284 | 422296083 | "Donation Inscription" | Item_Part_499 | "CCCC 41" |
| Hand_975 | 422552429 | "Cædmon's Hymn (152v)" | Item_Part_1201 | "Bodleian Bodley 163 (2016), fols. 1–227, 250 and 251" |
| Hand_1130 | 425231176 | "Latin Text and Some Latin Glosses" | Item_Part_1457 | "Worcester Additional 7, fols. 1–6" |
| Hand_1085 | 425486652 | "Notice of Grant (108r7–12)" | Item_Part_1350 | "CCCO 197" |
| Hand_605 | 425878395 | "Main Hand" | Item_Part_871 | "BL Cotton Domitian viii, fols. 30–70" |
| Hand_1083 | 429173411 | "Latin Notice of Dues (108v1–11)" | Item_Part_1350 | "CCCO 197" |
| Hand_42 | 441045993 | "Main Hand" | Item_Part_894 | "BL Cotton Nero E.i, vol. ii fols. 181–4" |
| Hand_682 | 442911583 | "OE Hand 3 (fols. 43–45)" | Item_Part_919 | "BL Cotton Tiberius A.iii, fols. 2–173" |
| Hand_839 | 444299749 | "OE Gloss (foremere, 107v)" | Item_Part_1051 | "BL Royal 4.A.xiv, fols. 107 and 108" |
| Hand_386 | 446101540 | "Glossator 6 (p. 61; Ker article c.vi)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_642 | 448515497 | "Latin Hand 2" | Item_Part_887 | "BL Cotton Nero A.ii, fols. 3–13" |
| Hand_580 | 453630124 | "Latin Hand(s)" | Item_Part_855 | "BL Cotton Claudius A.iii, fols. 31–86 and 106–50" |
| Hand_1177 | 455976384 | "Latin" | Item_Part_1547 | "El Escorial E.II.1" |
| Hand_247 | 459430052 | "Hand 3 (65r–72r)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_504 | 461273839 | "Latin Hand 7 (8r11–14)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_1260 | 465652273 | "Additions 3 (pp. 351–59)" | Item_Part_1812 | "CCCC 190, pp. 295–319 and 351–364" |
| Hand_512 | 466797707 | "Marginal Liturgical Directions (pp. 213–14 = 107rv)" | Item_Part_715 | "Durham Cathedral A.IV.19" |
| Hand_203 | 470216839 | "Main Hand" | Item_Part_379 | "BL Cotton Ch. viii.28" |
| Hand_126 | 470762237 | "Main Hand" | Item_Part_257 | "W.A.M. I" |
| Hand_854 | 475896788 | "Main Latin Hand" | Item_Part_1067 | "BL Royal 6.A.vi" |
| Hand_587 | 475998848 | "Hand 4 (fols. 38–55v)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_196 | 480158430 | "Main Hand" | Item_Part_368 | "BL Cotton Ch. viii.12" |
| Hand_412 | 481161364 | "Booklist (48v2–4)" | Item_Part_560 | "CCCC 367, pt. ii, fols. 45–52" |
| Hand_1335 | 481540316 | "Caedmon's Hymn (99r)" | Item_Part_1883 | "Oxford, Magdalen lat.105" |
| Hand_302 | 485666067 | "E: Manumission 4 (Gunhild, 1v)" | Item_Part_505 | "CCCC 140" |
| Hand_1119 | 488259909 | "Latin Annotations (87r, 150v, 153v, 154v)" | Item_Part_1439 | "Worcester F.48" |
| Hand_1184 | 489744525 | "Main Hand" | Item_Part_1567 | "Hannover W.M.XXIa, 36" |
| Hand_978 | 490239494 | "Main Latin Hand" | Item_Part_1201 | "Bodleian Bodley 163 (2016), fols. 1–227, 250 and 251" |
| Hand_1042 | 490715287 | "Running Titles" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_426 | 494874297 | "Hand B1 (pp. 3–93)" | Item_Part_568 | "CCCC 421, pp. 3–354" |
| Hand_1232 | 495718571 | "Latin Hand 1 (1r–2v12)" | Item_Part_1732 | "BAV Reg.lat.1671" |
| Hand_261 | 496662157 | "Caedmon's Hymn and OE Gloss (128v)" | Item_Part_482 | "CUL Kk.5.16 (2058)" |
| Hand_279 | 509086562 | "Titles, Hand 2 (Titles 45–48)" | Item_Part_498 | "CCCC 23, vol. i" |
| Hand_760 | 509261391 | "Recipes, Hand 3 (82v–83)" | Item_Part_970 | "BL Cotton Vitellius C.iii, fols. 11–85" |
| Hand_150 | 513938563 | "Added Bounds" | Item_Part_281 | "BL Stowe Ch. 34" |
| Hand_1186 | 514809243 | "Main Hand (Homily)" | Item_Part_1582 | "Kenneth Spencer Pryce C2 :1 (Y.103)" |
| Hand_686 | 518981519 | "Main Hand (incl. Tiberius A.iii, fol. 178)" | Item_Part_923 | "BL Cotton Tiberius A.vi, fols. 1–35" |
| Hand_452 | 519388607 | "Glossator" | Item_Part_612 | "Pembroke 312C, nos.1 and 2" |
| Hand_1334 | 524547996 | "Bede's Death-song (112v)" | Item_Part_1882 | "Lincoln Coll. Ox. lat.31, fols. 14–113" |
| Hand_634 | 524654699 | "Hand A (3r–42r)" | Item_Part_885 | "BL Cotton Nero A.i, fols. 3–57" |
| Hand_762 | 525778545 | "Names of Herbs" | Item_Part_970 | "BL Cotton Vitellius C.iii, fols. 11–85" |
| Hand_1326 | 526675853 | "Caedmon's Hymn (116v)" | Item_Part_1875 | "Hereford P.V.1, fols. 29–" |
| Hand_641 | 526944665 | "Latin Hand 1" | Item_Part_887 | "BL Cotton Nero A.ii, fols. 3–13" |
| Hand_543 | 532044890 | "Main Hand" | Item_Part_811 | "BL Additional 34652, fol. 3" |
| Hand_1107 | 543103297 | "OE Glossator 1" | Item_Part_1366 | "JCO 154" |
| Hand_534 | 553925840 | "Main Hand" | Item_Part_793 | "Lincoln Cathedral 298B" |
| Hand_635 | 554121037 | "Hand B (42–57)" | Item_Part_885 | "BL Cotton Nero A.i, fols. 3–57" |
| Hand_463 | 560874144 | "Latin Hand (120r–120v/i/21, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_429 | 561462041 | "pp. 330–332" | Item_Part_570 | "CCCC 422, pp. 27–570" |
| Hand_1339 | 561932676 | "Added note (95v)" | Item_Part_1887 | "Rouen, BM I.49 (524)" |
| Hand_223 | 563944058 | "Main Hand" | Item_Part_401 | "BL Stowe Ch. 9" |
| Hand_977 | 564095688 | "Glosses (66r, 111v, 112r, 154r)" | Item_Part_1201 | "Bodleian Bodley 163 (2016), fols. 1–227, 250 and 251" |
| Hand_963 | 567029098 | "Latin Hand incl. gloss (fols. 1–9)" | Item_Part_1181 | "Bodleian Auctarium F.4.32 (2176), fols. 1–9 and 19–37" |
| Hand_1071 | 568541001 | "Hand 2 (15r8–21 and 15v1–10)" | Item_Part_1323 | "Bodleian Laud Misc.509 (942)" |
| Hand_1096 | 570774858 | "Latin Gloss" | Item_Part_1355 | "Keble 22" |
| Hand_262 | 574315760 | "Note on division on 60v" | Item_Part_483 | "CUL Kk.5.32 (2074), fols. 49–60" |
| Hand_298 | 576505830 | "A: Manumission 1 (Ælfwig Scred, 1r)" | Item_Part_505 | "CCCC 140" |
| Hand_879 | 577790666 | "Hand 1 (fols. 7–8)" | Item_Part_1090 | "BL Royal 12.G.xii, fols. 2–9" |
| Hand_317 | 578393861 | "Latin Hand 1" | Item_Part_510 | "CCCC 163" |
| Hand_1314 | 582226206 | "Main hand (incl. Bede's Death-song, 108r)" | Item_Part_1863 | "Bodleian Digby 211 (1812)" |
| Hand_248 | 583829202 | "Hand 4 (72v–93v)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_1304 | 589158471 | "OE Glossaries (fols. 144–46)" | Item_Part_1849 | "Bodleian Bodley 730 (2709)" |
| Hand_573 | 589663637 | "Annalist 1 (s.a. 1085 – ???)" | Item_Part_851 | "BL Cotton Caligula A.xv, fols. 120–43" |
| Hand_586 | 590289167 | "Hand 3 (fols. 31–38)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_1124 | 590535461 | "Latin Gloss" | Item_Part_1446 | "Worcester F.173, fol. 1" |
| Hand_502 | 591253622 | "Latin Hand 4 (41r–44r)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_1235 | 593480172 | "Latin Hand 4 (fols. 158–218)" | Item_Part_1732 | "BAV Reg.lat.1671" |
| Hand_646 | 595201412 | "Glosses (24r, 27v, (188v–195v))" | Item_Part_893 | "BL Cotton Nero E.i, vol. i and vol. ii fols. 1–155" |
| Hand_1250 | 596974649 | "Hand C: Directions for Charm (pp. 617/21–27, 618)" | Item_Part_1793 | "CCCC 391" |
| Hand_1169 | 598517569 | "Main Latin Hand 1" | Item_Part_1532 | "Copenhagen, KB G.K.S.10 (2º)" |
| Hand_530 | 599290368 | "Hand C (Regula; fol. 6v)" | Item_Part_771 | "Gloucester 35, fols. 1–7" |
| Hand_140 | 599803109 | "First Line of face" | Item_Part_270 | "Canterbury Chart. Ant. C.4" |
| Hand_1086 | 604296069 | "Notice of Grants (108r14–23)" | Item_Part_1350 | "CCCO 197" |
| Hand_420 | 605000010 | "OE Glosses" | Item_Part_563 | "CCCC 389" |
| Hand_632 | 607431915 | "Hand 3 (two lines on 45v)" | Item_Part_884 | "BL Cotton Julius E.vii" |
| Hand_190 | 612074138 | "Main Hand" | Item_Part_362 | "BL Stowe Ch. 26" |
| Hand_936 | 617938392 | "Latin Hand 8 (53r–59v9)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_120 | 618412535 | "Main Hand" | Item_Part_251 | "College of Arms Waiting Room" |
| Hand_1138 | 620350218 | "Fol. 23v" | Item_Part_1461 | "York Additional 1, fols. 10–161" |
| Hand_393 | 623901363 | "Latin Glosses" | Item_Part_542 | "CCCC 279" |
| Hand_272 | 640112548 | "Glossator (pp. 23–24)" | Item_Part_496 | "CCCC 9, pp. 1–60" |
| Hand_674 | 640348428 | "Hand 2 (62–139v5)" | Item_Part_914 | "BL Cotton Otho C.i, vol. ii" |
| Hand_219 | 641331479 | "Main Hand" | Item_Part_398 | "BL Cotton Augustus ii.6" |
| Hand_1283 | 645186838 | "Main Hand" | Item_Part_1835 | "BL Cotton Vespasian D.xiv, fols. 4–169" |
| Hand_74 | 650448253 | "List of Sureties, Hand 1 (11v)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_771 | 652216767 | "Hand 2 (fols. 7–13, 54–72, 92)" | Item_Part_976 | "BL Cotton Vitellius D.xvii, fols. 4–92" |
| Hand_836 | 655776132 | "Office of the Virgin (1r–6r)" | Item_Part_1042 | "BL Royal 2.B.v" |
| Hand_857 | 658810075 | "Latin Hand(s)" | Item_Part_1069 | "BL Royal 6.A.vii" |
| Hand_221 | 659894164 | "Endorsement" | Item_Part_399 | "BL Cotton Augustus ii.23" |
| Hand_1233 | 660553924 | "Latin Hand 2 (2v13–89v)" | Item_Part_1732 | "BAV Reg.lat.1671" |
| Hand_974 | 664541049 | "List of Lands in Stifford (196v)" | Item_Part_1200 | "Bodleian Bodley 155 (1974)" |
| Hand_1265 | 673628789 | "Main Hand" | Item_Part_1816 | "Durham Cathedral B.IV.24, fols. 74–127" |
| Hand_677 | 673743947 | "Added Titles" | Item_Part_914 | "BL Cotton Otho C.i, vol. ii" |
| Hand_459 | 683742151 | "Latin Hand (97r–108v, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_1294 | 683907064 | "Additions Hand 3 (x, 154v, 64v, 170r36–37)" | Item_Part_1840 | "Bodleian Bodley 343" |
| Hand_197 | 688599630 | "Main Hand" | Item_Part_369 | "BL Cotton Augustus ii.43" |
| Hand_566 | 693674204 | "Latin Hand" | Item_Part_839 | "BL Arundel 155, fols. 1–135 and 171–91" |
| Hand_417 | 695372385 | "Corrector" | Item_Part_562 | "CCCC 383" |
| Hand_883 | 696942531 | "Main Latin Hand 2" | Item_Part_1094 | "BL Royal 13.A.xv" |
| Hand_330 | 698167816 | "Annotator 3 (pp. 126, 129)" | Item_Part_513 | "CCCC 178, pp. 1–270" |
| Hand_471 | 701391571 | "Donation Inscription" | Item_Part_651 | "TCC B.11.2 (241)" |
| Hand_1246 | 701552048 | "Signed Note (p. 142)" | Item_Part_1792 | "CCCC 162, pp. 139–60" |
| Hand_1033 | 702970172 | "Calendar, Computus, Contents (ii verso–xi verso)" | Item_Part_1293 | "Bodleian Hatton 113 (5210)" |
| Hand_88 | 708027759 | "Main Hand" | Item_Part_221 | "Canterbury Chart. Ant. B.2, Red Book, no. 20" |
| Hand_1310 | 708766626 | "Main hand (incl. added 'Fader ure', 184v)" | Item_Part_1857 | "BL Cotton Vitellius A.xii, fols. 136–85" |
| Hand_907 | 709162038 | "Main Latin Hand" | Item_Part_1137 | "Lambeth 200, fols. 66–113" |
| Hand_1017 | 715115256 | "Layer Three Glossator (Main Glossator)" | Item_Part_1266 | "Bodleian Digby 146 (1747)" |
| Hand_886 | 717619262 | "Latin Supply Leaf (fol. 7)" | Item_Part_1100 | "BL Royal 15.A.xvi" |
| Hand_1052 | 717767767 | "Interlinear Gloss" | Item_Part_1298 | "Bodleian Junius 27 (5139)" |
| Hand_1342 | 719294664 | "OE Additions (5v, 6r, 16r–21v, 71v, 74r, 175r)" | Item_Part_1890 | "JCO 17" |
| Hand_1176 | 721334267 | "Inscription (1r)" | Item_Part_1547 | "El Escorial E.II.1" |
| Hand_172 | 721909703 | "Main Hand (incl. first endorsement)" | Item_Part_300 | "Salt 84/2/41" |
| Hand_1178 | 722350477 | "Latin Glosses" | Item_Part_1549 | "Évreux, BM 43" |
| Hand_1198 | 722848174 | "OE Glossator 2" | Item_Part_1632 | "Pierpont Morgan M 776" |
| Hand_400 | 727794543 | "Added note (p. 113)" | Item_Part_546 | "CCCC 302" |
| Hand_265 | 737077084 | "OE Interlinear Gloss 1 (43r–44v)" | Item_Part_485 | "CUL Ll.1.10 (2139)" |
| Hand_415 | 739385900 | "Vita breuior (45r–48r)" | Item_Part_560 | "CCCC 367, pt. ii, fols. 45–52" |
| Hand_526 | 741307609 | "Unusual 'g'" | Item_Part_764 | "Exeter 3507" |
| Hand_1264 | 741344937 | "Marginal Addition (p. 36)" | Item_Part_1815 | "TCC R.15.32 (945), pp. 13–36" |
| Hand_1325 | 746256207 | "Fifty-seven Glosses" | Item_Part_1874 | "Hereford P.I.17" |
| Hand_275 | 755895091 | "Main Latin Hand" | Item_Part_496 | "CCCC 9, pp. 1–60" |
| Hand_918 | 763936877 | "Main Hand" | Item_Part_1146 | "Lambeth 427, fols. 210 and 211" |
| Hand_437 | 765541499 | "'Other Hand' (182v)" | Item_Part_574 | "CCCC 473" |
| Hand_899 | 767902782 | "Liber Vitae Addition (Godwine iustines sunu, 28v)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_964 | 771230649 | "Main Hand" | Item_Part_1182 | "Bodleian Auctarium F.4.32 (2176), fols. 10–18" |
| Hand_860 | 771328501 | "Main Glossator" | Item_Part_1076 | "BL Royal 7.C.iv" |
| Hand_559 | 775065818 | "OE Glosses" | Item_Part_835 | "BL Additional 71687" |
| Hand_773 | 779894219 | "OE Hand, incl. gloss" | Item_Part_978 | "BL Cotton Vitellius E.xviii" |
| Hand_518 | 780278361 | "Proverbs" | Item_Part_742 | "Durham Cathedral B.III.32" |
| Hand_1284 | 781235435 | "Additions Hand 1 (4v–6v, 67v, 165r14–22, 166r–69r)" | Item_Part_1835 | "BL Cotton Vespasian D.xiv, fols. 4–169" |
| Hand_110 | 781251518 | "Main Hand" | Item_Part_242 | "Exeter 2526" |
| Hand_1057 | 782665465 | "Hand 6 (fols. 138–48)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_864 | 789000473 | "Scribble (106v)" | Item_Part_1076 | "BL Royal 7.C.iv" |
| Hand_1041 | 790513159 | "Addition 5 (247r)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_1072 | 804483159 | "Hand 3 (17r11–23)" | Item_Part_1323 | "Bodleian Laud Misc.509 (942)" |
| Hand_567 | 805776956 | "Main Hand" | Item_Part_841 | "BL Burney 277, fol. 42" |
| Hand_482 | 808473016 | "Main Hand" | Item_Part_656 | "TCC B.15.34 (369)" |
| Hand_893 | 813306682 | "OE Corrector" | Item_Part_1122 | "BL Stowe 2" |
| Hand_185 | 817227477 | "Main Hand" | Item_Part_356 | "Winchester Coll. 12091" |
| Hand_467 | 821599962 | "Latin Hand (124r–125v, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_892 | 826600614 | "OE Glossator" | Item_Part_1122 | "BL Stowe 2" |
| Hand_112 | 827160043 | "Main Hand" | Item_Part_244 | "Exeter 2527" |
| Hand_147 | 836970820 | "Main Hand" | Item_Part_278 | "Exeter 2528" |
| Hand_1009 | 839265967 | "Back-leaning 'a'" | Item_Part_1240 | "Bodleian Bodley 718 (2632)" |
| Hand_334 | 839464602 | "Main Hand (incl. OE glosses, 70r)" | Item_Part_515 | "CCCC 183" |
| Hand_1199 | 840585428 | "Main Hand" | Item_Part_1642 | "Pierpont Morgan G 63" |
| Hand_1291 | 841030134 | "Main Hand" | Item_Part_1839 | "Bodleian Bodley 180" |
| Hand_1039 | 842097789 | "Addition 3 (5r–8v)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_981 | 843179299 | "Latin" | Item_Part_1210 | "Bodleian Bodley 311 (2122)" |
| Hand_1252 | 848847186 | "Latin Hand (p. 422)" | Item_Part_1793 | "CCCC 391" |
| Hand_503 | 849954663 | "Latin Hand 5 (1r–8r4)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_1256 | 850748029 | "Latin Additions (pp. 17–46, 53–60)" | Item_Part_496 | "CCCC 9, pp. 1–60" |
| Hand_476 | 851765773 | "Latin Hand 1 (22v5–23r4)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_985 | 857190988 | "Principal Corrector (incl. addition in 202v of 342)" | Item_Part_1215 | "Bodleian Bodley 340 (2404) and 342 (2405)" |
| Hand_939 | 857832598 | "Names (173r)" | Item_Part_1172 | "Bodleian Auctarium D.2.14 (2698), fol. 173" |
| Hand_824 | 858517756 | "Latin Hand 1" | Item_Part_1038 | "BL Royal 1.D.ix" |
| Hand_91 | 860281970 | "Main Hand" | Item_Part_224 | "Canterbury Chart. Ant. C.3" |
| Hand_1060 | 860935730 | "Hand 9 (154v–57r)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_897 | 863139520 | "Relic List, Hand 2 (58r23–58v13)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_852 | 867056687 | "Glossator 1" | Item_Part_1067 | "BL Royal 6.A.vi" |
| Hand_1179 | 867930455 | "Main Hand (Latin)" | Item_Part_1551 | "Florence Plut.xvii.20" |
| Hand_1262 | 867936679 | "Latin Hand(s)" | Item_Part_1814 | "CCCC 265" |
| Hand_323 | 872911300 | "Chronicle Hand 4 (28r; annals 962–3 and 964)" | Item_Part_511 | "CCCC 173, fols. 1–56" |
| Hand_794 | 876482822 | "Latin Hand 1 (fols. 28–49)" | Item_Part_997 | "BL Harley 603" |
| Hand_906 | 879089536 | "OE Glossator (212v, 214r)" | Item_Part_1135 | "Lambeth 173, fols. 157–221" |
| Hand_1038 | 886501521 | "Addition 2 (4v)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_561 | 893233577 | "Ages of the World (149r)" | Item_Part_837 | "BL Arundel 60" |
| Hand_381 | 896097355 | "Glossator 1 (p. 30; Ker article c.i)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_1197 | 898685813 | "OE Glossator 1" | Item_Part_1632 | "Pierpont Morgan M 776" |
| Hand_1098 | 904670653 | "Main Latin Text, most of Gloss" | Item_Part_1361 | "Oriel 3" |
| Hand_952 | 905155663 | "OE Glossator 1 (39r, 40v)" | Item_Part_1178 | "Bodleian Auctarium F.2.14 (2657)" |
| Hand_253 | 908099549 | "Hand 1 (1–148, less fols 7, 9–21)" | Item_Part_474 | "CUL Ii.4.6 (1803)" |
| Hand_251 | 909239172 | "Main Hand" | Item_Part_470 | "CUL Ii.2.4 (1737)" |
| Hand_1321 | 910644197 | "Main hand (incl. two writs, 72r and 77r)" | Item_Part_1870 | "Ely s.n." |
| Hand_489 | 912130373 | "Latin Gloss" | Item_Part_665 | "TCC R.15.32 (945), pp. i, ii, 1–12, 37–218" |
| Hand_1295 | 912880176 | "Main Hand" | Item_Part_1841 | "Bodleian Hatton 38" |
| Hand_1311 | 917614713 | "OE Glosses (10v)" | Item_Part_1858 | "BL Cotton Vitellius C.iii, fols. 5–10" |
| Hand_1292 | 919277573 | "Main Hand (fols. 1–170)" | Item_Part_1840 | "Bodleian Bodley 343" |
| Hand_431 | 922494793 | "Latin Supply Leaf" | Item_Part_571 | "CCCC 430" |
| Hand_874 | 923194521 | "Latin Hand (fols. 2–19r)" | Item_Part_1083 | "BL Royal 8.C.iii" |
| Hand_264 | 923778922 | "OE Addition (2r1–3)" | Item_Part_485 | "CUL Ll.1.10 (2139)" |
| Hand_163 | 925188485 | "Main Hand" | Item_Part_294 | "Exeter 2071" |
| Hand_493 | 932161003 | "Main Latin Hand (fols. 12–109)" | Item_Part_666 | "TCC O.1.18 (1042)" |
| Hand_1305 | 940889686 | "OE Addition, 140r" | Item_Part_1820 | "Brussels, BR 8558–8563 (2498), fols. 132–153" |
| Hand_34 | 941010850 | "Record E: Writ of Edward the Confessor (5v)" | Item_Part_853 | "BL Cotton Claudius A.iii, fols. 2–7 and 9*" |
| Hand_392 | 942133103 | "Second Marginal Glossator (105v–111v)" | Item_Part_539 | "CCCC 272" |
| Hand_365 | 949365326 | "Hexateuch Script (pp. 151–60)" | Item_Part_527 | "CCCC 201, pp. 8–160, 167–76" |
| Hand_268 | 950484180 | "Main Hand" | Item_Part_487 | "CUL Additional 3206" |
| Hand_60 | 951372664 | "Main Hand" | Item_Part_199 | "BL Stowe Ch. 21" |
| Hand_207 | 955785865 | "Main Hand" | Item_Part_385 | "BL Additional Ch. 19788" |
| Hand_1166 | 957006087 | "Latin Gloss" | Item_Part_1525 | "Christchurch private collector s.n.?" |
| Hand_943 | 959758580 | "OE Gloss" | Item_Part_1174 | "Bodleian Auctarium D.2.19 (3946)" |
| Hand_101 | 962451432 | "Main Hand" | Item_Part_234 | "Exeter 2517" |
| Hand_179 | 967036781 | "Main Hand" | Item_Part_350 | "LRO Records Office Ch. 1a" |
| Hand_830 | 967513318 | "Addition Hand 5 (6r)" | Item_Part_1042 | "BL Royal 2.B.v" |
| Hand_333 | 970186881 | "Record of Land Grant (96v)" | Item_Part_515 | "CCCC 183" |
| Hand_783 | 974863980 | "Hand 2 (49r2–72v)" | Item_Part_988 | "BL Harley 107" |
| Hand_210 | 977628540 | "Main Hand" | Item_Part_388 | "W.A.M. II" |
| Hand_1243 | 978088606 | "Glossator" | Item_Part_1755 | "Sondershausen Br 1" |
| Hand_527 | 982343128 | "OE Glosses (98v)" | Item_Part_764 | "Exeter 3507" |
| Hand_538 | 983237016 | "Latin Hand A (fols. 1–99)" | Item_Part_807 | "BL Additional 28188" |
| Hand_439 | 987489796 | "OE Glosses" | Item_Part_579 | "Fitz. 45-1980" |
| Hand_930 | 996524937 | "OE Glosses" | Item_Part_1168 | "Bodleian Ashmole 1431 (7523)" |
| Hand_724 | 997945494 | "OE Interlinear Glosses" | Item_Part_940 | "BL Cotton Tiberius C.ii" |
| Hand_309 | 998810036 | "Latin Additions 3" | Item_Part_507 | "CCCC 146" |
| Hand_1290 | 1000705769 | "Names of Evangelists (33r)" | Item_Part_1838 | "BL Royal 1.A.xiv" |
| Hand_464 | 1001503584 | "Latin Hand (169r–182v, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_1338 | 1007640843 | "Trilingual Proverbs (13v)" | Item_Part_1886 | "Bodleian Rawlinson c.641" |
| Hand_1332 | 1016617217 | "Main hand (incl. Glossary, fols. 68–73)" | Item_Part_1881 | "Bodleian Laud misc. 567" |
| Hand_213 | 1018098349 | "Main Hand" | Item_Part_392 | "BL Stowe Ch. 10" |
| Hand_796 | 1023435912 | "Latin Hand (fol. 1)" | Item_Part_998 | "BL Harley 647" |
| Hand_1336 | 1023926092 | "Added notes (1r)" | Item_Part_1885 | "Pembroke 82" |
| Hand_1111 | 1024830597 | "Latin Hand" | Item_Part_1425 | "Salisbury 172" |
| Hand_648 | 1024900855 | "Main Hand" | Item_Part_893 | "BL Cotton Nero E.i, vol. i and vol. ii fols. 1–155" |
| Hand_456 | 1032424852 | "Added directions (1v–2v)" | Item_Part_629 | "SSCC 100 (olim Δ.5.15), pt. ii" |
| Hand_1345 | 1038016471 | "Glosses (156rv, 158rv, 159v, 160r)" | Item_Part_1892 | "BL Stowe 57" |
| Hand_180 | 1038031022 | "Main Hand" | Item_Part_351 | "LRO Records Office Ch. 2" |
| Hand_1054 | 1038277289 | "Hand B (2v, 12r–16v, 25r–33v, 34r1–4)" | Item_Part_1299 | "Bodleian Junius 85 and 86 (5196–7)" |
| Hand_507 | 1038649989 | "Latin Gloss" | Item_Part_675 | "TCC O.4.11 (1242)" |
| Hand_746 | 1043629427 | "Hand 1, incl. cont. gloss (1–92)" | Item_Part_957 | "BL Cotton Vespasian D.xii" |
| Hand_1062 | 1044844887 | "Insertions (e.g. 27r, 150r)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_935 | 1050270802 | "Latin Hand 7 (fols. 39–52)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_870 | 1052045056 | "Scribe Y (additions and corrections)" | Item_Part_1078 | "BL Royal 7.C.xii, 4–218" |
| Hand_78 | 1055596159 | "Main Hand" | Item_Part_211 | "Bodleian Eng. hist. a.2, no. iii" |
| Hand_1253 | 1058340917 | "Latin Gloss (p. 422)" | Item_Part_1793 | "CCCC 391" |
| Hand_599 | 1059042995 | "Latin Couplet (55v)" | Item_Part_869 | "BL Cotton Domitian i, fols. 2–55" |
| Hand_945 | 1060430676 | "Donation Inscription (77r)" | Item_Part_1176 | "Bodleian Auctarium F.1.15 (2455), fols. 1–77" |
| Hand_421 | 1062380049 |  | Item_Part_563 | "CCCC 389" |
| Hand_856 | 1063829278 | "Latin Hands (2)" | Item_Part_1068 | "BL Royal 6.A.vii, fols. 1 and 162v" |
| Hand_863 | 1065627424 | "Main Latin Hand" | Item_Part_1076 | "BL Royal 7.C.iv" |
| Hand_589 | 1067765233 | "Hand 6 (fols. 57v)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_280 | 1067896221 | "Titles, Hand 3 (Titles 57, 66, 78)" | Item_Part_498 | "CCCC 23, vol. i" |
| Hand_1285 | 1071112711 | "Additions Hand 2 (163v11–166r10)" | Item_Part_1835 | "BL Cotton Vespasian D.xiv, fols. 4–169" |
| Hand_738 | 1075656179 | "Latin Liturgica" | Item_Part_947 | "BL Cotton Vespasian A.i" |
| Hand_1333 | 1077641378 | "Caedmon's Hymn (83r)" | Item_Part_1882 | "Lincoln Coll. Ox. lat.31, fols. 14–113" |
| Hand_878 | 1079516014 | "Latin Hand 2 (99r, 99v5–100r2, 100r14–101v7, 101v11–102v, 103v–106r)" | Item_Part_1086 | "BL Royal 12.C.xxiii" |
| Hand_271 | 1083134013 | "Latin Hand(s)" | Item_Part_494 | "CCC 30, pt. ii" |
| Hand_990 | 1083334598 | "Cryptograms (40r)" | Item_Part_1231 | "Bodleian Bodley 572 (2026), fols. 26–40" |
| Hand_257 | 1084925173 | "Signed Note, Titles (87v; 84v, 85v)" | Item_Part_479 | "CUL Kk.3.18 (2004)" |
| Hand_171 | 1085365982 | "Hand 2 (witness-list)" | Item_Part_299 | "BL Cotton Augustus ii.39" |
| Hand_144 | 1086938559 | "Main Hand" | Item_Part_274 | "BL Cotton Ch. xvi.31" |
| Hand_299 | 1092366585 | "C: Bath relic list (p. 7; Ker article 7)" | Item_Part_503 | "CCCC 111, pp. 7, 8, 55 and 56" |
| Hand_576 | 1093220750 | "Record D (6v, from 'Ðis synd')" | Item_Part_853 | "BL Cotton Claudius A.iii, fols. 2–7 and 9*" |
| Hand_994 | 1094994059 | "Main Latin Hand" | Item_Part_1233 | "Bodleian Bodley 577 (27645)" |
| Hand_1063 | 1095895702 | "Insertion (120v)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_1207 | 1098526571 | "Latin rubricator" | Item_Part_1680 | "BnF latin 2825, fols. 57–81" |
| Hand_606 | 1099848750 | "Main Latin Hand" | Item_Part_872 | "BL Cotton Domitian ix, fols. 2–7" |
| Hand_448 | 1104479217 | "Scribble (FULWIHT, 168r)" | Item_Part_605 | "Pembroke 88" |
| Hand_976 | 1106649281 | "Glossary (250r)" | Item_Part_1201 | "Bodleian Bodley 163 (2016), fols. 1–227, 250 and 251" |
| Hand_1206 | 1107183706 | "Latin Main Hand (fols. 85–111)" | Item_Part_1677 | "BnF latin 987" |
| Hand_397 | 1107427788 | "Main Hand" | Item_Part_546 | "CCCC 302" |
| Hand_116 | 1107948943 | "Main Hand" | Item_Part_247 | "Hertford D/ELw Z 22/4" |
| Hand_803 | 1110289701 | "Latin Hand (73r–85r8, 87r2–93r)" | Item_Part_1015 | "BL Harley 3020, fols. 36–94" |
| Hand_231 | 1112536871 | "fol. 4r, added" | Item_Part_458 | "CUL Ff.1.23 (1156)" |
| Hand_650 | 1115010928 | "Main Hand" | Item_Part_897 | "BL Cotton Otho A.vi, fols. 1–129" |
| Hand_1045 | 1115244587 | "Sermon (fols. 140–47)" | Item_Part_1295 | "Bodleian Hatton 115 (5135), fols. 1–147" |
| Hand_908 | 1121511382 | "Glossator 1 (70v)" | Item_Part_1138 | "Lambeth 204" |
| Hand_1249 | 1121759104 | "Hand B: Prayers (pp. 601–3, 611–12)" | Item_Part_1793 | "CCCC 391" |
| Hand_473 | 1125593564 | "OE Glosses" | Item_Part_651 | "TCC B.11.2 (241)" |
| Hand_1116 | 1125695536 | "Main Hand" | Item_Part_1435 | "Wells 7" |
| Hand_382 | 1126197154 | "Glossator 2 (p. 39; Ker article c.ii)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_377 | 1126285604 | "Scratched Glosses" | Item_Part_533 | "CCCC 223" |
| Hand_193 | 1127300236 | "Main Hand" | Item_Part_365 | "Longleat Library of the Marquess of Bath Muniments 10565" |
| Hand_922 | 1131142020 | "Hand 4 (31r–46v)" | Item_Part_1149 | "Lambeth 489" |
| Hand_537 | 1131198436 | "Latin Glosses" | Item_Part_806 | "BL Additional 24199, fols. 2–38" |
| Hand_565 | 1135612565 | "One Gloss (asolcennes, 177r16)" | Item_Part_839 | "BL Arundel 155, fols. 1–135 and 171–91" |
| Hand_1236 | 1140235840 | "Latin Glosses" | Item_Part_1732 | "BAV Reg.lat.1671" |
| Hand_111 | 1145593583 | "Main Hand" | Item_Part_243 | "Exeter 2527" |
| Hand_772 | 1145905330 | "Hand 3 (1–6, 14, 17–21, 73–91)" | Item_Part_976 | "BL Cotton Vitellius D.xvii, fols. 4–92" |
| Hand_929 | 1146025339 | "Main Hand" | Item_Part_1167 | "Bodleian Ashmole 328 (6882 and 7420)" |
| Hand_256 | 1146412467 | "Main Hand" | Item_Part_479 | "CUL Kk.3.18 (2004)" |
| Hand_1136 | 1148850396 | "List of Sureties (161v)" | Item_Part_1461 | "York Additional 1, fols. 10–161" |
| Hand_1025 | 1151162062 | "Latin Hand (1r–7v)" | Item_Part_1285 | "Bodleian Hatton 42 (4117)" |
| Hand_379 | 1152893095 | "Hand B: Laws (pp. 222–27, less pp. 224/20–225/12)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_611 | 1154538556 | "Corrector" | Item_Part_877 | "BL Cotton Faustina A.x, fols. 3–101" |
| Hand_1035 | 1154734894 | "Annotations, Signed Note (eg. 70v, 78r, 86r, 108v, 128v; 78v)" | Item_Part_1293 | "Bodleian Hatton 113 (5210)" |
| Hand_270 | 1156334654 | "Latin Hand(s)" | Item_Part_493 | "CCC 30, pt. i" |
| Hand_1056 | 1157503178 | "Hand 3 (148v10–22, 150r, 150v16–151r, 152r–53v, 154r17–154v12)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_286 | 1165165962 | "Glossator (53v, 65v, 66v)" | Item_Part_500 | "CCCC 44" |
| Hand_748 | 1165326697 | "OE Scratched Gloss" | Item_Part_958 | "BL Cotton Vespasian D.xiv, fols. 170–224" |
| Hand_236 | 1166317178 | "Latin Hand (25rv, 28r–29v, 32rv, 33r–48v)" | Item_Part_462 | "CUL Ff.4.43 (1286)" |
| Hand_525 | 1169925110 | "Main Hand" | Item_Part_763 | "Exeter 3501, fols. 8–130" |
| Hand_931 | 1170597270 | "Latin Hand 1 (fols. 1–8, 88–96)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_35 | 1172961227 | "Records B (6r, start of 6v)" | Item_Part_853 | "BL Cotton Claudius A.iii, fols. 2–7 and 9*" |
| Hand_562 | 1175398227 | "Latin Addition (fols. 133–142)" | Item_Part_837 | "BL Arundel 60" |
| Hand_946 | 1178119574 | "Main Hand (Latin)" | Item_Part_1176 | "Bodleian Auctarium F.1.15 (2455), fols. 1–77" |
| Hand_1210 | 1179984004 | "Latin Gloss" | Item_Part_1688 | "BnF latin 6401A" |
| Hand_1194 | 1179992773 | "OE Glosses" | Item_Part_1625 | "Beinecke 401A" |
| Hand_1286 | 1180115485 | "Main Hand" | Item_Part_1836 | "BL Cotton Vitellius A.xv, fols. 4–93" |
| Hand_255 | 1181988601 | "Contemporary glosses and additions" | Item_Part_474 | "CUL Ii.4.6 (1803)" |
| Hand_1075 | 1182317346 | "Latin Hand 2 (2r–6r)" | Item_Part_1327 | "Bodleian Rawlinson C.570 (12415)" |
| Hand_416 | 1190604267 | "Main Hand" | Item_Part_562 | "CCCC 383" |
| Hand_478 | 1190979321 | "Latin Hand 3 (21v, glosses)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_372 | 1194465712 | "Main Hand (Latin)" | Item_Part_530 | "CCCC 214" |
| Hand_858 | 1196946125 | "Main Glossator" | Item_Part_1070 | "BL Royal 6.B.vii" |
| Hand_498 | 1198380819 | "Main Glossator" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_1077 | 1200795193 | "OE Glossator 1" | Item_Part_1331 | "Bodleian Rawlinson G.57 (14788) and G.111 (14836)" |
| Hand_468 | 1200799674 | "Latin Hand (161r/i/1–ii/35, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_347 | 1201466578 | "Main Hand" | Item_Part_520 | "CCCC 191" |
| Hand_1026 | 1205040766 | "Cædmon's Hymn (129r)" | Item_Part_1286 | "Bodleian Hatton 43 (4106)" |
| Hand_85 | 1205393202 | "Main Hand" | Item_Part_218 | "CUL EDC 1B/1A" |
| Hand_607 | 1205755098 | "Main Latin Glossator (incl. OE glosses on 4r, 7r)" | Item_Part_872 | "BL Cotton Domitian ix, fols. 2–7" |
| Hand_387 | 1205984213 | "Glossator 7 (p. 63; Ker article c.vii)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_891 | 1207631923 | "Medical Glosses" | Item_Part_1111 | "BL Sloane 475, fols. 125–231" |
| Hand_986 | 1212297079 | "Additions 1 (MS 342, fols. 203r–206r)" | Item_Part_1215 | "Bodleian Bodley 340 (2404) and 342 (2405)" |
| Hand_1320 | 1212397014 | "Main hand (Bede's Death-song, p. 57)" | Item_Part_1869 | "Durham, UL Cosin V.ii.6" |
| Hand_551 | 1213596807 | "Thorney Liber Vitae (10r–10va)" | Item_Part_818 | "BL Additional 40000" |
| Hand_843 | 1214093350 | "Latin Hand 1 (3r–6v, 82r–115v, 1rv, 120rv, 119r1, 7r–9v)" | Item_Part_1060 | "BL Royal 5.E.xi" |
| Hand_461 | 1220988067 | "Latin Hand (20v/i/17–21r, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_969 | 1223107023 | "OE Glosses" | Item_Part_1186 | "Bodleian Bodley 49 (1946)" |
| Hand_239 | 1225312045 | "Latin Hand (26rv, 31rv, 65r–72v)" | Item_Part_462 | "CUL Ff.4.43 (1286)" |
| Hand_623 | 1226143772 | "Main Hand" | Item_Part_881 | "BL Cotton Julius A.ii, fols. 10–135" |
| Hand_303 | 1228788521 | "F: Manumission 5 (Sæwig, 1v)" | Item_Part_505 | "CCCC 140" |
| Hand_928 | 1229695440 | "Latin Glosses" | Item_Part_1164 | "Rylands 109" |
| Hand_348 | 1231120919 | "Contemporary corrections, alterations, and glosses" | Item_Part_520 | "CCCC 191" |
| Hand_1318 | 1231479791 | "Glosses (fol. 1 ff)" | Item_Part_1867 | "Dresden, Sächs. Dc.186" |
| Hand_308 | 1231651350 | "Latin Additions 2" | Item_Part_507 | "CCCC 146" |
| Hand_162 | 1232007812 | "Record Hand 2 (135v)" | Item_Part_777 | "Hereford P.I.2" |
| Hand_1055 | 1232146794 | "Main Hand (fols. 1–137)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_675 | 1232319493 | "Hand 3 (139v5–148v)" | Item_Part_914 | "BL Cotton Otho C.i, vol. ii" |
| Hand_905 | 1240251303 | "Main Latin Hand" | Item_Part_1133 | "Lambeth 149, fols. 1–139" |
| Hand_683 | 1242183382 | "Annotator" | Item_Part_919 | "BL Cotton Tiberius A.iii, fols. 2–173" |
| Hand_1003 | 1243573560 | "Manumissions, Hand 2 (no. 1 on 1r)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_205 | 1246601567 | "Main Hand" | Item_Part_381 | "Dorset RO D.124, 1" |
| Hand_1125 | 1247383922 | "Heading (78v)" | Item_Part_1447 | "Worcester Q.5" |
| Hand_470 | 1251768681 | "OE Glosses" | Item_Part_650 | "TCC B.10.5 (216)" |
| Hand_310 | 1254199614 | "Welsh Glosses" | Item_Part_508 | "CCCC 153" |
| Hand_590 | 1257433854 | "Hand 7 (58r1–10)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_588 | 1260120855 | "Hand 5 (fols. 56–57)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_869 | 1268651800 | "Scribe X (fol. 169)" | Item_Part_1078 | "BL Royal 7.C.xii, 4–218" |
| Hand_965 | 1272306805 | "Alterations" | Item_Part_1182 | "Bodleian Auctarium F.4.32 (2176), fols. 10–18" |
| Hand_610 | 1277493578 | "Maxims (100v)" | Item_Part_877 | "BL Cotton Faustina A.x, fols. 3–101" |
| Hand_75 | 1279182431 | "List of Sureties, Hand 2 (11v)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_146 | 1282083602 | "Main Hand" | Item_Part_276 | "BL Cotton Ch. xi.51" |
| Hand_1123 | 1282195310 | "OE Heading (24r)" | Item_Part_1445 | "Worcester F.173" |
| Hand_214 | 1283186834 | "Main Hand" | Item_Part_394 | "BL Cotton Augustus ii.30" |
| Hand_195 | 1283428913 | "Main Hand" | Item_Part_367 | "BL Cotton Augustus ii.45" |
| Hand_398 | 1284553941 | "Hand B (p. 29/1–8)" | Item_Part_546 | "CCCC 302" |
| Hand_380 | 1285429980 | "Hand C (pp. 224/20–225/12)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_506 | 1286218901 | "Main Latin Hand, incl. gloss" | Item_Part_674 | "TCC O.4.10 (1241)" |
| Hand_234 | 1286642364 | "Welsh, Irish, and Latin Glosses" | Item_Part_461 | "CUL Ff.4.42 (1285)" |
| Hand_775 | 1291218746 | "Latin Gloss" | Item_Part_979 | "BL Egerton 267, fol. 37" |
| Hand_129 | 1291575237 | "Main Hand" | Item_Part_260 | "W.A.M. XVIII" |
| Hand_430 | 1293628408 | "p. 520" | Item_Part_570 | "CCCC 422, pp. 27–570" |
| Hand_1313 | 1293899145 | "Added OE prayer (149r)" | Item_Part_1862 | "CUL Mm.4.28" |
| Hand_1170 | 1302786115 | "Main Latin Hand 2" | Item_Part_1532 | "Copenhagen, KB G.K.S.10 (2º)" |
| Hand_1067 | 1302836393 | "OE Glosses" | Item_Part_1317 | "Bodleian Lat. th. d.24 (30591), fols. 1 and 2" |
| Hand_644 | 1303259639 | "Latin Hand 2" | Item_Part_890 | "BL Cotton Nero C.v, fols. 1–161" |
| Hand_1346 | 1311502607 | "Main hand (incl. Bede's Death-song, 112v)" | Item_Part_1893 | "BL Stowe 104" |
| Hand_1043 | 1317229525 | "Annotations (eg. 86r)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_1068 | 1320353611 | "Latin Hand(s)" | Item_Part_1318 | "Bodleian Lat. th. d.33" |
| Hand_1302 | 1321568933 | "Additions" | Item_Part_1844 | "Rochester s.n." |
| Hand_249 | 1321942753 | "Supply Hand 1 (fols. 11–12)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_888 | 1324628256 | "Main Latin Hand" | Item_Part_1102 | "BL Royal 15.B.xix, fols. 1–35" |
| Hand_1191 | 1325192485 | "Interlinear Latin Gloss" | Item_Part_1590 | "St Petersburg F.v.I.3, fols. 1–38" |
| Hand_571 | 1330350993 | "Main Hand" | Item_Part_849 | "BL Cotton Caligula A.xiv, fols. 93–130" |
| Hand_795 | 1341644087 | "Latin Hand 2 (50r–54r/i/23)" | Item_Part_997 | "BL Harley 603" |
| Hand_133 | 1341802164 | "Main Hand" | Item_Part_264 | "Salt S. MS 7" |
| Hand_900 | 1341838041 | "Liber Vitae Addition (Ealdred. ... ægelhild his uuif, 28v)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_583 | 1350484654 | "Main Hand (1r–75v9a)" | Item_Part_860 | "BL Cotton Cleopatra A.iii" |
| Hand_1079 | 1352881269 | "OE Glosses" | Item_Part_1339 | "Bodleian Printed Books Arch.A.f.131" |
| Hand_260 | 1359928443 | "Names of winds" | Item_Part_480 | "CUL Kk.3.21 (2007)" |
| Hand_170 | 1361020875 | "Hand 1 (to end of BC)" | Item_Part_299 | "BL Cotton Augustus ii.39" |
| Hand_1324 | 1363820773 | "Main hand" | Item_Part_1873 | "Bodleian Hatton 115 (5135), fols. 148–55" |
| Hand_938 | 1364966922 | "Booklist, Hand 2 (173r)" | Item_Part_1172 | "Bodleian Auctarium D.2.14 (2698), fol. 173" |
| Hand_107 | 1365671109 | "Main Hand" | Item_Part_240 | "Exeter 2524" |
| Hand_289 | 1366336407 | "Latin Supply Leaves (8, 19, 22)" | Item_Part_501 | "CCCC 57" |
| Hand_1144 | 1371080580 | "Latin Material" | Item_Part_1467 | "Antwerp M.16.8 (190)" |
| Hand_822 | 1375611117 | "OE Gloss (1r)" | Item_Part_1034 | "BL Harley 7653" |
| Hand_1082 | 1375972348 | "Latin Glosses" | Item_Part_1349 | "CCCO 74" |
| Hand_993 | 1378392068 | "Glossator (11v, 35v, 36r, 65v, 71r, and 73v)" | Item_Part_1233 | "Bodleian Bodley 577 (27645)" |
| Hand_51 | 1382865412 | "Main Hand" | Item_Part_190 | "BL Harley Ch. 43.C.6" |
| Hand_1350 | 1384068061 | "Caedmon's Hymn (78v)" | Item_Part_1898 | "Tournai, BM 134" |
| Hand_1127 | 1384665073 | "Latin Hand 2 (2r–13r6, 14v–15r1)" | Item_Part_1447 | "Worcester Q.5" |
| Hand_361 | 1386687219 | "Hand 11 (fols. 374v–377)" | Item_Part_525 | "CCCC 198" |
| Hand_388 | 1389653020 | "Glossator 8 (p. 112; Ker article c.viii)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_451 | 1391048156 | "Main Hand" | Item_Part_609 | "Pembroke 301" |
| Hand_739 | 1398525019 | "Interpolated Gloss (153r)" | Item_Part_949 | "BL Cotton Vespasian A.xiv, fols. 114–79" |
| Hand_951 | 1398539287 | "OE Gloss" | Item_Part_1177 | "Bodleian Auctarium F.1.15 (2455), fols. 78–93" |
| Hand_799 | 1399278016 | "Latin Hand 1 (Prose Vita Cuthberti)" | Item_Part_1005 | "BL Harley 1117" |
| Hand_962 | 1400998958 | "Scribble 2 (þæt he beo wær, 47v)" | Item_Part_1181 | "Bodleian Auctarium F.4.32 (2176), fols. 1–9 and 19–37" |
| Hand_273 | 1411023757 | "Directions to Reader" | Item_Part_496 | "CCCC 9, pp. 1–60" |
| Hand_137 | 1417018773 | "Endorsement" | Item_Part_267 | "Taunton DD/CC 111489" |
| Hand_1267 | 1417273543 | "OE Gloss (80r)" | Item_Part_1819 | "Brussels, BR 8558–8563 (2498), fols. 80–131" |
| Hand_1008 | 1420712652 | "Donation Inscription (113r)" | Item_Part_1238 | "Bodleian Bodley 708 (2609)" |
| Hand_800 | 1422250348 | "Latin Hand 2 (Verse Vita Cuthberti)" | Item_Part_1005 | "BL Harley 1117" |
| Hand_1330 | 1427609679 | "OE Verses (39v)" | Item_Part_1880 | "Bodleian Laud misc. 413" |
| Hand_1341 | 1429850638 | "Marginalia (18r, 74v)" | Item_Part_1889 | "BL Royal 10.C.v" |
| Hand_134 | 1430316295 | "Main Hand" | Item_Part_265 | "Salt 84/1/41" |
| Hand_105 | 1442208732 | "Main Hand" | Item_Part_238 | "Exeter 2521" |
| Hand_1122 | 1445576812 | "Latin Hand(s)" | Item_Part_1442 | "Worcester F.92" |
| Hand_1254 | 1448219432 | "Latin Hand (p. 295)" | Item_Part_1793 | "CCCC 391" |
| Hand_136 | 1454183679 | "Main Hand" | Item_Part_267 | "Taunton DD/CC 111489" |
| Hand_339 | 1457123785 | "OE Charm (p. 130)" | Item_Part_518 | "CCCC 190, pp. iii–xii, 1–294" |
| Hand_784 | 1457516219 | "Hand 3 (?)" | Item_Part_988 | "BL Harley 107" |
| Hand_612 | 1464952907 | "Marginal additions to text" | Item_Part_877 | "BL Cotton Faustina A.x, fols. 3–101" |
| Hand_758 | 1475285829 | "Recipes, Hand 1 (18v)" | Item_Part_970 | "BL Cotton Vitellius C.iii, fols. 11–85" |
| Hand_1101 | 1478136902 | "Main Latin Hand" | Item_Part_1364 | "JCO 28" |
| Hand_225 | 1482182866 | "Main Latin Hand" | Item_Part_403 | "BL Cotton Augustus ii.29" |
| Hand_1135 | 1482348208 | "List of Service-Books (161r)" | Item_Part_1461 | "York Additional 1, fols. 10–161" |
| Hand_76 | 1489917648 | "Main Hand" | Item_Part_209 | "Bodleian Eng. hist. a.2, no. i" |
| Hand_350 | 1491151477 | "Hand B (pp. 111–122)" | Item_Part_523 | "CCCC 196" |
| Hand_786 | 1494017607 | "Main Latin Hand" | Item_Part_989 | "BL Harley 110" |
| Hand_244 | 1504243622 | "Hand 1 (1r–20v, 22r–64v)" | Item_Part_468 | "CUL Hh.1.10 (1624)" |
| Hand_750 | 1508052003 | "Main Hand (Latin)" | Item_Part_960 | "BL Cotton Vespasian D.xv, fols. 102–121" |
| Hand_419 | 1520568104 | "West-Saxon Genealogy (p. 108 = 69v)" | Item_Part_562 | "CCCC 383" |
| Hand_360 | 1523952943 | "Hand 10 (fols. 322–7)" | Item_Part_525 | "CCCC 198" |
| Hand_545 | 1526948080 | "Latin Addition (fols. 158–60)" | Item_Part_813 | "BL Additional 34890" |
| Hand_460 | 1530303436 | "Latin Hand (16r–20v/i/16, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_188 | 1531949922 | "Main Hand" | Item_Part_360 | "BL Cotton Augustus ii.73" |
| Hand_475 | 1532172528 | "One Gloss (ferliþon, 23r)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_664 | 1532744334 | "Main Hand" | Item_Part_907 | "BL Cotton Otho B.x, fols. 29 and 30" |
| Hand_941 | 1536733545 | "Donation Inscription (6v1–7)" | Item_Part_1173 | "Bodleian Auctarium D.2.16 (2719)" |
| Hand_1089 | 1539126341 | "Latin Glosses (e.g. 106v)" | Item_Part_1350 | "CCCO 197" |
| Hand_267 | 1540941397 | "OE Glosses 3 (57r)" | Item_Part_485 | "CUL Ll.1.10 (2139)" |
| Hand_1180 | 1541988191 | "Main Hand" | Item_Part_1556 | "Geneva 2" |
| Hand_2 | 1544481671 | "Main Hand (cartulary)" | Item_Part_825 | "BL Additional 46204" |
| Hand_369 | 1544941909 | "'Several [Latin] Scribes' incl. Glosses" | Item_Part_529 | "CCCC 206" |
| Hand_435 | 1551170963 | "Main Latin Hand B (neumes; 33v, 81r–88v, 135r–55r, 163–80v, 183r–90v)" | Item_Part_574 | "CCCC 473" |
| Hand_819 | 1564664766 | "Main Latin Hand" | Item_Part_1025 | "BL Harley 5431, fols. 4–126" |
| Hand_1309 | 1565968752 | "Formulas for visitation (fol. 156)" | Item_Part_1856 | "BL Cotton Titus D.xxiv" |
| Hand_301 | 1569524083 | "D: Manumission 3 (Sigewine, 1r)" | Item_Part_505 | "CCCC 140" |
| Hand_932 | 1572798505 | "Latin Hand 2 (9r–12r13, 14r14–14v, 15r20–16v, 59v10–60v, 6v22–25)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_1216 | 1572908316 | "Scratched OE Glosses (33v–42r)" | Item_Part_1699 | "BnF latin 9561" |
| Hand_934 | 1574470727 | "Latin Hand 4 (fols. 17–23)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_1300 | 1579679767 | "Supply-leaf (fol. 106)" | Item_Part_1844 | "Rochester s.n." |
| Hand_200 | 1581388514 | "Main Hand" | Item_Part_374 | "BL Cotton Augustus ii.40" |
| Hand_500 | 1583039648 | "Latin Hand 2 (8r16–20)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_469 | 1584234398 | "Main Hand (Latin)" | Item_Part_649 | "TCC B.10.4 (215)" |
| Hand_436 | 1587126445 | "Main Hand C (Q1: 2v–8v)" | Item_Part_574 | "CCCC 473" |
| Hand_1340 | 1590580841 | "Fourteen Glosses (18v–19v)" | Item_Part_1888 | "BL Royal 7.D.ii" |
| Hand_1343 | 1592025280 | "Bede's Death-song (15r)" | Item_Part_1891 | "Stonyhurst Society of Jesus 69" |
| Hand_740 | 1597077955 | "Latin Annotations, Corrections, etc. (mostly 116r–18v, 148v, 171v and 177v)" | Item_Part_949 | "BL Cotton Vespasian A.xiv, fols. 114–79" |
| Hand_238 | 1597575459 | "Latin Hand (17r–24r, 27rv, 30rv)" | Item_Part_462 | "CUL Ff.4.43 (1286)" |
| Hand_1261 | 1599571251 | "Latin Hand(s)" | Item_Part_1813 | "CCCC 265, pp. 269–367" |
| Hand_560 | 1604676977 | "Continuous Gloss" | Item_Part_837 | "BL Arundel 60" |
| Hand_462 | 1608871538 | "Latin Hand (81r–96v, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_513 | 1614454732 | "Latin Hand and OE glosses (pp. 153–66, 169–76 = 77r–83v, 85r–88v)" | Item_Part_715 | "Durham Cathedral A.IV.19" |
| Hand_1121 | 1616772237 | "Latin Hand" | Item_Part_1441 | "Worcester F.91" |
| Hand_903 | 1617695483 | "Vision of Eadwine (fol. 40)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_1129 | 1618707211 | "Latin Text and Some Latin Glosses" | Item_Part_1448 | "Worcester Q.8, fols. 164–71" |
| Hand_405 | 1622580139 | "Main Hand" | Item_Part_552 | "CCCC 322" |
| Hand_250 | 1625938562 | "Latin Gloss" | Item_Part_469 | "CUL Ii.2.1 (1734)" |
| Hand_497 | 1627521178 | "Main Hand (Latin)" | Item_Part_668 | "TCC O.2.30 (1134), fols. 129–72" |
| Hand_427 | 1629005003 | "Hand B2 (pp. 94–96)" | Item_Part_568 | "CCCC 421, pp. 3–354" |
| Hand_645 | 1631018351 | "OE Interlinear Gloss and inscription" | Item_Part_892 | "BL Cotton Nero D.iv" |
| Hand_594 | 1631533338 | "Main Latin Hand" | Item_Part_866 | "BL Cotton Cleopatra C.viii, fols. 4–37" |
| Hand_288 | 1632764893 | "Latin 'patch' (85v)" | Item_Part_501 | "CCCC 57" |
| Hand_1329 | 1638907774 | "Caedmon's Hymn (82v)" | Item_Part_1879 | "Bodleian Laud misc. 243" |
| Hand_1315 | 1650416308 | "Names and glosses (fol. 7ff)" | Item_Part_1864 | "Dresden, Sächs. Dc.187" |
| Hand_523 | 1652344579 | "Donation Inscription (1r–2v)" | Item_Part_762 | "Exeter 3501, fols. 0–7" |
| Hand_1289 | 1653735654 | "OE Title (3r: Textus IIII ewangeliorum anglice" | Item_Part_1838 | "BL Royal 1.A.xiv" |
| Hand_1323 | 1653773172 | "Six Glosses" | Item_Part_1872 | "BL Harley 3013" |
| Hand_725 | 1657599312 | "Latin Hand" | Item_Part_940 | "BL Cotton Tiberius C.ii" |
| Hand_1251 | 1658386840 | "Latin (pp. 581–91)" | Item_Part_1793 | "CCCC 391" |
| Hand_321 | 1664343542 | "List of Popes and Archbishops of Ca (54v; Ker article 4)" | Item_Part_511 | "CCCC 173, fols. 1–56" |
| Hand_861 | 1664792701 | "Earlier Glossator (fols. 24, 31, 25)" | Item_Part_1076 | "BL Royal 7.C.iv" |
| Hand_337 | 1673428216 | "Latin (?) Additions (p. 5)" | Item_Part_518 | "CCCC 190, pp. iii–xii, 1–294" |
| Hand_366 | 1673713898 | "Latin Additions" | Item_Part_527 | "CCCC 201, pp. 8–160, 167–76" |
| Hand_414 | 1675800097 | "Vision of Leofric (48v13–21)" | Item_Part_560 | "CCCC 367, pt. ii, fols. 45–52" |
| Hand_1165 | 1676003500 | "OE Glosses" | Item_Part_1513 | "Brussels, BR 8558–8563 (2498), fols. 1–79" |
| Hand_1255 | 1681920123 | "Directions to Reader" | Item_Part_1811 | "CCCC 9, pp. 61–458" |
| Hand_643 | 1682662914 | "Latin Hand 1" | Item_Part_890 | "BL Cotton Nero C.v, fols. 1–161" |
| Hand_220 | 1684430996 | "Main Hand" | Item_Part_399 | "BL Cotton Augustus ii.23" |
| Hand_1328 | 1691471619 | "Single Gloss (eorðe, 23v)" | Item_Part_1877 | "Bodleian Lat. misc. d.13 (30572)" |
| Hand_889 | 1695662884 | "Main Hand" | Item_Part_1105 | "BL Royal 15.B.xxii" |
| Hand_937 | 1696231222 | "Booklist, Hand 1 (173r)" | Item_Part_1172 | "Bodleian Auctarium D.2.14 (2698), fol. 173" |
| Hand_1307 | 1697210292 | "Main Hand" | Item_Part_1853 | "BL Cotton Faustina A.ix" |
| Hand_368 | 1697273400 | "Latin Addition (pp. 270–71)" | Item_Part_528 | "CCCC 201, pp. 179–272" |
| Hand_961 | 1698236394 | "Scribble 1 (her segð hu se halga apostol paulus lærð ælcum mæssepreoste þe godes folce to lare byð gesett, 47v)" | Item_Part_1181 | "Bodleian Auctarium F.4.32 (2176), fols. 1–9 and 19–37" |
| Hand_919 | 1699910118 | "Hand 1 (1r–20r)" | Item_Part_1149 | "Lambeth 489" |
| Hand_320 | 1702521549 | "Chronicle Hand 6 (s.a. 1070)" | Item_Part_511 | "CCCC 173, fols. 1–56" |
| Hand_608 | 1707158505 | "Second Runic Hand (11v)" | Item_Part_875 | "BL Cotton Domitian ix, fol. 11" |
| Hand_1301 | 1714561647 | "Supply-leaves (fols. 164, 166, 181)" | Item_Part_1844 | "Rochester s.n." |
| Hand_174 | 1715373179 | "Main Hand" | Item_Part_302 | "Salt 84/3/41" |
| Hand_455 | 1719986650 | "Latin Hand (1r–10v13)" | Item_Part_624 | "JCC 101 (D.26), fols. 1–14" |
| Hand_258 | 1722698748 | "Scratched Glosses" | Item_Part_480 | "CUL Kk.3.21 (2007)" |
| Hand_524 | 1723906611 | "Guild and Manumission Hand" | Item_Part_762 | "Exeter 3501, fols. 0–7" |
| Hand_176 | 1729873516 | "Main Hand" | Item_Part_304 | "Durham, Prior's Kitchen D & C Muniments 2.1, Pontificalium no. 9" |
| Hand_1306 | 1734141774 | "Main Hand (incl. Bede's Death-song, 43r)" | Item_Part_1852 | "BL Cotton Faustina A.v, (except fols. 99–102)" |
| Hand_613 | 1737352453 | "Added glosses in glossary" | Item_Part_877 | "BL Cotton Faustina A.x, fols. 3–101" |
| Hand_770 | 1738181789 | "Hand 1 (fols. 15, 16, 22–54)" | Item_Part_976 | "BL Cotton Vitellius D.xvii, fols. 4–92" |
| Hand_115 | 1738941868 | "Record Hand 1 (134rv)" | Item_Part_777 | "Hereford P.I.2" |
| Hand_1102 | 1744695378 | "Interlinear Glossator (14r)" | Item_Part_1364 | "JCO 28" |
| Hand_1120 | 1745303156 | "Latin Hand(s) (fols. 105–164)" | Item_Part_1439 | "Worcester F.48" |
| Hand_880 | 1751216243 | "Hand 2 (fols. 2–6, 9)" | Item_Part_1090 | "BL Royal 12.G.xii, fols. 2–9" |
| Hand_958 | 1752961787 | "Donation Inscription" | Item_Part_1180 | "Bodleian Auctarium F.3.6 (2666)" |
| Hand_1036 | 1755568909 | "Main Hand (1r–4v, 9–230, 236r–42v)" | Item_Part_1294 | "Bodleian Hatton 114 (5134)" |
| Hand_933 | 1755734580 | "Latin Hand 3 (12r15–14r19, 15r1–19, parts of Q10, 97r–110v)" | Item_Part_1169 | "Bodleian Auctarium D.infra 2.9 (2638), fols. 1–110" |
| Hand_201 | 1755794149 | "Main Hand" | Item_Part_375 | "BL Harley Ch. 43.C.2" |
| Hand_349 | 1760308089 | "Hand A (pp. 1–110)" | Item_Part_523 | "CCCC 196" |
| Hand_1058 | 1761710007 | "Hand 7 (149rv, 150v1–15, 151v)" | Item_Part_1301 | "Bodleian Junius 121 (5232)" |
| Hand_647 | 1762224797 | "OE directions (89v, 127v, 128r, 130r, 147v, 154v)" | Item_Part_893 | "BL Cotton Nero E.i, vol. i and vol. ii fols. 1–155" |
| Hand_186 | 1764340988 | "Main Hand" | Item_Part_358 | "BL Cotton Augustus ii.63" |
| Hand_194 | 1764500242 | "Main Hand" | Item_Part_366 | "BL Cotton Augustus ii.41" |
| Hand_1031 | 1765202824 | "Added Title" | Item_Part_1292 | "Bodleian Hatton 93 (4081), fol. 42" |
| Hand_1193 | 1768907710 | "OE Glosses (incl. eight sets of membra disjecta)" | Item_Part_1624 | "Beinecke 401" |
| Hand_1293 | 1769000200 | "Additions Hand 2 (vols. vi–xxxix verso)" | Item_Part_1840 | "Bodleian Bodley 343" |
| Hand_1076 | 1770021420 | "OE Glosses" | Item_Part_1328 | "Bodleian Rawlinson C.697 (12541)" |
| Hand_191 | 1774583910 | "Main Hand" | Item_Part_363 | "Canterbury Chart. Ant. R.14, Red Book, no. 14" |
| Hand_873 | 1778659879 | "Latin Hand" | Item_Part_1080 | "BL Royal 8.B.xi" |
| Hand_332 | 1780969614 | "Addition, p. 458 (Ker article 2)" | Item_Part_514 | "CCCC 178, pp. 287–457" |
| Hand_474 | 1784522083 | "(Further Hand)" | Item_Part_651 | "TCC B.11.2 (241)" |
| Hand_142 | 1788634702 | "Main Hand" | Item_Part_272 | "BL Cotton Augustus ii.25" |
| Hand_1106 | 1788905270 | "Marginalia to Ælfric" | Item_Part_1366 | "JCO 154" |
| Hand_1064 | 1790177890 | "Main Hand" | Item_Part_1302 | "Bodleian Lat. bib. b.1 (30550), fols. 73 and 74" |
| Hand_1080 | 1791886932 | "Main Hand" | Item_Part_1341 | "All Souls 38, fols. I–VI and i–vi" |
| Hand_1296 | 1793402217 | "Main Hand" | Item_Part_1842 | "Bodleian Hatton 116" |
| Hand_1185 | 1803760777 | "OE Gloss (122v)" | Item_Part_1580 | "Köln, Dombib. 213" |
| Hand_458 | 1805472859 | "Latin Hand 1 (145r/ii/38–40)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_585 | 1806635759 | "Hand 2 (fols. 13–31)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_802 | 1808430806 | "Main Hand (Latin)" | Item_Part_1009 | "BL Harley 2892" |
| Hand_1299 | 1809277604 | "Main Hand" | Item_Part_1844 | "Rochester s.n." |
| Hand_947 | 1812107230 | "Second Latin Glossator (66r–72v)" | Item_Part_1176 | "Bodleian Auctarium F.1.15 (2455), fols. 1–77" |
| Hand_884 | 1812690675 | "Latin Hand(s)" | Item_Part_1097 | "BL Royal 13.C.v" |
| Hand_1298 | 1821890989 | "Chronicle Hand 2 (88v–91v; annals for 1132–54)" | Item_Part_1843 | "Bodleian Laud 636" |
| Hand_338 | 1823186570 | "Main Latin Hand (1–289/6)" | Item_Part_518 | "CCCC 190, pp. iii–xii, 1–294" |
| Hand_751 | 1826209549 | "Main Hand (Vita Guthlaci)" | Item_Part_963 | "BL Cotton Vespasian D.xxi, fols. 18–40" |
| Hand_1266 | 1829928149 | "Scratched Glosses (42rv)" | Item_Part_1818 | "Bodleian Bodley 572 (2026), fols. 41–50" |
| Hand_235 | 1831592524 | "Latin Glosses" | Item_Part_461 | "CUL Ff.4.42 (1285)" |
| Hand_359 | 1835158083 | "Hand 9 (fols. 321v, 367r–74v)" | Item_Part_525 | "CCCC 198" |
| Hand_169 | 1840379812 | "Main Hand (Latin)" | Item_Part_298 | "BL Stowe Ch. 2" |
| Hand_367 | 1840441175 | "Main Hand" | Item_Part_528 | "CCCC 201, pp. 179–272" |
| Hand_609 | 1841934763 | "Main Hand" | Item_Part_877 | "BL Cotton Faustina A.x, fols. 3–101" |
| Hand_274 | 1849452348 | "Latin Additions (fols. 3–34)" | Item_Part_885 | "BL Cotton Nero A.i, fols. 3–57" |
| Hand_166 | 1852167400 | "Main Hand" | Item_Part_296 | "Taunton DD/SAS PR 502" |
| Hand_198 | 1854274215 | "Main Hand" | Item_Part_371 | "Winchester Cath. Library Showcase" |
| Hand_418 | 1867081152 | "List of Shipmen (p. 107 = 69r)" | Item_Part_562 | "CCCC 383" |
| Hand_307 | 1867655835 | "Latin Additions (nuptial blessings; pp. 324–25)" | Item_Part_507 | "CCCC 146" |
| Hand_96 | 1871917923 | "Main Hand" | Item_Part_229 | "Canterbury Chart. Ant. S.261, Red Book, no. 15" |
| Hand_192 | 1874696837 | "Main Hand" | Item_Part_364 | "BL Cotton Augustus ii.44" |
| Hand_177 | 1876317104 | "Hand 3" | Item_Part_798 | "BL Additional 9381" |
| Hand_749 | 1876501204 | "Four OE words (170r)" | Item_Part_958 | "BL Cotton Vespasian D.xiv, fols. 170–224" |
| Hand_1220 | 1877391248 | "Two OE Glosses (to, gemene)" | Item_Part_1711 | "Lewis John Frederick Lewis Collection ET 121" |
| Hand_401 | 1882962013 | "Alterations" | Item_Part_546 | "CCCC 302" |
| Hand_1118 | 1883364905 | "Cædmon's Hymn (81r)" | Item_Part_1436 | "Winchester Cath. 1" |
| Hand_266 | 1883967819 | "OE Interlinear Glossator 2 (43r–44v)" | Item_Part_485 | "CUL Ll.1.10 (2139)" |
| Hand_950 | 1884109831 | "Main Hand (Latin)" | Item_Part_1177 | "Bodleian Auctarium F.1.15 (2455), fols. 78–93" |
| Hand_1047 | 1886492345 | "Inserted Leaf, Hand 2 (fol. 65)" | Item_Part_1295 | "Bodleian Hatton 115 (5135), fols. 1–147" |
| Hand_992 | 1886588994 | "Second Rubricator (40r)" | Item_Part_1231 | "Bodleian Bodley 572 (2026), fols. 26–40" |
| Hand_1070 | 1887970378 | "Main Hand" | Item_Part_1323 | "Bodleian Laud Misc.509 (942)" |
| Hand_472 | 1889009543 | "Main Hand (Latin)" | Item_Part_651 | "TCC B.11.2 (241)" |
| Hand_942 | 1889948381 | "List of Relics (fols. 8–14)" | Item_Part_1173 | "Bodleian Auctarium D.2.16 (2719)" |
| Hand_428 | 1893594393 | "Hand B3 (pp. 209–24)" | Item_Part_568 | "CCCC 421, pp. 3–354" |
| Hand_1331 | 1893806518 | "Main hand (incl. OE Verses, 47r)" | Item_Part_1880 | "Bodleian Laud misc. 413" |
| Hand_390 | 1895909758 | "Marginal Headings (pp. 41, 74, 75, 77 and 78)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_499 | 1896507843 | "Latin Hand 1 (34r–40v)" | Item_Part_669 | "TCC O.2.31 (1135)" |
| Hand_756 | 1897654537 | "OE Glosses (mostly 92v)" | Item_Part_969 | "BL Cotton Vitellius A.xix" |
| Hand_434 | 1899489739 | "Main Latin Hand A (10r–52v, 55r–78v, 89r–134r)" | Item_Part_574 | "CCCC 473" |
| Hand_812 | 1909538230 | "[OBSOLETE: Now G.435-11] Two glosses (se forma monandæg, 120v; forwenednes, 121v)" | Item_Part_1019 | "BL Harley 3271" |
| Hand_953 | 1909729524 | "Wordlist and Glosses (11r–19v; 80v)" | Item_Part_1178 | "Bodleian Auctarium F.2.14 (2657)" |
| Hand_744 | 1911677607 | "Main Latin Hand" | Item_Part_952 | "BL Cotton Vespasian B.x, fols. 31–124" |
| Hand_973 | 1912854646 | "Names of Herbs; Glosses (1rv, 4v, 44rv, 45r, 55r; 81r and 84v)" | Item_Part_1194 | "Bodleian Bodley 130 (27609)" |
| Hand_550 | 1917658197 | "Inscription (fol. 4r)" | Item_Part_818 | "BL Additional 40000" |
| Hand_237 | 1918343508 | "Latin Hand (3r–8v, 9r–10v15, 12r1–16)" | Item_Part_462 | "CUL Ff.4.43 (1286)" |
| Hand_130 | 1918916907 | "Main Hand" | Item_Part_261 | "Paris Archives AE/III/60 (olim Cartons des rois K.19 no.6), main document" |
| Hand_1110 | 1920146996 | "Later OE Glossator (fols. 12–149)" | Item_Part_1413 | "Salisbury 150, fols. 1–151" |
| Hand_1109 | 1920716945 | "Latin Hand (3r ff.)" | Item_Part_1388 | "Salisbury 38" |
| Hand_600 | 1926258873 | "Main Latin Hand" | Item_Part_869 | "BL Cotton Domitian i, fols. 2–55" |
| Hand_208 | 1930388728 | "Main Hand" | Item_Part_386 | "BL Cotton Augustus ii.99" |
| Hand_1117 | 1932764037 | "Chapter Titles" | Item_Part_1435 | "Wells 7" |
| Hand_83 | 1939838440 | "Main Hand" | Item_Part_216 | "Burton 1" |
| Hand_1147 | 1940305816 | "Latin Glosses" | Item_Part_1489 | "Berlin Grimm 132,2" |
| Hand_1002 | 1940336475 | "Manumission Hand 1 (nos. 2–5 on 1rv)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_1007 | 1943960606 | "Latin Hand (e.g. 24r)" | Item_Part_1234 | "Bodleian Bodley 579 (2675)" |
| Hand_722 | 1944528115 | "OE Hand 2 (159v–62v)" | Item_Part_939 | "BL Cotton Tiberius C.i, fols. 43–203" |
| Hand_1190 | 1946166533 | "Main Latin Hand" | Item_Part_1588 | "Leiden Scaliger 69" |
| Hand_1244 | 1946376053 | "Latin Hand(s)" | Item_Part_1769 | "Illinois 128" |
| Hand_263 | 1947774285 | "Latin Hand(s)" | Item_Part_483 | "CUL Kk.5.32 (2074), fols. 49–60" |
| Hand_726 | 1948851002 | "Glossing and OE Hand (19–21r1, 21v–31)" | Item_Part_941 | "BL Cotton Tiberius C.vi" |
| Hand_831 | 1952454727 | "Addition Hand 6 (6v)" | Item_Part_1042 | "BL Royal 2.B.v" |
| Hand_1319 | 1954262052 | "Glossary of herb-names (fols. 82–84)" | Item_Part_1868 | "Durham Cathedral Hunter 100" |
| Hand_1316 | 1955191560 | "Glosses (fol. 30ff)" | Item_Part_1864 | "Dresden, Sächs. Dc.187" |
| Hand_570 | 1958810850 | "Latin Hand(s)" | Item_Part_848 | "BL Cotton Caligula A.xiv, fols. 1–36" |
| Hand_297 | 1964726729 | "Homily, fols. 71r–72v, some manumissions, end of agreement (Ker articles 2, 4, 8, 9)" | Item_Part_505 | "CCCC 140" |
| Hand_450 | 1966004402 | "Scribble (RODBEART, 168r)" | Item_Part_605 | "Pembroke 88" |
| Hand_187 | 1971068323 | "Main Hand" | Item_Part_359 | "BL Stowe Ch. 25" |
| Hand_466 | 1971630624 | "Latin Hand (48r–63v, etc.)" | Item_Part_644 | "TCC B.4.27 (141)" |
| Hand_1224 | 1979050495 | "Latin Glossator 2" | Item_Part_1720 | "BAV lat.3363" |
| Hand_536 | 1982258704 | "Manumission Hand 2 (fol. 8v; Förster no. XXXVII)" | Item_Part_798 | "BL Additional 9381" |
| Hand_584 | 1985660407 | "Hand 1 (fols. 2–12)" | Item_Part_864 | "BL Cotton Cleopatra B.xiii, fols. 1–58" |
| Hand_483 | 1985834829 | "Corrections and Alterations" | Item_Part_656 | "TCC B.15.34 (369)" |
| Hand_411 | 1988511551 | "Latin Hand 2 (p. 138/4–24)" | Item_Part_553 | "CCCC 326" |
| Hand_391 | 1990638856 | "Main Marginal Glossator" | Item_Part_539 | "CCCC 272" |
| Hand_1010 | 1993394603 | "Main Hand" | Item_Part_1247 | "Bodleian Bodley 775 (2558)" |
| Hand_199 | 1997356507 | "Main Hand" | Item_Part_373 | "Exeter 2522" |
| Hand_422 | 1998006095 | "Main Hand (Latin, of Psalter)" | Item_Part_565 | "CCCC 411" |
| Hand_521 | 1998158755 | "Glossator 1" | Item_Part_744 | "Durham Cathedral B.IV.9" |
| Hand_510 | 1998272434 | "Latin Gloss" | Item_Part_692 | "Canterbury Additional 172" |
| Hand_492 | 2000153279 | "Latin Capitula (fols. 2–10)" | Item_Part_666 | "TCC O.1.18 (1042)" |
| Hand_457 | 2001166783 | "Main Latin Hand" | Item_Part_629 | "SSCC 100 (olim Δ.5.15), pt. ii" |
| Hand_1347 | 2006282863 | "Bede's Death-song (p. 26)" | Item_Part_1894 | "TCC R.7.28 (770), pp. 1-74" |
| Hand_1046 | 2007616648 | "Inserted Leaf, Hand 1 (fol. 65)" | Item_Part_1295 | "Bodleian Hatton 115 (5135), fols. 1–147" |
| Hand_1308 | 2009195149 | "Names of winds (11r)" | Item_Part_1855 | "BL Cotton Tiberius C.i, fols. 2–42" |
| Hand_1112 | 2010403228 | "OE Gloss (50v)" | Item_Part_1425 | "Salisbury 172" |
| Hand_117 | 2014687809 | "Main Hand" | Item_Part_248 | "King's Lynn KL/C2/61" |
| Hand_145 | 2016304595 | "Main Hand" | Item_Part_275 | "Worcester B 1680.a" |
| Hand_727 | 2016895399 | "Hand 1 (2r–51v)" | Item_Part_944 | "BL Cotton Titus A.iv" |
| Hand_1030 | 2021690525 | "Main Hand" | Item_Part_1290 | "Bodleian Hatton 76 (4125), fols. 68–130a" |
| Hand_1126 | 2028462294 | "Latin Hand 1 (1v, 13r7–14r, 15r2–47v)" | Item_Part_1447 | "Worcester Q.5" |
| Hand_1023 | 2033752780 | "Latin Hand(s)" | Item_Part_1282 | "Bodleian Hatton 23 (4115)" |
| Hand_1271 | 2037880438 | "Main Hand (Ælfric, De temporibus anni)" | Item_Part_1821 | "BL Cotton Caligula A.xv, fols. 144–153" |
| Hand_983 | 2039054939 | "Main Latin Hand" | Item_Part_1214 | "Bodleian Bodley 319 (2226)" |
| Hand_909 | 2042361182 | "Glossator 2 (25r, 38v, 74v)" | Item_Part_1138 | "Lambeth 204" |
| Hand_141 | 2050149540 | "Main Hand" | Item_Part_271 | "Canterbury Chart. Ant. C.204" |
| Hand_1069 | 2050180049 | "Main Hand" | Item_Part_1322 | "Bodleian Laud Misc.482 (1054)" |
| Hand_921 | 2054850963 | "Hand 3 (25r–31r)" | Item_Part_1149 | "Lambeth 489" |
| Hand_254 | 2058288296 | "Hand 2 (148r–308v, 7r, 9r–21r)" | Item_Part_474 | "CUL Ii.4.6 (1803)" |
| Hand_1322 | 2060552069 | "Names of Winds (7v)" | Item_Part_1871 | "BL Harley 3667" |
| Hand_1270 | 2062484511 | "Extracts from Ælfric, De temporibus anni (fols. 142–43)" | Item_Part_851 | "BL Cotton Caligula A.xv, fols. 120–43" |
| Hand_1223 | 2062762668 | "Latin Glossator 1" | Item_Part_1720 | "BAV lat.3363" |
| Hand_384 | 2062892023 | "Glossator 4 (p. 54; Ker article c.iv)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_797 | 2064416430 | "Main Glossator" | Item_Part_1003 | "BL Harley 863, fols. 8–125" |
| Hand_488 | 2064466005 | "Main Hand" | Item_Part_661 | "TCC R.9.17 (819), fols. 1–48" |
| Hand_182 | 2066749825 | "Main Hand" | Item_Part_353 | "BL Cotton Ch. viii.14" |
| Hand_109 | 2067396408 | "Endorsement" | Item_Part_242 | "Exeter 2526" |
| Hand_896 | 2067795222 | "Relic List, Hand 1 (58r1–21)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_902 | 2074705234 | "Latin Additions (41r, 59r)" | Item_Part_1123 | "BL Stowe 944, fols. 6–61" |
| Hand_761 | 2077098725 | "Recipes, Hand 4 (82v–83)" | Item_Part_970 | "BL Cotton Vitellius C.iii, fols. 11–85" |
| Hand_443 | 2078810765 | "Records (fol. vi)" | Item_Part_604 | "Pembroke 83" |
| Hand_575 | 2088950521 | "Record C (6v, from '7 ic wille')" | Item_Part_853 | "BL Cotton Claudius A.iii, fols. 2–7 and 9*" |
| Hand_86 | 2102317147 | "Main Hand (MS 2)" | Item_Part_219 | "Canterbury Chart. Ant. C.1311" |
| Hand_1088 | 2105554785 | "Main Hand" | Item_Part_1350 | "CCCO 197" |
| Hand_840 | 2105638303 | "Latin Hand(s)" | Item_Part_1052 | "BL Royal 5.A.xii, fols. iii–vi" |
| Hand_671 | 2111747547 | "Addition 1: Part of Papal Bull (fols. 68–69r5)" | Item_Part_913 | "BL Cotton Otho C.i, vol. i" |
| Hand_721 | 2121722976 | "OE Hand 1 (109v–11v, 200r–202r)" | Item_Part_939 | "BL Cotton Tiberius C.i, fols. 43–203" |
| Hand_728 | 2126845866 | "Hand 2 (51v–117r)" | Item_Part_944 | "BL Cotton Titus A.iv" |
| Hand_69 | 2130417986 | "Main Hand" | Item_Part_204 | "BL Stowe Ch. 40" |
| Hand_1348 | 2133179292 | "Main hand (incl. two writs, 87v–88 and 93r)" | Item_Part_1895 | "TCC O.2.1 (1105)" |
| Hand_184 | 2134062284 | "Main Hand" | Item_Part_355 | "BL Cotton Augustus ii.62" |
| Hand_1182 | 2134094668 | "Glossator" | Item_Part_1564 | "Haarlem 188 F 53" |
| Hand_825 | 2134472905 | "Latin Hand 2" | Item_Part_1038 | "BL Royal 1.D.ix" |
| Hand_1317 | 2138796329 | "Names of herbs (fols. 27–39)" | Item_Part_1866 | "Dresden, Sächs. Dc.185" |
| Hand_383 | 2140271525 | "Glossator 3 (p. 41; Ker article c.iii)" | Item_Part_535 | "CCCC 265, pp. 1–268" |
| Hand_477 | 2140481550 | "Latin Hand 2 (13r1–3, 14r2–5, 14v7–12, 21r5, 21r1–18, 60r1–3)" | Item_Part_652 | "TCC B.14.3 (289)" |
| Hand_1084 | 2143148169 | "Notice of Possessions (106v–108r)" | Item_Part_1350 | "CCCO 197" |
| Hand_438 | 2143893658 | "Main Hand" | Item_Part_575 | "CCCC 557" |
| Hand_202 | 2146985176 | "Main Hand" | Item_Part_377 | "BL Harley Ch. 43.C.3" |
---

## Appendix B: Idiographs linked to more than one Scribe (n=63)

| Idiograph | Label | # Scribes | Scribes |
|---|---|---|---|
| Idiograph_1591 | "n" | 9 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1596 | "e" | 9 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1607 | "t" | 9 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1608 | "o" | 9 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1609 | "c" | 9 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1602 | "b" | 8 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1650 | "y, Straight" | 8 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1651 | "h, Insular" | 8 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1668 | "l" | 8 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1669 | "m" | 8 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1674 | "., punctus" | 8 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1675 | "u" | 8 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1585 | "eth" | 7 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1594 | "g, Insular" | 7 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1597 | "d, Insular" | 7 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1610 | "7" | 7 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1671 | "p" | 7 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1676 | "i" | 7 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1575 | "a, Insular" | 6 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1592 | "r, Insular" | 6 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575) |
| Idiograph_1595 | "abbrev. stroke" | 6 | "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1598 | "f, Insular" | 6 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576) |
| Idiograph_1600 | "wynn" | 6 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576) |
| Idiograph_1604 | "thorn" | 6 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576) |
| Idiograph_1847 | "thæt" | 6 | "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1593 | "s, Low" | 5 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 57" (Scribe_167); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575) |
| Idiograph_1603 | "æ, Insular" | 4 | "DigiPal Scribe 56" (Scribe_166); "G.366 Scribe 2" (Scribe_574); "G.366 Scribe 3" (Scribe_575); "Ker, Scribe K" (Scribe_9) |
| Idiograph_1606 | "x" | 4 | "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 3" (Scribe_575); "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1844 | "s, Long" | 4 | "DigiPal Scribe 56" (Scribe_166); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 2" (Scribe_574); "G.366B Scribe 1" (Scribe_576) |
| Idiograph_1677 | "k" | 3 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 56" (Scribe_166); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1679 | "accent" | 3 | "DigiPal Scribe 36" (Scribe_146); "DigiPal Scribe 58" (Scribe_168); "G.366 Scribe 3" (Scribe_575) |
| Idiograph_1590 | "&" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1605 | ";, punctus versus" | 2 | "DigiPal Scribe 36" (Scribe_146); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1670 | "s, Round" | 2 | "DigiPal Scribe 56" (Scribe_166); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1673 | "a, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1690 | "d, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1719 | "a, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1723 | "x. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1724 | "b. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1725 | "c. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1726 | "d, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1728 | "e. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1733 | "eth. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1734 | "f, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1735 | "g, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1736 | "h, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1737 | "i. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1738 | "l. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1739 | "m. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1740 | "n. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1741 | "o. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1742 | "r, Insular. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1743 | "s, Low. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1745 | "t. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1746 | "thorn. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1748 | "wynn. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1749 | "y, Straight. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1753 | "., punctus. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1754 | "7. Ker, Scribe O. saec. xi2" | 2 | "DigiPal Scribe 14" (Scribe_124); "Ker, Scribe O" (Scribe_13) |
| Idiograph_1839 | "r, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_1843 | "s, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_2018 | "f, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |
| Idiograph_2019 | "g, Caroline" | 2 | "G.366B Scribe 1" (Scribe_576); "Nero-Middleton Scribe" (Scribe_567) |