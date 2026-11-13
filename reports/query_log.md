# SPARQL Query Log

A running record of natural-language queries posed during RDF spot-checks, paired with their SPARQL translation. Maintained silently — not shown by default each turn, only produced/updated on request or reviewed together later.

RDF source: `data_rdf_digipal_cidoc_202609041816.rdf`

---

## Entry 1

**Natural-language query:** Give me all the Hands with an ACCEPTED_TYPE Assigned Date of 's. xi1/4'.

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?hand ?handlabel ?iplabel WHERE {
  ?hd crm:P2_has_type dp:Type_Accepted .
  ?hd crm:P141_assigned dp:Date_Period_8 .          # Date_Period_8 = dc:date "Saec. xi1/4" (exact match)
  ?hd crm:P140_assigned_attribute_to ?hand .
  OPTIONAL { ?hand rdfs:label ?handlabel }
  OPTIONAL {
    ?ip crm:P56_bears_feature ?hand .
    OPTIONAL { ?ip rdfs:label ?iplabel }
  }
}
ORDER BY ?iplabel
```
Note: `Date_Period_8`'s id was first found via `SELECT ?p ?date WHERE { ?p dcterms:date ?date . FILTER(CONTAINS(LCASE(STR(?date)), "xi1/4")) }`, then the exact label "Saec. xi1/4" was picked out from several partial matches (e.g. "Saec. xi1 or xi1/4") per the user's exact-value intent.

---

## Entry 2

**Natural-language query:** Redo the same table, but this time also add the ACCEPTED_TYPE Assigned Place (if any).

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?hand ?handlabel ?iplabel (GROUP_CONCAT(DISTINCT ?placelabel; separator="; ") as ?places) WHERE {
  ?hd crm:P2_has_type dp:Type_Accepted .
  ?hd crm:P141_assigned dp:Date_Period_8 .
  ?hd crm:P140_assigned_attribute_to ?hand .
  OPTIONAL { ?hand rdfs:label ?handlabel }
  OPTIONAL {
    ?ip crm:P56_bears_feature ?hand .
    OPTIONAL { ?ip rdfs:label ?iplabel }
  }
  OPTIONAL {
    ?hp crm:P2_has_type dp:Type_Accepted .
    ?hp crm:P140_assigned_attribute_to ?hand .
    ?hp crm:P141_assigned ?place .
    ?place a crm:E53_Place .                        # constraint added after first draft caught a bug (see note)
    ?place rdfs:label ?placelabel .
  }
}
GROUP BY ?hand ?handlabel ?iplabel
ORDER BY ?iplabel
```
Note: first draft omitted `?place a crm:E53_Place`, so it matched *any* `Type_Accepted` attribute-assignment for the "place" slot — including the HandDate itself, causing "Date 8" to wrongly appear as a place for several rows. Caught and fixed before presenting results; logged here as a reusable caution for future Place-via-`Type_Accepted` queries.

---

## Entry 3

**Natural-language query:** Count of Hands grouped by ACCEPTED_TYPE Place, where the Hands are associated with at least one Graph of Character 'æ' with Component 'eye' being 'high' or 'bulging' (or both).

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?placelabel (COUNT(DISTINCT ?hand) as ?nhands) WHERE {
  ?hp crm:P2_has_type dp:Type_Accepted .
  ?hp crm:P140_assigned_attribute_to ?hand .
  ?hp crm:P141_assigned ?place .
  ?place a crm:E53_Place .
  ?place rdfs:label ?placelabel .

  ?hand crm:P46_is_composed_of ?graph .
  ?graph crm:P65_shows_visual_item ?idio .
  ?idio crm:P138_represents ?allo .
  ?allo crm:P138_represents dp:Character_18 .        # æ

  ?graph crm:P46_is_composed_of ?gc .
  ?gc crm:P138_represents dp:Component_15 .          # eye
  ?gc crm:P2_has_type ?feat .
  FILTER(?feat IN (dp:Feature_52, dp:Feature_24))    # high, bulging
}
GROUP BY ?placelabel
ORDER BY DESC(?nhands)
```
Result: 94 distinct Hands across 26 Place values (Worcester and Unknown tied at 17 each). Reused the `?place a crm:E53_Place` guard from Entry 2 to avoid the same false-Place bug.

---
## Entry 4

**Natural-language query:** Table of the number of Graphs grouped by ACCEPTED_TYPE Date of the associated Hand.

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?datelabel (COUNT(?graph) as ?ngraphs) WHERE {
  ?hd crm:P2_has_type dp:Type_Accepted .
  ?hd crm:P140_assigned_attribute_to ?hand .
  ?hd crm:P141_assigned ?period .
  ?period a crm:E4_Period .
  ?period dcterms:date ?datelabel .

  ?hand crm:P46_is_composed_of ?graph .
}
GROUP BY ?datelabel
ORDER BY DESC(?ngraphs)
```
Result: 41 distinct date labels, 63,539 Graphs total (of 64,028 overall — remainder belong to Hands lacking an ACCEPTED-type Period).

