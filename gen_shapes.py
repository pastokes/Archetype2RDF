"""Generate a descriptive SHACL application profile from the harvested edge table (edges.json)
plus edges emitted by creation_rdf.py that have no data in the DigiPal export."""
import json, collections

edges = json.load(open("edges.json"))  # [skind, stype, pred, okind, otype, count]
edges = [e for e in edges if not e[0].startswith("EXT:")]  # drop dataset-metadata triples

CODE_ONLY = [  # emitted by creation_rdf.py but unpopulated in DigiPal
    ["Item_Part", "archetype:Item_Part", "crm:P46_is_composed_of", "Layout", "crm:E18_Physical_Thing", 0],
    ["Item_Part", "archetype:Item_Part", "crm:P43_has_dimension", "Dimension", "crm:E54_Dimension", 0],
    ["Owner", "crm:E13_Attribute_Assignment", "crm:P141_assigned", "Person", "crm:E21_Person", 0],
    ["Owner", "crm:E13_Attribute_Assignment", "crm:P141_assigned", "Institution", "crm:E74_Group", 0],
]
edges += CODE_ONLY

ALIAS = {"County": "Place", "Region": "Place", "InstiFoundation": "Formation", "InstiRefoundation": "Formation"}
def K(k): return ALIAS.get(k, k)

# kind -> (label, targetClass or None, identification comment, group)
G1, G2, G3, G4, G5, G6 = ("Palaeographic core: letters, graphs, components",
    "Hands, scribes and writing", "Manuscripts: items, parts and physical description",
    "Images, annotations and texts", "Attributions (E13) and dates",
    "Agents, places and documentation")
