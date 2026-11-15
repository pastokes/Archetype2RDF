"""Harvest every resource-to-resource triple of an Archetype export, grouped by
(subject kind, subject type, predicate, object kind, object type) -> edges.json.
Kind = the URI's local-name pattern with ids stripped; constants (no id) -> CONST:<name>;
non-DigiPal URIs -> EXT:<prefix>."""
import json, re, sys, collections
from rdflib import Graph, URIRef, RDF
DATA = "https://digipal.eu/data/"
PFX = {"http://www.cidoc-crm.org/cidoc-crm/":"crm:", "http://www.cidoc-crm.org/extensions/crmtex/":"crm-tx:",
       "https://w3id.org/archetype/ontology/":"archetype:", "http://www.w3.org/ns/oa#":"oa:",
       "http://www.w3.org/2002/07/owl#":"owl:", "http://purl.org/dc/terms/":"dcterms:",
       "http://www.w3.org/2000/01/rdf-schema#":"rdfs:", "http://www.w3.org/2004/02/skos/core#":"skos:",
       "http://xmlns.com/foaf/0.1/":"foaf:", "http://www.w3.org/ns/org#":"org:"}
def q(u):
    u=str(u)
    for k,v in PFX.items():
        if u.startswith(k): return v+u[len(k):]
    return u
SPECIAL = [  # (regex on local name, kind) -- checked before the generic rule
    (r"^Locus_Item_Part_\d+_.+$", "Locus"),
    (r"^Surface_Extent_Item_Part_\d+_.+$", "Surface_Extent"),
    (r"^Item_Part_Locus_\d+$", "Item_Part_Locus"),
    (r"^Layout_Historical_Item_\d+$", "Layout"),
    (r"^Dimension_Historical_Item_\d+_.+$", "Dimension"),
    (r"^Shelfmark_Current_Item_\d+$", "Shelfmark"),
    (r"^CatalogueNumber_.+$", "CatalogueNumber"),
]
def kind(u):
    u=str(u)
    if not u.startswith(DATA): return "EXT:"+q(u).split(":")[0]
    loc=u[len(DATA):]
    for rx,k in SPECIAL:
        if re.match(rx,loc): return k
    m=re.match(r"^(.*?)_\d+$",loc)
    return m.group(1) if m else "CONST:"+loc
g=Graph(); g.parse(sys.argv[1], format="turtle")
types=collections.defaultdict(set)
for s,o in g.subject_objects(RDF.type): types[s].add(q(o))
def typ(n):
    t=types.get(n)
    if not t: return "UNTYPED"
    # prefer archetype:/oa: class, else the single crm class
    for pref in ("archetype:","oa:","crm-tx:","crm:"):
        c=sorted(x for x in t if x.startswith(pref))
        if c: return c[0]
    return sorted(t)[0]
cnt=collections.Counter()
for s,p,o in g:
    if p==RDF.type or not isinstance(o,URIRef) or not isinstance(s,URIRef): continue
    cnt[(kind(s),typ(s),q(p),kind(o),typ(o))]+=1
json.dump([list(k)+[n] for k,n in sorted(cnt.items())], open("edges.json","w"), indent=0)
print(len(cnt),"edge patterns")