---
## Entry 5

**Natural-language query:** List of all Hands which do not have an ACCEPTED_TYPE Date. Give any other (non-Accepted) Dates if they have any.

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?hand ?handlabel ?iplabel ?typelabel ?datelabel WHERE {
  ?hand a <https://digipal.eu/Hand> .
  FILTER NOT EXISTS {
    ?hd crm:P2_has_type dp:Type_Accepted .
    ?hd crm:P140_assigned_attribute_to ?hand .
    ?hd crm:P141_assigned ?p .
  }
  OPTIONAL { ?hand rdfs:label ?handlabel }
  OPTIONAL { ?ip crm:P56_bears_feature ?hand . OPTIONAL {?ip rdfs:label ?iplabel} }
  OPTIONAL {
    ?hd2 crm:P140_assigned_attribute_to ?hand .
    ?hd2 crm:P2_has_type ?type .
    ?hd2 crm:P141_assigned ?period .
    ?period a crm:E4_Period .
    OPTIONAL {?type rdfs:label ?typelabel}
    ?period dcterms:date ?datelabel .
  }
}
ORDER BY ?iplabel
```
Result: 139 Hands with no ACCEPTED date; verified none of them have any HandDate assignment at all (accepted or otherwise) via a follow-up existence check. Spans 102 manuscripts, skews heavily toward Latin-only hands. Surfaced two follow-on findings logged in the main report: `Hand_1351`/`Hand_1352` missing `rdfs:label` (§1.6), and the Latin-hand dating gap plus a semi-automatic-completion idea (§2.4).

---
## Entry 6

**Natural-language query:** Are there any Historical Items where the Type is not 'Charter' that contain Hands that have Accepted attributions to a Place containing 'Central Production'?

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?hi ?type ?typelabel WHERE {
  ?hp crm:P2_has_type dp:Type_Accepted .
  ?hp crm:P141_assigned dp:Place_135 .              # only Place matching "Central Production"
  ?hp crm:P140_assigned_attribute_to ?hand .
  ?hand a <https://digipal.eu/Hand> .                # guard: HandPlace-type nodes can target non-Hand entities too

  ?ip crm:P56_bears_feature ?hand .
  ?hi crm:P46_is_composed_of ?ip .
  ?hi a <https://digipal.eu/Historical_Item> .

  OPTIONAL { ?hi crm:P2_has_type ?type . ?type a crm:E55_Type . OPTIONAL {?type rdfs:label ?typelabel} }
}
```
Result: 68 Hands → 59 distinct Historical Items, all typed "charter" (none "manuscript", none untyped). Answer: no non-charter Historical Items exist in this set. Note: only two `Historical_Item_Type` values exist in the whole dataset (charter, manuscript).

---
## Entry 7

**Natural-language query:** How many Attribute Assignments of type DUBITABLE are documented in Documents containing the string 'Dumville'?

**SPARQL (final, correctly scoped):**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>