KINDS = {
 "Character": ("Character", "archetype:Character", None, G1),
 "Allograph": ("Allograph", "archetype:Allograph", None, G1),
 "Idiograph": ("Idiograph", "archetype:Idiograph", None, G1),
 "Graph": ("Graph", "archetype:Graph", None, G1),
 "GraphComponent": ("Graph Component", "archetype:GraphComponent", None, G1),
 "IdiographComponent": ("Visual Component", "archetype:VisualComponent", "Instances currently all come from the idiographcomponent table (URIs data:IdiographComponent_<id>).", G1),
 "GenericComponent": ("Generic Component", "archetype:GenericComponent", None, G1),
 "Feature": ("Feature", "archetype:Feature", None, G1),
 "Ontograph": ("Ontograph", "archetype:Ontograph", None, G1),
 "HandInstance": ("Hand Instance", "archetype:HandInstance", None, G2),
 "Writing": ("Writing event", "crm-tx:TX2_Writing", "One Writing per Hand Instance (URIs data:Writing_<hand id>).", G2),
 "Scribe": ("Scribe", "archetype:Scribe", None, G2),
 "Scribal_Practice": ("Scribal Practice", "archetype:Scribal_Practice", None, G2),
 "Appearance": ("Appearance", "archetype:Appearance", None, G2),
 "Historical_Item": ("Historical Item", "archetype:Historical_Item", None, G3),
 "Item_Part": ("Item Part", "archetype:Item_Part", None, G3),
 "Current_Item": ("Current Item", "archetype:Current_Item", None, G3),
 "Layout": ("Layout", None, "Typed only crm:E18_Physical_Thing (shared with Collation and Decoration); identified by URI data:Layout_Historical_Item_<id>, or as the E18 that a Historical Item is composed of and that has no P2_has_type.", G3),
 "Collation": ("Collation", None, "Typed only crm:E18_Physical_Thing; identified by crm:P2_has_type data:Collation.", G3),
 "Decoration": ("Decoration", None, "Typed only crm:E18_Physical_Thing; identified by crm:P2_has_type data:Decoration.", G3),
 "Dimension": ("Dimension", "crm:E54_Dimension", None, G3),
 "Locus": ("Locus", None, "Typed crm:E41_Appellation (not targeted by class because crm:E42_Identifier is a subclass of E41); identified by crm:P2_has_type data:Type_Locus. One Locus node per (Item Part, locus string), shared by any Image, Hand Instance or Text-in-Item-Part that cites the same locus.", G3),
 "Image": ("Image", None, "Typed only crm:E36_Visual_Item (not targeted by class because Idiograph, Allograph, Character, VisualComponent etc. are all subclasses of E36); identified as the target of an oa:Annotation, or by URI data:Image_<id>.", G4),
 "Annotation": ("Annotation", "oa:Annotation", None, G4),
 "Text": ("Text", None, "Typed crm-tx:TX1_Written_Text (not targeted by class because TX7, and so Hand Instance and Graph, are subclasses of TX1 in CRMtex). Typing as TX1 is already flagged in creation_rdf.py as wrong (should be a conceptual text, e.g. E33).", G4),
 "Text_Item_part": ("Text in Item Part", None, "Typed crm-tx:TX7_Written_Text_Segment (not targeted by class because Hand Instance and Graph are also TX7); identified as the object of crm-tx:TXP4_has_segment from a Text.", G4),
 "HandDate": ("Hand date attribution", None, "Typed only crm:E13_Attribute_Assignment (shared with Hand place, Item origin, Archive and Owner); identified as an E13 whose P140 is a Hand Instance and whose P141 is an E4_Period.", G5),
 "HandPlace": ("Hand place attribution", None, "Typed only crm:E13_Attribute_Assignment; identified as an E13 whose P140 is a Hand Instance and whose P141 is an E53_Place.", G5),
 "ItemOrigin": ("Item origin attribution", None, "Typed only crm:E13_Attribute_Assignment; identified as an E13 whose P140 is a Historical Item (URIs data:ItemOrigin_<id>; indistinguishable by structure from Archive when P141 is a Place).", G5),
 "Archive": ("Archive attribution", None, "Typed only crm:E13_Attribute_Assignment; identified as an E13 whose P140 is a Historical Item (URIs data:Archive_<id>; indistinguishable by structure from Item origin).", G5),
 "Owner": ("Ownership attribution", None, "Typed only crm:E13_Attribute_Assignment; identified as an E13 whose P140 is an Item Part. Records an assertion of ownership, not the owner itself.", G5),
 "Date_Period": ("Date", None, "Typed crm:E4_Period (not targeted by class because every E5 Event, e.g. Writing, Formation and E13 Attribute Assignment, is a subclass of E4); URIs data:Date_Period_<id>.", G5),
 "Date_Time_Span": ("Date time-span", "crm:E52_Time-Span", None, G5),
 "Institution": ("Institution", None, "Typed only crm:E74_Group (shared with Repository); URIs data:Institution_<id>.", G6),
 "Repository": ("Repository", None, "Typed only crm:E74_Group (shared with Institution); identified as the object of crm:P50_has_current_keeper, or by URI data:Repository_<id>.", G6),
 "Formation": ("Institution foundation / refoundation", "crm:E66_Formation", "Two kinds of node share this shape, distinguished by P2_has_type data:Type_Fondation or data:Type_Refondation.", G6),
 "Place": ("Place", "crm:E53_Place", "Covers three kinds of node with no class distinction: site-level Places (data:Place_<id>), Counties (data:County_<id>) and Regions (data:Region_<id>).", G6),
 "Description": ("Description (of Historical Item or Text)", None, "Typed only crm:E31_Document (shared with Hand description, Source, Reference, Date evidence); URIs data:Description_<id>.", G6),
 "HandDescription": ("Hand description", None, "Typed only crm:E31_Document; identified as an E31 with crm:P67_refers_to a Hand Instance.", G6),
 "Category": ("Category", None, "Typed only crm:E55_Type; identified by crm:P2_has_type data:Category_Historical_Item. Used for Historical Items, Texts and (as glossed text) Hand Instances.", G6),
 "Historical_Item_Type": ("Historical Item type", None, "Typed only crm:E55_Type; identified by crm:P2_has_type data:TYPE_Historical_Item.", G6),
 "Historical_Item_Format": ("Historical Item format", None, "Typed only crm:E55_Type; identified by crm:P2_has_type data:Type_Format.", G6),
}
LEAF_LABEL = {
 "Language": "Language", "Hair": "Hair arrangement (E57 Material)", "MediaPermission": "Media permission (E30 Right)",
 "Shelfmark": "Shelfmark (E42 Identifier)", "CatalogueNumber": "Catalogue number (E42 Identifier)",
 "Person": "Person (E21)", "LatinStyle": "Latin Style (TX10 Style)", "Script": "Script (TX10 Style)",
 "Status": "Annotation status (E55 Type)", "InstitutionType": "Institution type (E55 Type)",
 "RepositoryType": "Repository type (E55 Type)", "FormCharacter": "Character form (E55 Type)",
 "OntographType": "Ontograph type (E55 Type)", "Source": "Source (E31 Document)",
 "Reference": "Reference (E31 Document)", "Date_Document": "Date evidence document (E31 Document)",
 "Item": "data:Item_<id> (untyped)",
}
def label(k):
    k = K(k)
    if k in KINDS: return KINDS[k][0]
    if k.startswith("CONST:"): return "data:" + k[6:]
    return LEAF_LABEL[k]

