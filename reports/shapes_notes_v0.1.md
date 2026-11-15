# Archetype resource-link shapes (v0.1): generation notes and open points

Companion to `archetype_shapes_0.1.ttl`. Sources: `data_digipal_turtle_202611151557.rdf` (regenerated 2026-11-15; first version from `data_pstokes_turtle_202609222044.rdf`), `creation_rdf.py`, `archetype_ontology_0.1.ttl`. Generator: `gen_shapes.py`, reading `edges.json` produced by `harvest_edges.py`.

## 1. What the file contains

- **44 node shapes** (42 in the first version). There is one for each kind of node that has links: every `archetype:` class, plus the CRM-typed kinds such as Image, Owner, Layout and Writing. Places, Counties and Regions share a single shape, as do Foundation and Refoundation.
- **87 outgoing property shapes.** Each gives the property exactly as it is stored in the data, and the class of the node at the other end.
- **51 incoming property shapes** (48 in the first version) (`sh:inversePath`). These list the links that are stored on *another* node but point at this one. They answer "how do I get from an Idiograph back to its Graphs?"
- Controlled constants (e.g. `data:Type_Accepted`) are given as `sh:in` values rather than as a class.
- There are no cardinalities and no literal properties.

**The original P56i example** (now P46i). The link is stored only as `Item_Part —P46_is_composed_of→ HandInstance` (it was `P56_bears_feature` in the first version; see §5). `P46i_forms_part_of` never appears in the export. The same holds for every CRM inverse: without a reasoner, a SPARQL query must use the forward property with the variables swapped. The incoming shapes give the CRM inverse name only as documentation.

## 2. How it was checked

1. **Harvest.** Every resource-to-resource triple in the export (1,014,667 triples loaded into Oxigraph) was grouped by subject kind, property and object kind. This gave 104 distinct patterns. The 10 dataset-metadata patterns (foaf/org/dcterms) were set aside.
2. **Code.** `creation_rdf.py` was read in full. Four links are emitted by the code but have no data in DigiPal: Item Part → Layout, Item Part → Dimension, Owner → Person and Owner → Institution. They are included in the shapes and marked "not populated in DigiPal".
3. **Accuracy.** pySHACL was run with the shapes against the whole export (558k resource triples). Every shape was applied to every node of its kind. Result: **conforms, 0 violations**.
4. **Completeness.** The same run was repeated with every shape "closed", so that any link not described by a shape would be reported. Two wrong links were deliberately injected as a control. The only violations reported were the four expected from those two injected links, so **no real link in the export is missing from the shapes**.

## 3. Points for you to rule on

Items A–D are things in the data or code that look wrong. Items E–H are things the profile exposes rather than errors.

**A. `archetype:Script` is declared but never used.** The ontology declares the class (⊑ E29, TX10_Style), but the export has 0 instances. The 4 Script nodes are typed only `crm-tx:TX10_Style`. So are the 23 Latin Style nodes, which have no `archetype:` class at all. The options are to type Script nodes `archetype:Script` in the code, or to drop the class. Latin Style needs the same decision, which ties into the existing TODO on unifying Script, Style and Appearance.

**B. `Current_Item owl:sameAs data:Item_<id>` looks like a leftover.** There are 1,675 of these triples.
- The `<id>` is the **Item Part's** id, not the Current Item's.
- The `Item_` nodes have no other triples anywhere.
- 133 Current Items point to more than one such node. Under OWL semantics, that makes the `Item_` nodes of different Item Parts identical to one another.

I'd suggest removing this link (`creation_rdf.py`, line 404). It is described in the shapes for now and marked SUSPECT.

**C. `crm:P14_carried_out_by_founder` / `crm:P14_carried_out_by_reformer` are not CIDOC-CRM properties.** They were minted inside the CRM namespace, and there are 31 and 14 triples respectively. The options are:
- plain `P14_carried_out_by`, with the role expressed through `P14.1 in the role of` (which needs a reified node);
- or two `archetype:` sub-properties of P14 (the pattern already used for `has_evidence_note`).

**D. `P72_has_language` on Historical Item (231 triples).** P72's domain is E33 Linguistic Object, and Historical Item isn't one. This is the same problem already flagged in the code for Text.

**E. P56 and Item Part.** P56's domain is E19 Physical Object. Under LRMoo, F5_Item is ⊑ E24, not E19. In RDFS terms this isn't an error: a reasoner would simply infer that Item Part is an E19. But it feeds into the open Item_Part / F5_Item question already noted in the ontology.

**F. 20 of the 42 shapes cannot be targeted by class** (first version; now 19 of 44 — Text and Text Copy are targetable, and the new Item Part locus shape is not). For these kinds, only the URI pattern or the node's position in the graph says what they are:
- five kinds share `E13_Attribute_Assignment` (Archive, Item origin, Owner, Hand date, Hand place);
- two kinds share `E31_Document` (Description, Hand description), with three more among the leaf nodes;
- three kinds share `E18_Physical_Thing` (Layout, Collation, Decoration);
- two kinds share `E74_Group` (Institution, Repository);
- three E55 vocabularies (Category, Historical Item type, Historical Item format);
- five kinds whose own class is a superclass of other Archetype classes (Image/E36, Date/E4, Locus/E41, Text/TX1, Text-in-Item-Part/TX7). *2026-11-15: Text (`archetype:Text`) and Text Copy (`archetype:TextCopy`) now have classes of their own and are targeted; Locus and the new Item Part locus (both E41) are still identified by their `P2_has_type` constant.*