SELECT DISTINCT ?doc WHERE {
  { ?period a crm:E4_Period . ?period crm:P70i_is_documented_in ?doc . }
  UNION
  { ?scribe a <https://digipal.eu/Scribe> . ?scribe crm:P70i_is_documented_in ?doc . }
  ?doc ?p ?o .
  FILTER(isLiteral(?o) && CONTAINS(STR(?o), "Dumville"))
}
```
Result: **0**. First attempt searched all `E31_Document` content broadly and found many "Dumville" hits, but those live on `Description_N` documents attached directly to `Historical_Item`s (bibliography notes) — a structurally separate part of the schema, unreachable from `Type_Dubitable` attribute assignments. Correctly scoping to the actual `P70i_is_documented_in` chain from `E4_Period`/`Scribe` (the only two classes that carry this predicate — notably `E53_Place` does not, so Dubitable HandPlace assignments have no Document path at all) showed only 172 reachable Documents, of which just 7 have any content at all. Logged as §1.7 in the main report — flagged for review, not confirmed as an error.

---
## Entry 8

**Natural-language query:** For all Hands which produced at least one Graph with Component 'Ascender' and Feature 'long', what proportion have gloss_only 'TRUE'?

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>

SELECT DISTINCT ?hand ?glossonly WHERE {
  ?hand crm:P46_is_composed_of ?graph .
  ?graph crm:P46_is_composed_of ?gc .
  ?gc crm:P138_represents dp:Component_4 .      # ascender
  ?gc crm:P2_has_type dp:Feature_69 .           # long
  OPTIONAL { ?hand dp:gloss_only ?glossonly }
}
```
Result: 9 distinct Hands; all 9 have `gloss_only = false`. Proportion true: 0%.

Preceding this, a related query ("Hands with type GLOSSED TEXT") turned up no matching resource anywhere in the RDF — logged as §1.8 in the main report (Peter: likely a misremembering of the actual vocabulary, not a data gap).

---
## Entry 9

**Natural-language query:** All Repositories located in Cambridge which hold at least one Current Item.

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?repo ?repolabel (COUNT(DISTINCT ?ci) as ?nitems) WHERE {
  ?repo crm:P74_has_current_or_former_residence ?place .
  ?place rdfs:label ?placelabel .
  FILTER(LCASE(STR(?placelabel)) = "cambridge")
  ?repo rdfs:label ?repolabel .
  ?ci crm:P50_has_current_keeper ?repo .
  ?ci a <https://digipal.eu/Current_Item> .
}
GROUP BY ?repo ?repolabel
ORDER BY ?repolabel
```
Result: 14 Repositories, 227 Current Items total. Only one Place labeled exactly "Cambridge" exists (no ambiguity to resolve, unlike the earlier Worcester/York case).

---
## Entry 10

**Natural-language query:** What percentage of Historical Items have corresponding Current Items in London and have Collation where fragment=true? (Clarified: denominator is Historical Items with a London Current Item; numerator is the subset of those with a fragment=true Collation.)

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>

# Denominator
SELECT DISTINCT ?hi WHERE {
  ?hi a <https://digipal.eu/Historical_Item> .
  ?hi crm:P46_is_composed_of ?ip .
  ?ci crm:P46_is_composed_of ?ip .
  ?ci a <https://digipal.eu/Current_Item> .
  ?ci crm:P50_has_current_keeper ?repo .
  ?repo crm:P74_has_current_or_former_residence dp:Place_38 .   # London
}

# Numerator: add
  ?hi crm:P46_is_composed_of ?coll .
  ?coll dp:fragment "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
```
Path: `Historical_Item → P46_is_composed_of → Item_Part ← P46_is_composed_of ← Current_Item → P50_has_current_keeper → Repository → P74_has_current_or_former_residence → Place_38 ("London")`, joined with `Historical_Item → P46_is_composed_of → Collation` (an `E18_Physical_Thing` typed `Collation` via `P2_has_type`, carrying `dp:fragment` boolean and `dp:leaves` integer literals).

Result: 497 Historical Items have a London Current Item; 26 of those have a fragment=true Collation → **5.23%**. (Of all 1,553 Historical Items, this would be 1.67% — noted but not the intended denominator.)

---
## Entry 11

**Natural-language query:** How many fragmentary Historical Items (i.e. Historical Items which have Collation fragment=true) show more than one Hand?

**SPARQL:**
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dp: <http://digipal.eu/ontology#>

SELECT ?hi (COUNT(DISTINCT ?hand) as ?n) WHERE {
  ?hi a <https://digipal.eu/Historical_Item> .
  ?hi crm:P46_is_composed_of ?coll .
  ?coll dp:fragment "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
  ?hi crm:P46_is_composed_of ?ip .
  ?ip crm:P56_bears_feature ?hand .
}
GROUP BY ?hi
```
(then filter rows where ?n > 1)

Result: 57 total fragmentary Historical Items; 48 have at least one Hand recorded; of those, **17** have more than one distinct Hand. The remaining 9 fragmentary Historical Items have no Hand recorded at all.

---