INVERSE = {  # CIDOC-CRM inverse property names, for documentation only (not materialised in the export)
 "P1_is_identified_by": "P1i_identifies", "P2_has_type": "P2i_is_type_of", "P4_has_time-span": "P4i_is_time-span_of",
 "P14_carried_out_by": "P14i_performed", "P33_used_specific_technique": "P33i_was_specific_technique_of",
 "P43_has_dimension": "P43i_is_dimension_of", "P45_consists_of": "P45i_is_incorporated_in",
 "P46_is_composed_of": "P46i_forms_part_of", "P50_has_current_keeper": "P50i_is_current_keeper_of",
 "P56_bears_feature": "P56i_is_found_on", "P65_shows_visual_item": "P65i_is_shown_by",
 "P67_refers_to": "P67i_is_referred_to_by", "P70_documents": "P70i_is_documented_in",
 "P70i_is_documented_in": "P70_documents", "P72_has_language": "P72i_is_language_of",
 "P74_has_current_or_former_residence": "P74i_is_current_or_former_residence_of", "P89_falls_within": "P89i_contains",
 "P91_has_unit": "P91i_is_unit_of", "P95_has_formed": "P95i_was_formed_by", "P104_is_subject_to": "P104i_applies_to",
 "P107_has_current_or_former_member": "P107i_is_current_or_former_member_of", "P108_has_produced": "P108i_was_produced_by",
 "P138_represents": "P138i_has_representation", "P140_assigned_attribute_to": "P140i_was_attributed_by",
 "P141_assigned": "P141i_was_assigned_by", "P148_has_component": "P148i_is_component_of",
}

