# Archetype resource-link shapes (v0.1): generation notes and open points

Companion to `archetype_shapes_0.1.ttl`. Sources: `data_pstokes_turtle_202609222044.rdf`, `creation_rdf.py`, `archetype_ontology_0.1.ttl`.

## 1. What the file contains

- **42 node shapes.** There is one for each kind of node that has links: every `archetype:` class, plus the CRM-typed kinds such as Image, Owner, Layout and Writing. Places, Counties and Regions share a single shape, as do Foundation and Refoundation.
- **87 outgoing property shapes.** Each gives the property exactly as it is stored in the data, and the class of the node at the other end.
- **48 incoming property shapes** (`sh:inversePath`). These list the links that are stored on *another* node but point at this one. They answer "how do I get from an Idiograph back to its Graphs?"
- Controlled constants (e.g. `data:Type_Accepted`) are given as `sh:in` values rather than as a class.
- There are no cardinalities and no literal properties.

**The original P56i example.** The link is stored only as `Item_Part —P56_bears_feature→ HandInstance`. `P56i_is_found_on` never appears in the export. The same holds for every CRM inverse: without a reasoner, a SPARQL query must use the forward property with the variables swapped. The incoming shapes give the CRM inverse name only as documentation.

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

**F. 20 of the 42 shapes cannot be targeted by class.** For these kinds, only the URI pattern or the node's position in the graph says what they are:
- five kinds share `E13_Attribute_Assignment` (Archive, Item origin, Owner, Hand date, Hand place);
- two kinds share `E31_Document` (Description, Hand description), with three more among the leaf nodes;
- three kinds share `E18_Physical_Thing` (Layout, Collation, Decoration);
- two kinds share `E74_Group` (Institution, Repository);
- three E55 vocabularies (Category, Historical Item type, Historical Item format);
- five kinds whose own class is a superclass of other Archetype classes (Image/E36, Date/E4, Locus/E41, Text/TX1, Text-in-Item-Part/TX7).

Archive and Item origin cannot be told apart by structure at all when both assign a Place. The comment on each shape says how to recognise it. This is the strongest practical argument for more `archetype:` classes, extending the existing Layout/Collation/Decoration note in the ontology header.

**G. Constants live in the DigiPal data namespace.** Values such as `data:Type_Accepted`, `data:Type_Dubitable`, `data:Type_Locus`, `data:Category_Historical_Item` and the county/region types are part of the Archetype model itself. They are not DigiPal data. They probably belong in the SKOS vocabulary or the `archetype:` namespace, so that the profile isn't tied to DigiPal. Related to this, `data:Befor_Allograph` (misspelt) and `data:After_Allograph` are declared but never used.

**H. County types are attached to the County, not to the link.** 24 Counties carry both `Type_Current_County` and `Type_Historical_County`. As a result, the data can't say whether a given Place falls within a county as its *current* or its *historical* county. This is related to the existing note about administrative Places versus site Places.

**Minor points (no action needed now):**
- `Image —P138_represents→ Locus` means the image represents an *appellation* (the name of the folio) rather than the folio itself.
- Navigation from Idiograph to Scribe (`Idiograph ←P148— Scribal_Practice ←characterised_by— Scribe`) fails for 108 Idiographs that have no scribe. 65 Scribal Practices have no Idiographs.

## 4. Provisional choices

- The shape namespace `archsh:` = `https://w3id.org/archetype/shapes/` is a placeholder and has not been agreed.
- The file is generated by `gen_shapes.py` from the harvested edge table. The descriptions are partly hand-written in that script, so it's better to edit them there and regenerate than to edit the `.ttl` directly.