Archive and Item origin cannot be told apart by structure at all when both assign a Place. The comment on each shape says how to recognise it. This is the strongest practical argument for more `archetype:` classes, extending the existing Layout/Collation/Decoration note in the ontology header.

**G. Constants live in the DigiPal data namespace.** Values such as `data:Type_Accepted`, `data:Type_Dubitable`, `data:Type_Locus`, `data:Category_Historical_Item` and the county/region types are part of the Archetype model itself. They are not DigiPal data. They probably belong in the SKOS vocabulary or the `archetype:` namespace, so that the profile isn't tied to DigiPal. Related to this, `data:Befor_Allograph` (misspelt) and `data:After_Allograph` are declared but never used.

**H. County types are attached to the County, not to the link.** 24 Counties carry both `Type_Current_County` and `Type_Historical_County`. As a result, the data can't say whether a given Place falls within a county as its *current* or its *historical* county. This is related to the existing note about administrative Places versus site Places.

**Minor points (no action needed now):**
- `Image —P138_represents→ Locus` means the image represents an *appellation* (the name of the folio) rather than the folio itself.
- Navigation from Idiograph to Scribe (`Idiograph ←P148— Scribal_Practice ←characterised_by— Scribe`) fails for 108 Idiographs that have no scribe. 65 Scribal Practices have no Idiographs.

## 4. Provisional choices

- The shape namespace `archsh:` = `https://w3id.org/archetype/shapes/` is a placeholder and has not been agreed.
- The file is generated by `gen_shapes.py` from the harvested edge table. The descriptions are partly hand-written in that script, so it's better to edit them there and regenerate than to edit the `.ttl` directly.

## 5. Changes since v0.1 affecting the shapes (2026-11-15) — regenerated and verified

Text modelling was revised (see `domain_range_compliance.md` §2.21). The following shapes are now out of date and will be regenerated now that the Hand and Image steps are also done (all four steps verified, see `domain_range_compliance.md` §2.21):

- **TextShape:** Text is now `archetype:Text ⊑ E33` and can be targeted by class (point F no longer applies to it). Outgoing `TXP4_has_segment` is gone; incoming `TextCopy —P128_carries→ Text` replaces it. `P72`/`P2` unchanged.
- **TextInItemPartShape → TextCopyShape:** class `archetype:TextCopy ⊑ crm-tx:TX1_Written_Text`, targetable by class. Outgoing `P128_carries → archetype:Text`; incoming `Item_Part —P46→` (always) and `Surface_Extent —P46→` (where a locus is cited). No `P1 → Locus` any more; no label (TextItemPart names never used).
- **New Surface_ExtentShape:** `archetype:Surface_Extent ⊑ E24`. Outgoing `P1_is_identified_by → Locus (E41)` and `P46_is_composed_of → TextCopy` or `→ HandInstance`; incoming `Item_Part —P46→`; incoming `Image —P138→`. 1,274 instances.
- **ItemPartShape:** outgoing `P46 → TextCopy` and `P46 → Surface_Extent` added; outgoing `P1 → E41` now includes the Item Part's own locus (typed `Type_Locus_In_Current_Item`). The cited-locus `P1` links have been removed, so `P1 → E41` now means only the Item Part's own locus. `P56 → HandInstance` is now `P46 → HandInstance`.
- **LocusShape:** every cited Locus is now named by exactly one Surface Extent (incoming `P1`) and by nothing else — no longer by Item Part, Hand Instance, Text-in-Item-Part, or (via `P138`) Image.
- **HandInstanceShape:** outgoing `P1 → Locus` removed; incoming `Item_Part —P56→` becomes `—P46→`; new incoming `Surface_Extent —P46→` (10 cases).
- **ImageShape:** outgoing `P138 → E41 (Locus)` replaced by `P138 → Surface_Extent`. This resolves the minor point in §3 ("the image represents an *appellation*").
- **Point E (P56 and Item Part):** confirmed as a real problem rather than a harmless inference, since Surface Extent (also E24) must not be inferred to be an E19. Resolved by using `P46` throughout, Hands included (0 `P56` triples remain in the export).
- **Point D / earlier note on Text:** `P72` on Text is now valid; `P72` on Historical Item remains open.

**Regeneration (2026-11-15).** `edges.json` re-harvested from `data_digipal_turtle_202611151557.rdf` with the new `harvest_edges.py` (116 edge patterns, including the dataset-metadata ones, which the generator drops); `gen_shapes.py` updated accordingly (new Surface Extent and Item Part locus kinds; Text Copy replaces Text in Item Part; Text targeted by class; descriptions and the P128 inverse name added; obsolete P56/TXP4/cited-locus descriptions removed). Result: 44 shapes, 87 outgoing, 51 incoming. Checked as in §2: **conforms, 0 violations**; closed run conforms, and with three old-style links injected as controls (`Item_Part —P56→ HandInstance`, `TextCopy —P1→ Text`, `Text —TXP4→ TextCopy`) exactly those three, and nothing else, were reported. The hand-written review comments formerly in the `.ttl` have been moved by the project lead into a TODO block at the top of `gen_shapes.py`, so they survive regeneration.