NOTES = {
 ("Allograph", "crm:P138_represents", "Character"): "The Character of which this Allograph is a form.",
 ("Allograph", "crm:P148_has_component", "GenericComponent"): "Type level: the Components this Allograph is made up of (no Features recorded at this level).",
 ("Character", "crm:P138_represents", "Ontograph"): "The Ontograph this Character belongs to.",
 ("Character", "crm:P148_has_component", "GenericComponent"): "Type level: the Components this Character is made up of.",
 ("Idiograph", "crm:P138_represents", "Allograph"): "The Allograph of which this Idiograph is one scribe's realisation.",
 ("Idiograph", "crm:P148_has_component", "IdiographComponent"): "The Visual Components (component + features) recorded for this Idiograph.",
 ("IdiographComponent", "crm:P138_represents", "GenericComponent"): "The generic Component this Visual Component realises.",
 ("IdiographComponent", "crm:P2_has_type", "Feature"): "The Features recorded on this component of the Idiograph.",
 ("Graph", "crm:P65_shows_visual_item", "Idiograph"): "The Idiograph of which this physical Graph is an instance. Continue Idiograph -P138-> Allograph -P138-> Character.",
 ("Graph", "crm:P46_is_composed_of", "GraphComponent"): "The physical components (ascender, minim, etc.) annotated on this Graph.",
 ("GraphComponent", "crm:P65_shows_visual_item", "GenericComponent"): "The generic Component this physical component shows.",
 ("GraphComponent", "crm:P2_has_type", "Feature"): "The Features observed on this component of this Graph.",
 ("GenericComponent", "crm:P2_has_type", "Feature"): "The Features this Component MAY bear (the permitted-feature list from component_features), not Features observed on any Graph.",
 ("HandInstance", "crm:P46_is_composed_of", "Graph"): "The Graphs written in this Hand Instance.",
 ("HandInstance", "crm:P2_has_type", "Appearance"): "Appearance of the hand.",
 ("HandInstance", "crm:P2_has_type", "Category"): "Glossed-text category (from Hand.glossed_text_id).",
 ("HandInstance", "crm:P1_is_identified_by", "Locus"): "Locus of the hand within its Item Part.",
 ("Writing", "crm:P108_has_produced", "HandInstance"): "The Hand Instance produced by this Writing. Scribe, Script and Latin Style hang off the Writing, not the Hand Instance: HandInstance <-P108- Writing -P14-> Scribe.",
 ("Writing", "crm:P14_carried_out_by", "Scribe"): "The Scribe who carried out this Writing.",
 ("Writing", "crm:P33_used_specific_technique", "Script"): "Script and Latin Style as techniques of the Writing (deliberately not CRMtex TXP12_has_style on the Hand Instance; see creation_rdf.py).",
 ("Scribe", "archetype:characterised_by", "Scribal_Practice"): "The Scribe's Scribal Practice, which groups the Scribe's Idiographs: Scribe -characterised_by-> Scribal_Practice -P148-> Idiograph.",
 ("Scribe", "crm:P70i_is_documented_in", "Reference"): "Bibliographic References for this Scribe.",
 ("Scribal_Practice", "crm:P148_has_component", "Idiograph"): "The Idiographs that make up this Scribe's practice.",
 ("Item_Part", "crm:P56_bears_feature", "HandInstance"): "The Hand Instances found on this Item Part.",
 ("Item_Part", "crm:P1_is_identified_by", "Locus"): "Every Locus cited within this Item Part (by Images, Hand Instances or Texts).",
 ("Item_Part", "crm:P46_is_composed_of", "Layout"): "Emitted by creation_rdf.py when Layout.item_part_id is set; not populated in DigiPal (Layout attaches to Historical Item there).",
 ("Item_Part", "crm:P43_has_dimension", "Dimension"): "Emitted by creation_rdf.py when Layout.item_part_id is set; not populated in DigiPal.",
 ("Historical_Item", "crm:P46_is_composed_of", "Item_Part"): "The Item Parts that make up this Historical Item.",
 ("Current_Item", "crm:P46_is_composed_of", "Item_Part"): "The Item Parts now bound in this Current Item.",
 ("Current_Item", "owl:sameAs", "Item"): "SUSPECT: points to data:Item_<item part id>, a node with no other triples; see note.",
 ("Current_Item", "crm:P50_has_current_keeper", "Repository"): "The Repository that holds this Current Item.",
 ("Annotation", "oa:hasBody", "Graph"): "The Graph this annotation records.",
 ("Annotation", "oa:hasTarget", "Image"): "The Image on which the annotation is drawn.",
 ("Image", "crm:P138_represents", "Item_Part"): "The Item Part shown in this Image.",
 ("Image", "crm:P138_represents", "HandInstance"): "The Hand Instances visible in this Image (from hand_images).",
 ("Image", "crm:P138_represents", "Locus"): "The locus (folio/page) shown in this Image.",
 ("HandDate", "crm:P140_assigned_attribute_to", "HandInstance"): "Accepted date of a Hand Instance: HandInstance <-P140- HandDate -P141-> Date.",
 ("HandPlace", "crm:P140_assigned_attribute_to", "HandInstance"): "Accepted place of a Hand Instance: HandInstance <-P140- HandPlace -P141-> Place.",
 ("Owner", "crm:P140_assigned_attribute_to", "Item_Part"): "The Item Part whose ownership is asserted.",
 ("Owner", "crm:P141_assigned", "Repository"): "The owner. Person and Institution owners are emitted by creation_rdf.py but not populated in DigiPal.",
 ("ItemOrigin", "crm:P141_assigned", "Place"): "The place (or institution) of origin.",
 ("Archive", "crm:P141_assigned", "Place"): "The archive's place.",
 ("Institution", "crm:P107_has_current_or_former_member", "Scribe"): "Scribes of this Institution (scriptorium).",
 ("Formation", "crm:P14_carried_out_by_founder", "Person"): "NOT A CIDOC-CRM PROPERTY: see note.",
 ("Formation", "crm:P14_carried_out_by_reformer", "Person"): "NOT A CIDOC-CRM PROPERTY: see note.",
 ("Date_Period", "crm:P70i_is_documented_in", "Date_Document"): "The node carrying the evidence note for this date.",
 ("Description", "crm:P70i_is_documented_in", "Source"): "The Source this description comes from.",
 ("HandDescription", "crm:P67_refers_to", "HandInstance"): "The Hand Instance described.",
 ("Text", "crm-tx:TXP4_has_segment", "Text_Item_part"): "The occurrences of this Text in particular Item Parts.",
}

# ---- build outgoing and incoming groupings ----
out = collections.defaultdict(lambda: collections.defaultdict(list))  # skind -> pred -> [(okind, otype, n)]
inc = collections.defaultdict(lambda: collections.defaultdict(list))  # okind -> pred -> [(skind, stype, n)]
for sk, st, p, ok, ot, n in edges:
    sk, ok = K(sk), K(ok)
    if sk not in KINDS:
        raise SystemExit(f"no shape for subject kind {sk}")
    out[sk][p].append((ok, ot, n))
    if ok in KINDS:
        inc[ok][p].append((sk, st, n))

def uniq(xs):
    seen, r = set(), []
    for x in xs:
        if x not in seen: seen.add(x); r.append(x)
    return r

def value_constraint(vals):
    kinds = uniq(v[0] for v in vals)
    if all(k.startswith("CONST:") for k in kinds):
        return "sh:in ( " + " ".join("data:" + k[6:] for k in kinds) + " )"
    if any(k.startswith("CONST:") for k in kinds):
        raise SystemExit(f"mixed constants/classes {kinds}")
    types = uniq(v[1] for v in vals)
    if types == ["UNTYPED"]:
        return "sh:nodeKind sh:IRI"
    if len(types) == 1:
        return f"sh:class {types[0]}"
    return "sh:or ( " + " ".join(f"[ sh:class {t} ]" for t in types) + " )"

def esc(s): return s.replace("\\", "\\\\").replace('"', '\\"')

def local(p): return p.split(":", 1)[1]

L = []
L.append("""@prefix sh:        <http://www.w3.org/ns/shacl#> .
@prefix archetype: <https://w3id.org/archetype/ontology/> .
@prefix archsh:    <https://w3id.org/archetype/shapes/> .
@prefix crm:       <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix crm-tx:    <http://www.cidoc-crm.org/extensions/crmtex/> .
@prefix oa:        <http://www.w3.org/ns/oa#> .
@prefix owl:       <http://www.w3.org/2002/07/owl#> .
@prefix rdfs:      <http://www.w3.org/2000/01/rdf-schema#> .
@prefix data:      <https://digipal.eu/data/> .

#################################################################
# Archetype application profile: resource links (SHACL) — draft v0.1
#
# DESCRIPTIVE, not a validation suite. Each NodeShape lists, for one
# kind of node in the Archetype RDF export, which property leads to
# which other kind of node — i.e. "what path do I follow from X to Y".
# No cardinalities are asserted.
#
# Generated from:
#   - data_pstokes_turtle_202609222044.rdf (every resource-to-resource
#     triple, grouped by subject kind / property / object kind);
#   - creation_rdf.py (links the code can emit but which have no
#     DigiPal data: marked "not populated in DigiPal");
#   - archetype_ontology_0.1.ttl (class names).
# Literal-valued properties are deliberately out of scope for this pass.
#
# Reading the shapes:
#   - "Outgoing" property shapes: sh:path is the property as it appears
#     in the data, from this node to the other.
#   - "Incoming" property shapes use sh:inversePath: the triple is stored
#     on the OTHER node, pointing at this one. The export materialises
#     only the forward property, so a SPARQL query must use the forward
#     property with the variables swapped (e.g. ?itempart
#     crm:P56_bears_feature ?hand), NOT the CRM inverse (P56i_is_found_on),
#     unless a reasoner is used. The CRM inverse name is given in the
#     description for reference only.
#   - Shapes carry sh:targetClass only where the Archetype node kind has
#     a class of its own that no other kind shares (directly or through
#     a subclass). Kinds that share a generic CRM class (e.g. the five
#     kinds of crm:E13_Attribute_Assignment) have no target; their
#     rdfs:comment says how to recognise them.
#   - Constants such as data:Type_Accepted are DigiPal data URIs; see
#     the accompanying note.
#
# Namespace archsh: is PROVISIONAL (not yet agreed).
#################################################################

<https://w3id.org/archetype/shapes/>
    a owl:Ontology ;
    rdfs:label "Archetype application profile — resource links (draft)"@en ;
    owl:versionInfo "0.1" ;
    owl:imports <https://w3id.org/archetype/ontology/0.1/> .
""")

def shape_name(k):
    return "archsh:" + KINDS[k][0].title().replace(" ", "").replace("(", "").replace(")", "").replace("/", "Or").replace("-", "") .replace(",", "") + "Shape"

group_order = [G1, G2, G3, G4, G5, G6]
stats = collections.Counter()
for grp in group_order:
    L.append(f"\n#################################################################\n# {grp}\n#################################################################\n")
    for k, (lab, tgt, ident, g) in KINDS.items():
        if g != grp: continue
        L.append(f"{shape_name(k)}\n    a sh:NodeShape ;")
        if tgt: L.append(f"    sh:targetClass {tgt} ;")
        L.append(f'    rdfs:label "{esc(lab)}"@en ;')
        if ident: L.append(f'    rdfs:comment "{esc(ident)}"@en ;')
        props = []
        for p, vals in sorted(out[k].items()):
            okinds = uniq(v[0] for v in vals)
            descr = f"Outgoing: {lab} -{local(p)}-> " + " or ".join(label(o) for o in okinds) + "."
            notes = uniq(NOTES[(k, p, o)] for o in okinds if (k, p, o) in NOTES)
            unpop = [label(o) for o in okinds if all(v[2] == 0 for v in vals if v[0] == o)]
            if notes: descr += " " + " ".join(notes)
            if unpop and not any("not populated" in n for n in notes):
                descr += " Not populated in DigiPal: " + ", ".join(unpop) + "."
            props.append(f'    sh:property [\n        sh:path {p} ;\n        {value_constraint(vals)} ;\n        sh:description "{esc(descr)}"@en\n    ]')
            stats["out"] += 1
        for p, vals in sorted(inc[k].items()):
            skinds = uniq(v[0] for v in vals)
            inv = INVERSE.get(local(p))
            descr = f"Incoming: " + " or ".join(label(s) for s in skinds) + f" -{local(p)}-> this {lab}."
            if inv: descr += f" (CRM inverse {inv}; not materialised in the export.)"
            types = uniq(v[1] for v in vals)
            c = f"sh:class {types[0]}" if len(types) == 1 else "sh:or ( " + " ".join(f"[ sh:class {t} ]" for t in types) + " )"
            props.append(f'    sh:property [\n        sh:path [ sh:inversePath {p} ] ;\n        {c} ;\n        sh:description "{esc(descr)}"@en\n    ]')
            stats["in"] += 1
        L.append(" ;\n".join(props) + " .\n" if props else "    .\n")
        stats["shapes"] += 1

open("archetype_shapes_0.1.ttl", "w").write("\n".join(L))
print(dict(stats))
