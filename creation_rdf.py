# PAS changes:
# HistoricalItem -> Historical Item (etc) for RDF output
#   Also CurrentItem, ItemPart
# consits_of -> consists_of
# Human Made -> Human-Made, Time-Span etc
# digipal.huma-num.fr -> digipal.eu
# F3 Item -> F5 Item (one occurrence)
# existance -> existence (one occurrence)
# Fixed direction of text_item / text link: text_item is a segment of the text, so the text should have the segment, not the other way around.
# Added lines to include text type and language links for Text entities (missing in original code)
# allographcomponent and character_component relationships fixed to use P148_has_component (not P65_shows_visual_item)
# IdiomCat removed since it is not used in practice by Archetype. All references to IdiomCat have been commented out.
# ItemPart generation fixed to include correct link to Hand: g.add((itempart_uri, CRM['P56_bears_feature'], hand_uri))
#.   NB that Hand is a CRMtx.TX7_Written_Text_Segment, not a CRM.E36_Visual_Item, so the link is P56_bears_feature, not P65_shows_visual_item)
#   NB also that Hand is linked directly to Item Part, not via Writing, for the same reason: the mark on a surface is directly connected to the material object,
#      whereas in some sense the writing as activity results in the Hand, and so is in a sense intermediate between the Hand and the Item Part.
# Numerous changes to Hand, including reintroducing Writing and Scribe, and moving assigned date/place to Hand level (via E13 Attribute Assignment) rather than Writing level.
# Numerous changes in modeling of digipal_description table
# Historicalitem.date changed to text literal, historicalitem.date changed to Attribute Assignment
# Archive origin, MSOrigin and ItemOrigin all migrated onto E13 Attribute Assignment
# Systematically wrapped all ID/FK values in int() to avoid problems with generating different IDs, one int and one float (e.g. Date_1 and Date_1.0)
#.  Also wrapped integer values in str() when creating URIs, to avoid problems with NaN values (which are floats) in some columns that are typed as int64.
# Layout and Dimension corrected to point to Historical Item, not Item Part.
#.  Item Part loop is preserved as a fallback for other Archetype-based projects that may use it, but the URI naming should be changed accordingly if implemented.
#.  Also added check to filter out considerable number of empty rows in digipal_layout table, to avoid adding a relatively large number of empty Layout triples to the RDF.
#   NB also that inspection of the DigiPal data shows that the on_top_line field is always FALSE, even though 
#   for the period in DigiPal it should be always TRUE. Since it is not used in any other project to my knowledge,
#   it has been removed entirely from the export.
# Fixed Repository -> MediaPermission to apply to each Image directly (otherwise we're saying the Repository has copyright of itself!).
# Temporary change of Owner -> Repository relationship to sameAs, pending revision of the Owner[ship] model (see below).
# Added timestamp to filename. NB assumes that the script is always run with at least a minute between runs, otherwise the filename will be the same and the file will be overwritten.
# Fixed issue with Appearance being conflated with Script: added new Appearance class and linked to Hand via P2_has_type. Appearance is now used for the appearance of a Hand, and Script is used for the Writing activity.
#.  Also fixed hand.script to associate with Writing (activity), and removed Writing System which was a misunderstanding of the data model.
#.  Likewise for Latin Style, since this is more or less formalised at the same level of hand.script.
#   TODO: Should unify the treatment of Latin and English in regard to arch:Script, arch:Style and arch:Appearance, and explicitly define relatinship between LatinStyle and Script.
# Added missing export of digipal_script and historical_item_type tables
# Fixed handling of CurrentCounty (since both CurrentCounty and HistoricalCounty point to the same County table so should use a single County class)
# TODO: should really change everything to braket notation for consistency
# TODO: Problem of typing: some columns are typed as int64 but contain NaN, which is a float. This causes problems when creating URIs, so need to convert to int first, then to str. – Fixed (see above) but CHECK!
# TODO: Modelling of Layout and Collation (and probably other 'minor' DigiPal tables) is not valid CIDOC-CRM and needs revision.
# TODO: Idiograph is only very lightly modelled here. I think it links to the Hand but nothing more, so question if should do properly.
# TODO: For ontology only -- missing Image-ItemPart link (and Hand-Image link). Not used for export because images aren't included, though arguably the filenames and image sizes at least should be
# Note: P198i for the patron saint is not valid CIDOC-CRM. Since the patron saint is not used anywhere in practice, it has
#    been removed from the export. It could be added back if needed but it's not clear how (perhaps P1 or P67; see report).

# -------------------------------------------------------- LES IMPORTS -----------------------------------------------------------
import pandas as pd
import re
from sqlalchemy import create_engine, inspect
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, XSD
from datetime import datetime

# -------------------------------------------------------- LES FONCTIONS ---------------------------------------------------------
def connection():
    try:
        mydb = create_engine("postgresql+psycopg://postgres:1234@localhost:5432/pstokes")
        return mydb
    except Exception as e:
        print(f"**** Error connecting to database: {e} ****")
        print(f"**** Have you launched PostGres? ****")
        return None

def charger_toutes_tables(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    dataframes = {}
    for table in tables:
        dataframes[table] = pd.read_sql_table(table, engine)
    return dataframes

def keep_digipal(dico):
    d = {}
    for key in dico.keys():
        if not dico[key].empty:
            if re.match('digipal_', key):
                d[key.replace("digipal_", "")] = dico[key]
            elif re.match('django_content_type', key):
                d['django_content_type'] = dico[key]
    return d

# -------------------------------------------------------- CHARGEMENT -----------------------------------------------------------
digipal = connection()
dfs = charger_toutes_tables(digipal)
data = keep_digipal(dfs)

# -------------------------------------------------------- LISTE DES TABLES ET VARIABLES -----------------------------------------------------------
txt=""
for table_name, df in data.items():
    txt+=(f"\n--- {table_name} ---\n")
    txt+=(f"{df.dtypes}\n")
    txt+=(f"{df.head(2)}\n")

with open("tables_variables.txt", "w", encoding="utf-8") as f:
    f.write(txt)

# -------------------------------------------------------- MERGES TABLES POUR FACILITE LE TRAITEMENT -----------------------------------------------------------
# archive
archive = data['archive'].merge(
    data['django_content_type'],
    left_on="content_type_id", right_on="id",
    suffixes=("", "_content_type"), how="left"
)

# -------------------------------------------------------- CREATION DU GRAPHE ---------------------------------------------------
g = Graph()

# --- Namespaces standards ---
CRM  = Namespace("http://www.cidoc-crm.org/cidoc-crm/")   # CIDOC-CRM
FRBRoo = Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/")  # FRBRoo. # TODO: is there now an LRMoo namespace? If so, should use that instead.
CRMtx  = Namespace("https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html/")   # CIDOC-TX
Gold = Namespace("https://static.vocabs.clariah.nl/docs/gold/2010.html/")  # Gold
ANNO=Namespace("http://www.w3.org/ns/oa#") #Annotation Web
ARCH = Namespace("https://digipal.eu/") 
EX   = Namespace("http://digipal.eu/ontology#")            
XSD_ = Namespace("http://www.w3.org/2001/XMLSchema#")
DCTERMS = Namespace("http://purl.org/dc/terms/")    # PAS: Added for annotation creators

g.bind("crm",    CRM)
g.bind("frbroo", FRBRoo)
g.bind("crm-tx",    CRMtx)
g.bind("gold", Gold)
g.bind("archetype", ARCH)
g.bind("web_annotation", ANNO)
g.bind("ex",     EX)
g.bind("owl",    OWL)
g.bind("xsd",    XSD_)
g.bind("dcterms", DCTERMS)

# --- Déclaration de l'ontologie ---
ontologie = URIRef("http://digipal.eu/ontology")
g.add((ontologie, RDF.type,   OWL.Ontology))
g.add((ontologie, RDFS.label, Literal("Ontologie Digipal", lang="en")))

# Vrais imports OWL (ontologies formelles)
g.add((ontologie, OWL.imports, URIRef("https://cidoc-crm.org/rdfs/7.1.3/CIDOC_CRM_v7.1.3.rdf")))
g.add((ontologie, OWL.imports, URIRef("https://cidoc-crm.org/extensions/crmtex/owl/2.0/CRMtex_v2.0.owl")))

# Références documentaires (pas des ontologies, donc seeAlso et non imports)
g.add((ontologie, RDFS.seeAlso, URIRef("http://erlangen-crm.org/efrbroo/")))
g.add((ontologie, RDFS.seeAlso, URIRef("https://static.vocabs.clariah.nl/docs/gold/2010.html")))
g.add((ontologie, RDFS.seeAlso, URIRef("https://www.w3.org/TR/annotation-vocab/")))
g.add((ontologie, RDFS.seeAlso, URIRef("https://digipal.eu/")))

#--------------------------------------- Declaration lien parents/enfants -----------------------------------------------------
# --- Item / FRBRoo F5 ---
g.add((FRBRoo.F5_Item, RDFS.subClassOf, CRM['E22_Human-Made_Object']))
g.add((ARCH.Historical_Item, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Item_Part, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Current_Item, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Historical_Item, RDFS.subClassOf, FRBRoo.F3_Manifestation))
g.add((ARCH.Item_Part, RDFS.subClassOf, FRBRoo.F3_Manifestation))

# --- Script / Style ---
g.add((ARCH.Script, RDFS.subClassOf, CRMtx.TX10_Style))
g.add((CRMtx.TX10_Style, RDFS.subClassOf, CRM.E29_Design_or_Procedure))
# PAS: Added Appearance as full class
g.add((ARCH.Appearance, RDFS.subClassOf, CRM['E55_Type']))

# --- Scribe ---
g.add((ARCH.Scribe, RDFS.subClassOf, CRM.E21_Person))

# --- Writing / Trace ---
g.add((ARCH.Trace, RDFS.subClassOf, CRMtx.TX2_Writing))

# --- Written Text ---
g.add((ARCH.Hand, RDFS.subClassOf, CRMtx.TX7_Written_Text_Segment))
g.add((ARCH.Graph, RDFS.subClassOf, CRMtx.TX7_Written_Text_Segment))
g.add((CRMtx.TX7_Written_Text_Segment, RDFS.subClassOf, CRMtx.TX1_Written_Text))
g.add((CRMtx.TX1_Written_Text, RDFS.subClassOf, CRM['E25_Human-Made_Feature']))

# --- Allograph / Idiograph / Character ---
g.add((ARCH.Idiograph, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Allograph, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Character, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Generalised_Allograph, RDFS.subClassOf, CRM.E36_Visual_Item))
g.add((ARCH.Component, RDFS.subClassOf, CRM.E36_Visual_Item))

# --- Grapheme / Ontograph ---
g.add((ARCH.Ontograph, RDFS.subClassOf, CRMtx.TX8_Grapheme))
g.add((CRMtx.TX8_Grapheme, RDFS.subClassOf, CRM.E55_Type))
g.add((ARCH.Ontograph, RDFS.subClassOf, CRM.E90_Symbolic_Object))
g.add((CRMtx.TX12_Grapheme_Sequence, RDFS.subClassOf, CRM.E90_Symbolic_Object))
g.add((CRMtx.TX11_Grapheme_Occurrence, RDFS.subClassOf, CRMtx.TX12_Grapheme_Sequence))

# --- Structure temporelle / événements ---
g.add((CRM.E1_CRM_Entity, RDFS.subClassOf, OWL.Thing))
g.add((CRM.E92_Spacetime_Volume, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E2_Temporal_Entity, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E4_Period, RDFS.subClassOf, CRM.E2_Temporal_Entity))
g.add((CRM.E4_Period, RDFS.subClassOf, CRM.E92_Spacetime_Volume))
g.add((CRM.E5_Event, RDFS.subClassOf, CRM.E4_Period))
g.add((CRM.E64_End_of_Existence, RDFS.subClassOf, CRM.E5_Event))
g.add((CRM.E68_Dissolution, RDFS.subClassOf, CRM.E64_End_of_Existence))
g.add((CRM.E63_Beginning_of_Existence, RDFS.subClassOf, CRM.E5_Event))
g.add((CRM.E12_Production, RDFS.subClassOf, CRM.E63_Beginning_of_Existence))
g.add((FRBRoo.F28_Expression_Creation, RDFS.subClassOf, CRM.E12_Production))
g.add((CRMtx.TX2_Writing, RDFS.subClassOf, FRBRoo.F28_Expression_Creation))
g.add((CRM.E65_Creation, RDFS.subClassOf, CRM.E63_Beginning_of_Existence))
g.add((FRBRoo.F28_Expression_Creation, RDFS.subClassOf, CRM.E65_Creation))
g.add((CRM.E66_Formation, RDFS.subClassOf, CRM.E63_Beginning_of_Existence))
g.add((CRM.E7_Activity, RDFS.subClassOf, CRM.E5_Event))
g.add((CRM.E11_Modification, RDFS.subClassOf, CRM.E7_Activity))
g.add((CRM.E12_Production, RDFS.subClassOf, CRM.E11_Modification))
g.add((CRM.E65_Creation, RDFS.subClassOf, CRM.E7_Activity))
g.add((CRM.E66_Formation, RDFS.subClassOf, CRM.E7_Activity))
g.add((CRM.E8_Acquisition, RDFS.subClassOf, CRM.E7_Activity))

# --- Autres branches de E1 CRM Entity ---
g.add((CRM['E52_Time-Span'], RDFS.subClassOf, CRM['E1_CRM_Entity']))
g.add((CRM['E53_Place'], RDFS.subClassOf, CRM['E1_CRM_Entity']))
g.add((CRM['E54_Dimension'], RDFS.subClassOf, CRM['E1_CRM_Entity']))
g.add((CRM['E59_Primitive_Value'], RDFS.subClassOf, CRM['E1_CRM_Entity']))
g.add((CRM['E61_Time_Primitive'], RDFS.subClassOf, CRM['E59_Primitive_Value']))
g.add((CRM['E62_String'], RDFS.subClassOf, CRM['E59_Primitive_Value']))
g.add((CRM['E77_Persistent_Item'], RDFS.subClassOf, CRM['E1_CRM_Entity']))
g.add((CRM['E39_Actor'], RDFS.subClassOf, CRM['E77_Persistent_Item']))
g.add((CRM['E70_Thing'], RDFS.subClassOf, CRM['E77_Persistent_Item']))

# --- GOLD  ---
g.add((Gold.Abstract, RDFS.subClassOf, CRM.E77_Persistent_Item))
g.add((Gold.LinguisticDataStructure, RDFS.subClassOf, Gold.Abstract))
g.add((Gold.FeatureSystem, RDFS.subClassOf, Gold.LinguisticDataStructure))

# --- E70 Thing : Human Made Thing / Legal Object ---
g.add((CRM['E71_Human-Made_Thing'], RDFS.subClassOf, CRM['E70_Thing']))
g.add((CRM['E72_Legal_Object'], RDFS.subClassOf, CRM['E70_Thing']))
g.add((CRM['E24_Physical_Human-Made_Thing'], RDFS.subClassOf, CRM['E71_Human-Made_Thing']))
g.add((CRM['E22_Human-Made_Object'], RDFS.subClassOf, CRM['E24_Physical_Human-Made_Thing']))
g.add((CRM['E25_Human-Made_Feature'], RDFS.subClassOf, CRM['E24_Physical_Human-Made_Thing']))
g.add((CRM['E28_Conceptual_Object'], RDFS.subClassOf, CRM['E71_Human-Made_Thing']))
g.add((ARCH.Element_of_Style, RDFS.subClassOf, CRM['E28_Conceptual_Object']))

# --- E55 Type ---
g.add((CRM['E55_Type'], RDFS.subClassOf, CRM['E28_Conceptual_Object']))
g.add((ARCH.Feature, RDFS.subClassOf, CRM['E55_Type']))
g.add((CRM['E56_Language'], RDFS.subClassOf, CRM['E55_Type']))
g.add((CRM['E57_Material'], RDFS.subClassOf, CRM['E55_Type']))
g.add((CRM['E58_Measurement_Unit'], RDFS.subClassOf, CRM['E55_Type']))
g.add((FRBRoo.F3_Manifestation, RDFS.subClassOf, CRM['E55_Type']))

# --- E89 Propositional Object / E73 Information Object ---
g.add((CRM['E89_Propositional_Object'], RDFS.subClassOf, CRM['E28_Conceptual_Object']))
g.add((CRM['E73_Information_Object'], RDFS.subClassOf, CRM['E89_Propositional_Object']))
g.add((CRM['E31_Document'], RDFS.subClassOf, CRM['E73_Information_Object']))
g.add((CRM['E33_Linguistic_Object'], RDFS.subClassOf, CRM['E73_Information_Object']))
g.add((CRM['E34_Inscription'], RDFS.subClassOf, CRM['E33_Linguistic_Object']))
g.add((CRM['E36_Visual_Item'], RDFS.subClassOf, CRM['E73_Information_Object']))
g.add((ARCH.Component, RDFS.subClassOf, CRM['E36_Visual_Item']))
g.add((ARCH.Generalised_Allograph, RDFS.subClassOf, CRM['E36_Visual_Item']))
g.add((CRM['E37_Mark'], RDFS.subClassOf, CRM['E36_Visual_Item']))
g.add((CRM['E34_Inscription'], RDFS.subClassOf, CRM['E37_Mark']))
g.add((CRM['E29_Design_or_Procedure'], RDFS.subClassOf, CRM['E73_Information_Object']))
g.add((ARCH.Script, RDFS.subClassOf, CRM['E29_Design_or_Procedure']))
g.add((CRM['E34_Inscription'], RDFS.subClassOf, CRM['E73_Information_Object']))

# --- E90 Symbolic Object ---
g.add((CRM['E90_Symbolic_Object'], RDFS.subClassOf, CRM['E28_Conceptual_Object']))
g.add((CRM['E41_Appellation'], RDFS.subClassOf, CRM['E90_Symbolic_Object']))
g.add((CRM['E42_Identifier'], RDFS.subClassOf, CRM['E41_Appellation']))
g.add((CRM['E61_Time_Primitive'], RDFS.subClassOf, CRM['E41_Appellation']))
g.add((CRM['E73_Information_Object'], RDFS.subClassOf, CRM['E90_Symbolic_Object']))

# --- E72 Legal Object ---
g.add((CRM['E18_Physical_Thing'], RDFS.subClassOf, CRM['E72_Legal_Object']))
g.add((CRM['E19_Physical_Object'], RDFS.subClassOf, CRM['E18_Physical_Thing']))
g.add((CRM['E20_Biological_Object'], RDFS.subClassOf, CRM['E19_Physical_Object']))
g.add((CRM['E21_Person'], RDFS.subClassOf, CRM['E20_Biological_Object']))
g.add((CRM['E22_Human-Made_Object'], RDFS.subClassOf, CRM['E19_Physical_Object']))
g.add((CRM['E24_Physical_Human-Made_Thing'], RDFS.subClassOf, CRM['E18_Physical_Thing']))
g.add((CRM['E26_Physical_Feature'], RDFS.subClassOf, CRM['E72_Legal_Object']))
g.add((CRM['E25_Human-Made_Feature'], RDFS.subClassOf, CRM['E26_Physical_Feature']))
g.add((CRM['E90_Symbolic_Object'], RDFS.subClassOf, CRM['E72_Legal_Object']))

# ------------------------- TX13 Script -----------------------------------
g.add((CRMtx.TX13_Script, RDFS.subClassOf, CRM['E89_Propositional_Object']))
g.add((CRM['E89_Propositional_Object'], RDFS.subClassOf, CRM['E28_Conceptual_Object']))

# -------------------------------------------------------- HISTORICAL ITEM → frbr:F5 Item --------------------------------
TYPE_HISTITEM = URIRef("http://digipal.eu/ontology#TYPE_Historical_Item")
g.add((TYPE_HISTITEM, RDF.type, CRM['E55_Type']))
g.add((TYPE_HISTITEM, RDFS.label, Literal("Type", lang="en")))

FORMAT_TYPE = URIRef("http://digipal.eu/ontology#Type_Format")
g.add((FORMAT_TYPE, RDF.type, CRM['E55_Type']))
g.add((FORMAT_TYPE, RDFS.label, Literal("Format", lang="en")))

# PAS: Added 'accepted' type for accepted date and place for a given Hand (or other class)
# Used to distinguish the one shown first on the front end, vs. the fuller evidentiary trail of scholarly views
ACCEPTED_TYPE = URIRef("http://digipal.eu/ontology#Type_Accepted")
g.add((ACCEPTED_TYPE, RDF.type, CRM['E55_Type']))
g.add((ACCEPTED_TYPE, RDFS.label, Literal("Accepted", lang="en")))

for _, row in data['historicalitem'].iterrows():

    hist_item = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(row['id'])}")
    g.add((hist_item, RDF.type,      ARCH.Historical_Item))
    if pd.notna(row['name']):
        g.add((hist_item, RDFS.label, Literal(row['name'])))
    if pd.notna(row['catalogue_number']):
        # Nettoyer la valeur pour l'URI : remplacer les caractères invalides par _
        catalogue_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', str(row['catalogue_number']))
        catalogue_number_uri = URIRef(f"http://digipal.eu/ontology#CatalogueNumber_{catalogue_clean}")

        g.add((catalogue_number_uri, RDF.type,   CRM['E42_Identifier']))
        g.add((catalogue_number_uri, EX.cataloguenumber, Literal(str(row['catalogue_number']))))  # valeur originale conservée ici
        g.add((hist_item, CRM['P1_is_identified_by'], catalogue_number_uri))

    # --- Type de manuscrit → E55 Type (lien vers Historical_Item_Type) ---
    if pd.notna(row['historical_item_type_id']):
        type_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_Type_{int(row['historical_item_type_id'])}")
        g.add((type_uri,   RDF.type,   CRM['E55_Type']))
        g.add((hist_item,  CRM['P2_has_type'], type_uri))             
        g.add((type_uri,  CRM['P2_has_type'], TYPE_HISTITEM))
        
    # --- Langue → E56 Language ---
    if pd.notna(row['language_id']):
        langue_uri = URIRef(f"http://digipal.eu/ontology#Language_{int(row['language_id'])}")
        g.add((langue_uri, RDF.type,   CRM['E56_Language']))
        g.add((hist_item,  CRM['P72_has_language'], langue_uri))     

    if pd.notna(row['date']):
        g.add((hist_item, EX.date, Literal(str(row['date']))))

    if pd.notna(row['url']):
        g.add((hist_item, EX.url, Literal(str(row['url']))))

    if pd.notna(row['vernacular']):
        g.add((hist_item, EX.vernacular, Literal(bool(row['vernacular']))))
    if pd.notna(row['neumed']):
        g.add((hist_item, EX.neumed, Literal(bool(row['neumed']))))
    if pd.notna(row['legacy_reference']):
        g.add((hist_item, EX.legacy_reference, Literal(str(row['legacy_reference']))))
    
    if pd.notna(row['historical_item_format_id']):
        format_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_Format_{int(row['historical_item_format_id'])}")
        g.add((hist_item,  CRM['P2_has_type'], format_uri)) 

# PAS: Added missing Historical Item Type export
for _, hi_type in data['historicalitemtype'].iterrows():
    type_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_Type_{int(hi_type['id'])}")
    if pd.notna(hi_type['name']):
        g.add((type_uri, RDFS.label, Literal(hi_type['name'])))

for _, format in data['format'].iterrows():
    hist_item_format = URIRef(f"http://digipal.eu/ontology#Historical_Item_Format_{int(format['id'])}")
    g.add((hist_item_format, RDF.type, CRM['E55_Type']))
    g.add((hist_item_format, RDFS.label, Literal(str(format['name']))))
    g.add((hist_item_format, CRM['P2_has_type'], FORMAT_TYPE))               

# PAS changed to unify structure for Archive, MsOrigin and ItemOrigin (finally!)
for _, a in archive.iterrows():
    # Fix: was "HistoricalItem_" (URI bug — orphaned 180 Archive attribute-assignment nodes)
    hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(a['historical_item_id'])}")
    attr_assignment = URIRef(f"http://digipal.eu/ontology#Archive_{int(a['id'])}")
    g.add((attr_assignment, RDF.type, CRM['E13_Attribute_Assignment']))
    g.add((attr_assignment, CRM['P140_assigned_attribute_to'], hist_uri))
    # PAS: Added notna() guard and conversion to bool() for dubitable, since it is a boolean field in the database but can be NaN
    if pd.notna(a['dubitable']):
        g.add((attr_assignment, EX.dubitable, Literal(bool(a['dubitable']))))
    if pd.notna(a['object_id']) and str(a['content_type_id']) == '43':
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(a['object_id'])}")
        g.add((attr_assignment, CRM['P141_assigned'], place_uri))
    elif pd.notna(a['object_id']) and str(a['content_type_id']) != '43':
        print("Le type de object_id dans historicalitem n'est pas pris en compte à modifier")

# --- DEFINITION DES TYPES DE PLACE ---
REGION_TYPE = URIRef("http://digipal.eu/ontology#Type_Region")
g.add((REGION_TYPE, RDF.type, CRM['E55_Type']))
g.add((REGION_TYPE, RDFS.label, Literal("Région", lang="en")))

CURRENT_COUNTY_TYPE = URIRef("http://digipal.eu/ontology#Type_Current_County")
g.add((CURRENT_COUNTY_TYPE, RDF.type, CRM['E55_Type']))
g.add((CURRENT_COUNTY_TYPE, RDFS.label, Literal("Current County", lang="en")))

HISTORICAL_COUNTY_TYPE = URIRef("http://digipal.eu/ontology#Type_Historical_County")
g.add((HISTORICAL_COUNTY_TYPE, RDF.type, CRM['E55_Type']))
g.add((HISTORICAL_COUNTY_TYPE, RDFS.label, Literal("Historical County", lang="en")))

FONDATION_TYPE = URIRef("http://digipal.eu/ontology#Type_Fondation")
g.add((FONDATION_TYPE, RDF.type, CRM['E55_Type']))
g.add((FONDATION_TYPE, RDFS.label, Literal("Fondation", lang="en")))

REFONDATION_TYPE = URIRef("http://digipal.eu/ontology#Type_Refondation")
g.add((REFONDATION_TYPE, RDF.type, CRM['E55_Type']))
g.add((REFONDATION_TYPE, RDFS.label, Literal("Refondation", lang="en")))

for _, p in data['place'].iterrows():
    place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(p['id'])}")
    g.add((place_uri, RDF.type,      CRM['E53_Place']))  
    g.add((place_uri, RDFS.label, Literal(str(p['name']))))
    if pd.notna(p['eastings']):
        g.add((place_uri, EX.eastings, Literal(str(p['eastings']))))
    if pd.notna(p['northings']):
        g.add((place_uri, EX.northings, Literal(str(p['northings']))))
    if pd.notna(p['region_id']): 
        region_uri = URIRef(f"http://digipal.eu/ontology#Region_{int(p['region_id'])}")
        g.add((region_uri, CRM['P2_has_type'], REGION_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], region_uri))

    if pd.notna(p['current_county_id']):
        current_county_uri = URIRef(f"http://digipal.eu/ontology#County_{int(p['current_county_id'])}") # PAS: removed CurrentCounty to unify with HistoricalCounty, since both point to the same County table
        g.add((current_county_uri, CRM['P2_has_type'], CURRENT_COUNTY_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], current_county_uri))
    
    if pd.notna(p['historical_county_id']):
        historical_county_uri = URIRef(f"http://digipal.eu/ontology#County_{int(p['historical_county_id'])}")
        g.add((historical_county_uri, CRM['P2_has_type'], HISTORICAL_COUNTY_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], historical_county_uri))

for _, county in data['county'].iterrows():
    county_uri = URIRef(f"http://digipal.eu/ontology#County_{int(county['id'])}")
    g.add((county_uri, RDF.type,      CRM['E53_Place']))  
    g.add((county_uri, RDFS.label, Literal(str(county['name']))))

for _, region in data['region'].iterrows():
    region_uri = URIRef(f"http://digipal.eu/ontology#Region_{int(region['id'])}")
    g.add((region_uri, RDF.type,      CRM['E53_Place']))  
    g.add((region_uri, RDFS.label, Literal(str(region['name']))))

# PAS: Fixed conceptual and coding issues (see above)
for _, i in data['institution'].iterrows():
    insti = URIRef(f"http://digipal.eu/ontology#Institution_{int(i['id'])}")
    g.add((insti, RDF.type, CRM['E74_Group']))
    g.add((insti, RDFS.label, Literal(str(i['name']))))

    if pd.notna(i['foundation']):
        insti_foundation = URIRef(f"http://digipal.eu/ontology#InstiFoundation_{int(i['id'])}")
        g.add((insti_foundation, RDF.type, CRM['E66_Formation']))
        g.add((insti_foundation, CRM['P95_has_formed'], insti))
        g.add((insti_foundation, EX['foundation'], Literal(str(i['foundation']))))
        if pd.notna(i['founder_id']):
            founder_insti = URIRef(f"http://digipal.eu/ontology#Person_{int(i['founder_id'])}")
            g.add((insti_foundation, CRM['P14_carried_out_by_founder'], founder_insti))
        g.add((insti_foundation, CRM['P2_has_type'], FONDATION_TYPE))

    if pd.notna(i['refoundation']):
        insti_refoundation = URIRef(f"http://digipal.eu/ontology#InstiRefoundation_{int(i['id'])}")
        g.add((insti_refoundation, RDF.type, CRM['E66_Formation']))
        g.add((insti_refoundation, CRM['P95_has_formed'], insti))
        g.add((insti_refoundation, EX['refoundation'], Literal(str(i['refoundation']))))
        if pd.notna(i['founder_id']):
            founder_insti = URIRef(f"http://digipal.eu/ontology#Person_{int(i['founder_id'])}")
            g.add((insti_refoundation, CRM['P14_carried_out_by_founder'], founder_insti))
        if pd.notna(i['reformer_id']):
            reformer_insti = URIRef(f"http://digipal.eu/ontology#Person_{int(i['reformer_id'])}")
            g.add((insti_refoundation, CRM['P14_carried_out_by_reformer'], reformer_insti))
        g.add((insti_refoundation, CRM['P2_has_type'], REFONDATION_TYPE))

    if pd.notna(i['institution_type_id']):
        type_insti_uri = URIRef(f"http://digipal.eu/ontology#InstitutionType_{int(i['institution_type_id'])}")
        g.add((insti, CRM['P2_has_type'], type_insti_uri))

    if pd.notna(i['place_id']):
        place_insti_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(i['place_id'])}")
        g.add((place_insti_uri, RDF.type, CRM['E53_Place']))
        g.add((insti, CRM['P74_has_current_or_former_residence'], place_insti_uri))

for _, inst_type in data['institutiontype'].iterrows():
    insti_type= URIRef(f"http://digipal.eu/ontology#InstitutionType_{int(inst_type['id'])}")
    g.add((insti_type, RDF.type, CRM['E55_Type']))
    g.add((insti_type, RDFS.label, Literal(str(inst_type['name']))))

for _, pers in data['person'].iterrows():
    insti = URIRef(f"http://digipal.eu/ontology#Person_{int(pers['id'])}")
    g.add((insti, RDF.type, CRM['E21_Person']))
    g.add((insti, RDFS.label, Literal(str(pers['name']))))

for _, item in data['itempart'].iterrows():
    itempart= URIRef(f"http://digipal.eu/ontology#Item_Part_{int(item['id'])}")
    g.add((itempart, RDF.type,      ARCH.Item_Part))
    if pd.notna(item['display_label']):
        g.add((itempart, RDFS.label, Literal(item['display_label'])))
    if pd.notna(item['pagination']):
        g.add((itempart, EX.pagination, Literal(item['pagination'])))
    if pd.notna(item['notes']):
        g.add((itempart, RDFS.comment, Literal(item['notes'])))
    if pd.notna(item['current_item_id']):
        F5_Item_uri = URIRef(f"http://digipal.eu/ontology#Item_{int(item['id'])}")
        current_item_uri = URIRef(f"http://digipal.eu/ontology#Current_Item_{int(item['current_item_id'])}")
        g.add((current_item_uri,  CRM['P46_is_composed_of'], itempart))
        g.add((current_item_uri,  OWL['sameAs'], F5_Item_uri))

for _, part in data['itempartitem'].iterrows():
    hist= URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(part['historical_item_id'])}")
    item= URIRef(f"http://digipal.eu/ontology#Item_Part_{int(part['item_part_id'])}")
    g.add((hist,  CRM['P46_is_composed_of'], item))

    #Création F5 item et F3 Manifestation 
    F5_Item_uri = URIRef(f"http://digipal.eu/ontology#Item_Part_{int(part['item_part_id'])}")
    F3_Manifestation_uri = URIRef(f"http://digipal.eu/ontology#Manifestation_{int(part['item_part_id'])}")
    g.add((F3_Manifestation_uri, RDF.type, FRBRoo['F3_Manifestation']))
    g.add((F5_Item_uri, RDF.type, FRBRoo['F5_Item']))
    g.add((hist, OWL['sameAs'], F5_Item_uri))
    g.add((item, OWL['sameAs'], F5_Item_uri))
    g.add((hist, OWL['sameAs'], F3_Manifestation_uri))
    g.add((item, OWL['sameAs'],F3_Manifestation_uri))

# PAS: ItemOrigin migrated onto E13 Attribute Assignment to use the same pattern as Archive and MSOrigin
for _, origin in data['itemorigin'].iterrows():
    hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(origin['historical_item_id'])}")
    attr_assignment = URIRef(f"http://digipal.eu/ontology#ItemOrigin_{int(origin['id'])}")
    g.add((attr_assignment, RDF.type, CRM['E13_Attribute_Assignment']))
    g.add((attr_assignment, CRM['P140_assigned_attribute_to'], hist_uri))
    # PAS: Added notna() guard and conversion to bool() for dubitable, since it is a boolean field in the database but can be NaN
    if pd.notna(origin['dubitable']):
        g.add((attr_assignment, EX.dubitable, Literal(bool(origin['dubitable']))))
    if pd.notna(origin['place_id']):
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(origin['place_id'])}")
        g.add((attr_assignment, CRM['P141_assigned'], place_uri))
    if pd.notna(origin['institution_id']):
        institution_uri = URIRef(f"http://digipal.eu/ontology#Institution_{int(origin['institution_id'])}")
        g.add((attr_assignment, CRM['P141_assigned'], institution_uri))

MEASUREMENT_UNIT = URIRef("http://digipal.eu/ontology#Measurement_Unit_millimeter")
g.add((MEASUREMENT_UNIT, RDF.type, CRM['E58_Measurement_Unit']))
g.add((MEASUREMENT_UNIT, RDFS.label, Literal("Millimeter", lang="en")))

for _, layout in data['layout'].iterrows():
    # PAS: Very many rows (close to 80%) in digipal_layout have no real content: all the measurement fields are null or
    # zero, and all boolean flags null or False, so we filter out these rather than adding them.
    # Assume then that False is only meaningful when at least one other field is populated.
    # NB also that inspection of the DigiPal data shows that the on_top_line field is always FALSE, even though 
    # for the period in DigiPal it should be always TRUE. Since it is not used in any other project to my knowledge,
    # it has been removed entirely from the export.
    has_content = (
        (pd.notna(layout['page_height']) and layout['page_height'] != 0) or
        (pd.notna(layout['page_width']) and layout['page_width'] != 0) or
        (pd.notna(layout['frame_height']) and layout['frame_height'] != 0) or
        (pd.notna(layout['frame_width']) and layout['frame_width'] != 0) or
        (pd.notna(layout['tramline_width']) and layout['tramline_width'] != 0) or
        (pd.notna(layout['lines']) and layout['lines'] != 0) or
        (pd.notna(layout['columns']) and layout['columns'] != 0) or
        (pd.notna(layout['comments']) and str(layout['comments']).strip() != '') or
        pd.notna(layout['hair_arrangement_id']) or
#        (layout['on_top_line'] == True) or         # PAS: removed due to problem in source data (see above)
        (layout['multiple_sheet_rulling'] == True) or
        (layout['bilinear_ruling'] == True) or
        (layout['insular_pricking'] == True)
    )
    if not has_content:
        continue

    # PAS: NB layout and dimension URIs assume linking to Historical Item since that is how DigiPal's data is structured.
    #  If other Archetype-based projects use Layout elsewhere, e.g. linked to Item Part, the URI naming should be changed accordingly.
    layout_uri = URIRef(f"http://digipal.eu/ontology#Layout_Historical_Item_{int(layout['historical_item_id'])}") 
    dimension_uri = URIRef(f"http://digipal.eu/ontology#Dimension_Historical_Item_{int(layout['historical_item_id'])}")
    g.add((layout_uri, RDF.type, CRM['E18_Physical_Thing']))
    g.add((dimension_uri, RDF.type, CRM['E54_Dimension']))

    g.add((layout_uri, RDFS.label, Literal(f"Layout {layout['id']}")))
    g.add((dimension_uri, RDFS.label, Literal(f"Dimension {layout['id']}")))

    # PAS: Fixed issue of converting float to int for dimensions, since should be integers for these properties.
    if pd.notna(layout['page_height']):
        g.add((dimension_uri, EX['page_height'], Literal(int(layout['page_height']))))
    if pd.notna(layout['page_width']):
        g.add((dimension_uri, EX['page_width'], Literal(int(layout['page_width']))))
    if pd.notna(layout['frame_height']):
        g.add((dimension_uri, EX['frame_height'], Literal(int(layout['frame_height']))))
    if pd.notna(layout['frame_width']):
        g.add((dimension_uri, EX['frame_width'], Literal(int(layout['frame_width']))))
    if pd.notna(layout['tramline_width']):
        g.add((dimension_uri, EX['tramline_width'], Literal(int(layout['tramline_width']))))
    if pd.notna(layout['lines']):
        g.add((layout_uri, EX['lines'], Literal(int(layout['lines']))))
    if pd.notna(layout['columns']):
        g.add((layout_uri, EX['columns'], Literal(int(layout['columns']))))

# PAS: on_top_line removed (see above)
    if pd.notna(layout['multiple_sheet_rulling']):
        g.add((layout_uri, EX['multiple_sheet_rulling'], Literal(layout['multiple_sheet_rulling'])))
    if pd.notna(layout['bilinear_ruling']):
        g.add((layout_uri, EX.bilinear_ruling, Literal(layout['bilinear_ruling'])))
    if pd.notna(layout['comments']):
        g.add((layout_uri, RDFS.comment, Literal(layout['comments'])))
    if pd.notna(layout['insular_pricking']):
        # PAS: Fixed error in property name (was EX.columns)
        g.add((layout_uri, EX['insular_pricking'], Literal(layout['insular_pricking'])))

    if pd.notna(layout['hair_arrangement_id']):
        hair =  URIRef(f"http://digipal.eu/ontology#Hair_{int(layout['hair_arrangement_id'])}")
        g.add((layout_uri,  CRM['P45_consists_of'], hair))

    # PAS: This loop is redundant in practice as Layout is only linked to Historical Items in DigiPal,
    # but it could well be used for Item Parts in other implementations, so keep it in case.
    # NB that if this is implemented then the naming of the layout and dimension URIs should be changed accordingly (see above)
    if pd.notna(layout['item_part_id']):
        itempart_layout =  URIRef(f"http://digipal.eu/ontology#Item_Part_{int(layout['item_part_id'])}")
        g.add((itempart_layout,  CRM['P46_is_composed_of'], layout_uri))

        if pd.notna(layout['page_height']) or pd.notna(layout['page_width']) or pd.notna(layout['frame_height']) or pd.notna(layout['frame_width']) or pd.notna(layout['tramline_width']):
            g.add((itempart_layout,  CRM['P43_has_dimension'], dimension_uri))

    # PAS: added — historical_item_id is the field actually populated in DigiPal's data;
    # item_part_id above is kept as a fallback for other Archetype-based projects that may use it.
    if pd.notna(layout['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(layout['historical_item_id'])}")
        g.add((hist_uri, CRM['P46_is_composed_of'], layout_uri))
        if pd.notna(layout['page_height']) or pd.notna(layout['page_width']) or pd.notna(layout['frame_height']) or pd.notna(layout['frame_width']) or pd.notna(layout['tramline_width']):
            g.add((hist_uri, CRM['P43_has_dimension'], dimension_uri))

for _, hair in data['hair'].iterrows():
    hair_uri =  URIRef(f"http://digipal.eu/ontology#Hair_{int(hair['id'])}")
    g.add((hair_uri, RDF.type,      CRM['E57_Material']))    
    if pd.notna(hair['label']):
        g.add((hair_uri, RDFS.label, Literal(hair['label'])))

CAT_HISTITEM = URIRef("http://digipal.eu/ontology#Category_Historical_Item")
g.add((CAT_HISTITEM , RDF.type, CRM['E55_Type']))
g.add((CAT_HISTITEM , RDFS.label, Literal("Category", lang="en")))

for _, category in data['category'].iterrows(): 
    category_uri = URIRef(f"http://digipal.eu/ontology#Category_{int(category['id'])}")
    g.add((category_uri,  CRM['P2_has_type'], CAT_HISTITEM))
    g.add((category_uri, RDF.type,      CRM['E55_Type']))
    if pd.notna(category['name']):
        g.add((category_uri, RDFS.label, Literal(category['name'])))
    # PAS: Fixed error of float to int conversion for sort_order, since it should be an integer for this property.
    if pd.notna(category['sort_order']):
        g.add((category_uri, EX.sort_order, Literal(int(category['sort_order']))))

for _, hist_cat in data['historicalitem_categories'].iterrows():
    cat_uri = URIRef(f"http://digipal.eu/ontology#Category_{int(hist_cat['category_id'])}")
    hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(hist_cat['historicalitem_id'])}")
    g.add((hist_uri,  CRM['P2_has_type'], cat_uri))

for _, language in data['language'].iterrows():
    language_uri = URIRef(f"http://digipal.eu/ontology#Language_{int(language['id'])}")
    g.add((language_uri, RDF.type,      CRM['E56_Language']))          # classe locale pour filtrer facilement
    if pd.notna(language['name']):
        g.add((language_uri, RDFS.label, Literal(language['name'])))

COLLATION_type = URIRef("http://digipal.eu/ontology#Collation")
g.add((COLLATION_type, RDF.type, CRM['E55_Type']))
g.add((COLLATION_type,  RDFS.label, Literal("Collation", lang="en")))

DECORATION_type = URIRef("http://digipal.eu/ontology#Decoration")
g.add((DECORATION_type, RDF.type, CRM['E55_Type']))
g.add((DECORATION_type,  RDFS.label, Literal("Decoration", lang="en")))

for _, collation in data['collation'].iterrows():
    # PAS: Filter for collation rows that have no content (all fields null or empty) to avoid creating meaningless nodes in the graph.
    has_content = (
        (collation['fragment'] == True) or
        (pd.notna(collation['leaves']) and collation['leaves'] != 0)
    )
    if not has_content:
        continue

    collation_uri = URIRef(f"http://digipal.eu/ontology#Collation_{int(collation['id'])}")
    g.add((collation_uri, RDF.type,      CRM['E18_Physical_Thing']))
    g.add((collation_uri,  CRM['P2_has_type'], COLLATION_type))
    g.add((collation_uri, RDFS.label, Literal(f"Collation {collation['id']}")))
    if pd.notna(collation['fragment']):
        g.add((collation_uri, EX.fragment, Literal(collation['fragment'])))
    if pd.notna(collation['leaves']):
        g.add((collation_uri, EX.leaves, Literal(int(collation['leaves']))))
    if pd.notna(collation['front_flyleaves']):
        g.add((collation_uri, EX.front_flyleaves, Literal(int(collation['front_flyleaves']))))
    if pd.notna(collation['back_flyleaves']):
        g.add((collation_uri, EX.back_flyleaves, Literal(int(collation['back_flyleaves']))))
    if pd.notna(collation['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(collation['historical_item_id'])}")
        g.add((hist_uri,  CRM['P46_is_composed_of'], collation_uri))

for _, deco in data['decoration'].iterrows():
    deco_uri = URIRef(f"http://digipal.eu/ontology#Decoration_{int(deco['id'])}")
    g.add((deco_uri, RDF.type,      CRM['E18_Physical_Thing']))
    g.add((deco_uri,  CRM['P2_has_type'], DECORATION_type))
    g.add((deco_uri, RDFS.label, Literal(f"Decoration {deco['id']}")))
    if pd.notna(deco['illustrated']):
        g.add((deco_uri, EX.illustrated, Literal(deco['illustrated'])))

    if pd.notna(deco['decorated']):
        g.add((deco_uri, EX.decorated, Literal(deco['decorated'])))

    if pd.notna(deco['illuminated']):
        g.add((deco_uri, EX.illuminated, Literal(deco['illuminated'])))

    if pd.notna(deco['num_colours']):
        g.add((deco_uri, EX.num_colours, Literal(int(deco['num_colours']))))
    if pd.notna(deco['num_inks']):
        g.add((deco_uri, EX.num_inks, Literal(int(deco['num_inks']))))

    if pd.notna(deco['colours']):
        g.add((deco_uri, EX.colours, Literal(deco['colours'])))
    
    if pd.notna(deco['inks']):
        g.add((deco_uri, EX.inks, Literal(deco['inks'])))
    
    if pd.notna(deco['style']):
        g.add((deco_uri, EX.style, Literal(deco['style'])))
    
    if pd.notna(deco['description']):
        g.add((deco_uri, DCTERMS.description, Literal(deco['description'])))

    if pd.notna(deco['catalogue_references']):
        g.add((deco_uri, EX.catalogue_references, Literal(deco['catalogue_references'])))

    if pd.notna(deco['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(deco['historical_item_id'])}")
        g.add((hist_uri,  CRM['P46_is_composed_of'], deco_uri))

# PAS: Changed structure from Writing event to Assigned Attribute, since Writing is here reserved for Hands.
for _, hist_date in data['historicalitemdate'].iterrows():
    attr_assignment = URIRef(f"http://digipal.eu/ontology#HistItemDate_{int(hist_date['id'])}")
    g.add((attr_assignment, RDF.type, CRM['E13_Attribute_Assignment']))
    if pd.notna(hist_date['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(hist_date['historical_item_id'])}")
        g.add((attr_assignment, CRM['P140_assigned_attribute_to'], hist_uri))
    if pd.notna(hist_date['date_id']):
        date_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{int(hist_date['date_id'])}")
        g.add((attr_assignment, CRM['P141_assigned'], date_uri))

    if pd.notna(hist_date['evidence']):
        g.add((attr_assignment, CRM['P3_has_note'], Literal(hist_date['evidence'])))
    if pd.notna(hist_date['vernacular']):
        g.add((attr_assignment, EX.vernacular, Literal(hist_date['vernacular'])))
    if pd.notna(hist_date['addition']):
        g.add((attr_assignment, EX.addition, Literal(hist_date['addition'])))
    if pd.notna(hist_date['dubitable']):
        g.add((attr_assignment, EX.dubitable, Literal(hist_date['dubitable'])))

for _, date in data['date'].iterrows():
    date_period_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{int(date['id'])}")
    g.add((date_period_uri, RDF.type,      CRM.E4_Period))
    g.add((date_period_uri, RDFS.label, Literal(f"Date {date['id']}")))
    g.add((date_period_uri, EX.date, Literal(date['date'])))
    g.add((date_period_uri, EX.weight, Literal(date['weight'])))
    # PAS: Added guards for NaN values to avoid adding triples with empty literals, and also converted to bool for post_conquest and s_xi since they are boolean fields in the database but can be NaN.
    if pd.notna(date['post_conquest']):
        g.add((date_period_uri, EX.post_conquest, Literal(bool(date['post_conquest']))))
    if pd.notna(date['s_xi']):
        g.add((date_period_uri, EX.s_xi, Literal(bool(date['s_xi']))))

    # PAS: Fixed error of float to int conversion for sort_order, band, and additional_band, since they should be integers for these properties.
    # Also added checks for NaN values to avoid adding triples with empty literals.
    if pd.notna(date['sort_order']):
        g.add((date_period_uri, EX.sort_order, Literal(int(date['sort_order']))))
    if pd.notna(date['band']):
        g.add((date_period_uri, EX.band, Literal(int(date['band']))))
    if pd.notna(date['additional_band']):
        g.add((date_period_uri, EX.additional_band, Literal(int(date['additional_band']))))

    
    date_timespan_uri = URIRef(f"http://digipal.eu/ontology#Date_Time_Span_{int(date['id'])}")
    g.add((date_period_uri,  CRM['P4_has_time-span'], date_timespan_uri))
    g.add((date_timespan_uri, RDF.type,      CRM['E52_Time-Span']))
    g.add((date_timespan_uri, RDFS.label, Literal(f"Time-span {date['id']}")))
    # PAS: Added guards for NaN values to avoid adding triples with empty literals.
    if pd.notna(date['min_weight']):
        g.add((date_timespan_uri, EX.min_weight, Literal(date['min_weight'])))
    if pd.notna(date['max_weight']):
        g.add((date_timespan_uri, EX.max_weight, Literal(date['max_weight'])))

    if pd.notna(date['evidence']):
        date_document_uri = URIRef(f"http://digipal.eu/ontology#Date_Document_{int(date['id'])}")
        g.add((date_period_uri,  CRM.P70i_is_documented_in, date_document_uri))
        g.add((date_document_uri, RDF.type,      CRM.E31_Document)) 
        g.add((date_document_uri, EX.evidence, Literal(date['evidence'])))

for _, desc in data['description'].iterrows():
    description_uri = URIRef(f"http://digipal.eu/ontology#Description_{int(desc['id'])}")
    g.add((description_uri, RDF.type, CRM['E31_Document']))
    # PAS: Removed redundant duplication of description (and also RDFS.label is not appropriate for a description).
    if pd.notna(desc['description']):
        # PAS: Changed to use DCTERMS.description instead of EX.description for better semantic alignment.
        g.add((description_uri, DCTERMS.description, Literal(desc['description'])))
    if pd.notna(desc['comments']):
        g.add((description_uri, EX.comments, Literal(desc['comments'])))
    if pd.notna(desc['summary']): # Never used in practice...
        g.add((description_uri, EX.summary, Literal(desc['summary'])))
    if pd.notna(desc['source_id']): 
        source_uri = URIRef(f"http://digipal.eu/ontology#Source_{int(desc['source_id'])}")
        g.add((description_uri,  CRM['P70i_is_documented_in'], source_uri))
    if pd.notna(desc['text_id']): 
        text_uri = URIRef(f"http://digipal.eu/ontology#Text_{int(desc['text_id'])}")
        g.add((description_uri,  CRM['P70_documents'], text_uri))
    if pd.notna(desc['historical_item_id']): 
        historical_item_uri = URIRef(f"http://digipal.eu/ontology#Historical_Item_{int(desc['historical_item_id'])}")
        g.add((description_uri,  CRM['P70_documents'], historical_item_uri))


for _, current in data['currentitem'].iterrows():
    current_uri = URIRef(f"http://digipal.eu/ontology#Current_Item_{int(current['id'])}")
    g.add((current_uri, RDF.type,      ARCH.Current_Item)) 
    if pd.notna(current['shelfmark']):
        g.add((current_uri, EX.shelfmark, Literal(current['shelfmark'])))
    if pd.notna(current['description']):
        g.add((current_uri, DCTERMS.description, Literal(current['description'])))
    if pd.notna(current['display_label']):
        g.add((current_uri, RDFS.label, Literal(current['display_label'])))
    if pd.notna(current['repository_id']):
        repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{int(current['repository_id'])}")
        g.add((current_uri,  CRM.P50_has_current_keeper, repository_uri))
    
for _, repository in data['repository'].iterrows():
    repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{int(repository['id'])}")
    g.add((repository_uri, RDF.type,      CRM.E74_Group)) #Peut-être mettre en document 
    if pd.notna(repository['name']):
        g.add((repository_uri, RDFS.label, Literal(repository['name'])))
    if pd.notna(repository['short_name']):
        g.add((repository_uri, EX.short_name, Literal(repository['short_name'])))
    if pd.notna(repository['url']):
        g.add((repository_uri, EX.url, Literal(repository['url'])))
    if pd.notna(repository['comma']):
        g.add((repository_uri, EX.comma, Literal(repository['comma'])))
    if pd.notna(repository['british_isles']):
        g.add((repository_uri, EX.british_isles, Literal(repository['british_isles'])))
    if pd.notna(repository['digital_project']):
        g.add((repository_uri, EX.digital_project, Literal(repository['digital_project'])))
    if pd.notna(repository['copyright_notice']):
        g.add((repository_uri, EX.copyright_notice, Literal(repository['copyright_notice'])))
    if pd.notna(repository['place_id']):
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(repository['place_id'])}")
        g.add((repository_uri,  CRM.P74_has_current_or_former_residence, place_uri))
    # PAS: NB this isn't the rights that an institution has over itself, so not P104.
    # Instead, we apply this directly to the relevant Image, unless an image-specific permission is provided.
    if pd.notna(repository['type_id']):
        type_uri = URIRef(f"http://digipal.eu/ontology#RepositoryType_{int(repository['type_id'])}")
        g.add((repository_uri,  CRM.P2_has_type, type_uri))
    # PAS: P10 is clearly the wrong relationship (should only apply to Time-Spans), but it's unclear what the right one should be.
    # DigiPal only has obe occurrence which is an error, and no other projects use it AFAIK, so omit for now.
    # TODO: Add a proper solution for potential future projects
#    if pd.notna(repository['part_of_id']):
#        part_of_uri = URIRef(f"http://digipal.eu/ontology#Repository_{int(repository['part_of_id'])}")
#        g.add((repository_uri,  CRM.P10_falls_within, part_of_uri))
    
for _, text in data['text'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{int(text['id'])}")
    g.add((text_uri, RDF.type,      CRMtx.TX1_Written_Text))  # TODO: No, TX1 is a Physical Feature, not a Linguistic Object, so this is wrong. arch:Text should be E33_Linguistic_Object (or FRBRoo Expression)
    if pd.notna(text['name']):
        g.add((text_uri, RDFS.label, Literal(text['name'])))
    if pd.notna(text['date']):
        g.add((text_uri, EX.date, Literal(text['date'])))
    if pd.notna(text['url']):
        g.add((text_uri, EX.url, Literal(text['url'])))
    if pd.notna(text['date_sort']):
        g.add((text_uri, EX.date, Literal(text['date_sort'])))

for _, text_cat in data['text_categories'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{int(text_cat['text_id'])}")
    cat_uri = URIRef(f"http://digipal.eu/ontology#Category_{int(text_cat['category_id'])}")
    # PAS: added text type to category link, as it was missing in the original code.
    g.add((text_uri, CRM['P2_has_type'], cat_uri))

for _, text_lang in data['text_languages'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{int(text_lang['text_id'])}")
    lang_uri = URIRef(f"http://digipal.eu/ontology#Language_{int(text_lang['language_id'])}")
    # PAS: added language link to text, as it was missing in the original code.
    # TODO: NB that P72 is not strictly correct as Text here is TX1 so a Physical Feature, not a E33 Linguistic Object
    g.add((text_uri, CRM['P72_has_language'], lang_uri))

for _, text_item in data['textitempart'].iterrows():
    text_item_uri = URIRef(f"http://digipal.eu/ontology#Text_Item_part_{int(text_item['id'])}")
    g.add((text_item_uri, RDF.type,      CRMtx.TX7_Written_Text_Segment))
    if pd.notna(text_item['name']):
        g.add((text_item_uri, RDFS.label, Literal(text_item['name'])))
    if pd.notna(text_item['date']):
        g.add((text_item_uri, EX.date, Literal(text_item['date'])))
    if pd.notna(text_item['locus']):
        g.add((text_item_uri, EX.locus, Literal(text_item['locus'])))
    if pd.notna(text_item['text_id']):
        text_uri = URIRef(f"http://digipal.eu/ontology#Text_{int(text_item['text_id'])}")
        # PAS: fixed reversed link. The text item is a segment of the text, so the text should have the segment, not the other way around.
        g.add((text_uri,  CRMtx.TXP4_has_segment, text_item_uri))

for _, owner in data['owner'].iterrows():
    owner_uri = URIRef(f"http://digipal.eu/ontology#Owner_{int(owner['id'])}")
    g.add((owner_uri, RDF.type,      CRM.E39_Actor))
    if pd.notna(owner['date']):
        g.add((owner_uri, EX.date, Literal(owner['date'])))
    if pd.notna(owner['evidence']):
        g.add((owner_uri, EX.evidence, Literal(owner['evidence'])))
    if pd.notna(owner['rebound']):
        g.add((owner_uri, EX.rebound, Literal(owner['rebound'])))
    if pd.notna(owner['annotated']):
        g.add((owner_uri, EX.annotated, Literal(owner['annotated'])))
    if pd.notna(owner['dubitable']):
        g.add((owner_uri, EX.dubitable, Literal(owner['dubitable'])))
    if pd.notna(owner['display_label']):
        g.add((owner_uri, RDFS.label, Literal(owner['display_label'])))
    if pd.notna(owner['person_id']):
        person_uri = URIRef(f"http://digipal.eu/ontology#Person_{int(owner['person_id'])}") 
        g.add((owner_uri,  OWL.sameAs, person_uri))
    if pd.notna(owner['institution_id']):
        institution_uri = URIRef(f"http://digipal.eu/ontology#Institution_{int(owner['institution_id'])}") 
        g.add((owner_uri,  OWL.sameAs, institution_uri))
    if pd.notna(owner['repository_id']):
        repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{int(owner['repository_id'])}") 
        # PAS: Can't see why P74 is used here, so changed to OWL.sameAs to match the others.
        # However, this isn't really correct either as a digipal_owner record is in fact a linking table which
        # also includes information about the ownership itself (so the name is misleading: it's less 'owner' than 'ownership').
        # TODO: Revise and fix the model, perhaps using full CIDOC-CRM Acquisition pattern (E8 Acquisition, E10 Transfer of Custody, E39 Actor, E53 Place, etc.) to model the ownership event and its participants.
        g.add((owner_uri,  OWL.sameAs, repository_uri))
    
for _, hand in data['hand'].iterrows():
    hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{int(hand['id'])}")
    g.add((hand_uri, RDF.type,      ARCH.Hand))
    if pd.notna(hand['num']):
        g.add((hand_uri, EX.num, Literal(hand['num'])))
    if pd.notna(hand['scragg']):
        g.add((hand_uri, EX.scragg, Literal(hand['scragg'])))
    if pd.notna(hand['em_title']):
        g.add((hand_uri, EX.em_title, Literal(hand['em_title'])))
    if pd.notna(hand['label']):
        g.add((hand_uri, RDFS.label, Literal(hand['label'])))
    if pd.notna(hand['display_note']):
        g.add((hand_uri, EX.display_note, Literal(hand['display_note'])))
    if pd.notna(hand['internal_note']):
        g.add((hand_uri, EX.internal_note, Literal(hand['internal_note'])))
    if pd.notna(hand['relevant']):
        g.add((hand_uri, EX.relevant, Literal(hand['relevant'])))
    if pd.notna(hand['latin_only']):
        g.add((hand_uri, EX.latin_only, Literal(hand['latin_only'])))
    if pd.notna(hand['gloss_only']):
        g.add((hand_uri, EX.gloss_only, Literal(hand['gloss_only'])))
    if pd.notna(hand['membra_disjecta']):
        g.add((hand_uri, EX.membra_disjecta, Literal(hand['membra_disjecta'])))
    # PAS: Fixed error of float to int conversion for num_glosses and num_glossing_hands, since they should be integers for these properties.
    if pd.notna(hand['num_glosses']):
        g.add((hand_uri, EX.num_glosses, Literal(int(hand['num_glosses']))))
    if pd.notna(hand['num_glossing_hands']):
        g.add((hand_uri, EX.num_glossing_hands, Literal(int(hand['num_glossing_hands']))))
    if pd.notna(hand['scribble_only']):
        g.add((hand_uri, EX.scribble_only, Literal(hand['scribble_only'])))
    if pd.notna(hand['imitative']):
        g.add((hand_uri, EX.imitative, Literal(hand['imitative'])))
    if pd.notna(hand['comments']):
        g.add((hand_uri, EX.comments, Literal(hand['comments'])))
    if pd.notna(hand['display_label']):
        g.add((hand_uri, EX.display_label, Literal(hand['display_label'])))
    if pd.notna(hand['locus']):
        g.add((hand_uri, EX.locus, Literal(hand['locus'])))
    if pd.notna(hand['surrogates']):
        g.add((hand_uri, EX.surrogates, Literal(hand['surrogates'])))
    if pd.notna(hand['selected_locus']):
        g.add((hand_uri, EX.selected_locus, Literal(hand['selected_locus'])))
    if pd.notna(hand['ker']):
        g.add((hand_uri, EX.ker, Literal(hand['ker'])))

    # PAS: Writing moved to Hand-level
    # NB no direct link from Writing to Item Part — relies on the transitive Writing—P108→Hand←P56—ItemPart path.
    # This is because Hand is a human-made feature so is already closely connected to the Item Part,
    # and is in a sense exactly the link between the Activity and the physical surface.
    writing_uri = URIRef(f"http://digipal.eu/ontology#Writing_{int(hand['id'])}")
    g.add((writing_uri, RDF.type, CRMtx.TX2_Writing))
    g.add((writing_uri, CRM.P108_has_produced, hand_uri))
    if pd.notna(hand['scribe_id']):
        scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{int(hand['scribe_id'])}")
        g.add((writing_uri, CRM.P14_carried_out_by, scribe_uri))

    # PAS: Hand's accepted date/place now via E13 Attribute Assignment, per hand — not via the Writing event.
    # Seems closer toto the way palaeographers think: 'this is a hand of the eleventh century' often means
    # 'this hand has the style/characteristics of writing from the eleventh century, and therefore we attribute
    # the date of the writing event to that period'
    if pd.notna(hand['assigned_date_id']):
        date_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{int(hand['assigned_date_id'])}")
        attr_assignment_date = URIRef(f"http://digipal.eu/ontology#HandDate_{int(hand['id'])}")
        g.add((attr_assignment_date, RDF.type, CRM['E13_Attribute_Assignment']))
        g.add((attr_assignment_date, CRM['P140_assigned_attribute_to'], hand_uri))
        g.add((attr_assignment_date, CRM['P141_assigned'], date_uri))
        g.add((attr_assignment_date, CRM['P2_has_type'], ACCEPTED_TYPE))
    if pd.notna(hand['assigned_place_id']):
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(hand['assigned_place_id'])}")
        attr_assignment_place = URIRef(f"http://digipal.eu/ontology#HandPlace_{int(hand['id'])}")
        g.add((attr_assignment_place, RDF.type, CRM['E13_Attribute_Assignment']))
        g.add((attr_assignment_place, CRM['P140_assigned_attribute_to'], hand_uri))
        g.add((attr_assignment_place, CRM['P141_assigned'], place_uri))
        g.add((attr_assignment_place, CRM['P2_has_type'], ACCEPTED_TYPE))

    # PAS: Writing System in CRMtex means something else so is removed.
    # Also, arch:Script as TX10 Style is now linked to the TX2 Writing event, not the arch:Hand result, since TX10 is a Design or Procedure
    # and so describes the activity rather than the result. This is a deliberate decision *not* to follow CRMtex's use
    # of TXP12 has_style, which is defined as a property of the result of the activity (the writing) rather than the activity itself,
    # because this seems to directly contradict the definition of TX10 Style as subclass of E29 Design or Procedure.
    # TODO: CHECK and follow up with the CRMtex folk.
    if pd.notna(hand['script_id']):
        script_uri = URIRef(f"http://digipal.eu/ontology#Script_{int(hand['script_id'])}")
        g.add((writing_uri, CRM.P33_used_specific_technique, script_uri))   # not TXP12, not hand_uri
    if pd.notna(hand['item_part_id']):
        item_uri = URIRef(f"http://digipal.eu/ontology#Item_{int(hand['item_part_id'])}")
        g.add((item_uri, RDF.type,      FRBRoo.F5_Item))
        g.add((hand_uri,  CRM.P46_is_composed_of, item_uri))
        itempart_uri = URIRef(f"http://digipal.eu/ontology#Item_Part_{int(hand['item_part_id'])}") 
        # PAS: Fixed itempart - hand relationship.
        g.add((itempart_uri, CRM['P56_bears_feature'], hand_uri))
    # PAS: Fixed Appearance
    if pd.notna(hand['appearance_id']):
        appearance_uri = URIRef(f"http://digipal.eu/ontology#Appearance_{int(hand['appearance_id'])}")
        g.add((hand_uri, CRM.P2_has_type, appearance_uri))
    if pd.notna(hand['glossed_text_id']):
        glossed_text_uri = URIRef(f"http://digipal.eu/ontology#Category_{int(hand['glossed_text_id'])}") 
        g.add((hand_uri,  CRM.P2_has_type, glossed_text_uri))
    # PAS: Latin Style is in fact a finer typology applied to arch:Script (e.g. Style I Anglo-Caroline minuscule),
    # so it's here modelled in the same way as arch:Script.
    # TODO: It would be easy and desirable to formally link the arch:LatinStyle to the arch:Script it's a substyle of,
    # and to unify the treatment of Latin and English in regard to arch:Script, arch:Style and arch:Appearance.
    if pd.notna(hand['latin_style_id']):
        latin_style_uri = URIRef(f"http://digipal.eu/ontology#LatinStyle_{int(hand['latin_style_id'])}") 
        g.add((writing_uri, CRM.P33_used_specific_technique, latin_style_uri))   # was: hand_uri, CRMtx.TXP12_has_style

# PAS: First, we build the chain for MediaPermission inheritance taken from Repository->MediaPermission.
# Repository-MediaPermission is not a direct legal assertion about the Repository (a repository doesn't hold rights over
# itself) — it's a fallback policy applied to all Images at that repository unless the Image
# has its own override. So we apply it here per-Image instead of at Repository level.
itempart_to_current_item = data['itempart'].set_index('id')['current_item_id'].to_dict()
current_item_to_repository = data['currentitem'].set_index('id')['repository_id'].to_dict()
repository_to_media_permission = data['repository'].set_index('id')['media_permission_id'].to_dict()

for _, image in data['image'].iterrows():
    image_uri = URIRef(f"http://digipal.eu/ontology#Image_{int(image['id'])}")
    g.add((image_uri, RDF.type,      CRM.E36_Visual_Item))
    if pd.notna(image['locus']):
        g.add((image_uri, EX.locus, Literal(image['locus'])))
    if pd.notna(image['caption']):
        g.add((image_uri, EX.caption, Literal(image['caption'])))
    if pd.notna(image['image']):
        g.add((image_uri, EX.image, Literal(image['image'])))
    if pd.notna(image['display_label']):
        g.add((image_uri, RDFS.label, Literal(image['display_label'])))
    if pd.notna(image['folio_side']):
        g.add((image_uri, EX.folio_side, Literal(image['folio_side'])))
    if pd.notna(image['iipimage']):
        g.add((image_uri, EX.iipimage, Literal(image['iipimage'])))
    if pd.notna(image['transcription']):
        g.add((image_uri, EX.transcription, Literal(image['transcription'])))
    if pd.notna(image['internal_notes']):
        g.add((image_uri, EX.internal_notes, Literal(image['internal_notes'])))
    if pd.notna(image['custom_label']):
        g.add((image_uri, EX.custom_label, Literal(image['custom_label'])))
    if pd.notna(image['width']): # à mettre dans un truc dimension 
        g.add((image_uri, EX.width, Literal(image['width'])))
    if pd.notna(image['height']): # à mettre dans un truc dimension
        g.add((image_uri, EX.height, Literal(image['height'])))
    if pd.notna(image['size']): # à mettre dans un truc dimension
        g.add((image_uri, EX.size, Literal(image['size'])))
    if pd.notna(image['keywords_string']):
        g.add((image_uri, EX.keywords_string, Literal(image['keywords_string'])))
    if pd.notna(image['quire']):
        g.add((image_uri, EX.quire, Literal(image['quire'])))
    if pd.notna(image['page_boundaries']):
        g.add((image_uri, EX.page_boundaries, Literal(image['page_boundaries'])))
    if pd.notna(image['item_part_id']):
        itempart_uri = URIRef(f"http://digipal.eu/ontology#Item_Part_{int(image['item_part_id'])}")
        g.add((image_uri,  CRM.P138_represents, itempart_uri))
    # PAS: Added new ImagePermission logic to pull from Repository if no Image-specific permission is provided.
    effective_media_permission_id = image['media_permission_id']
    if pd.isna(effective_media_permission_id) and pd.notna(image['item_part_id']):
        current_item_id = itempart_to_current_item.get(image['item_part_id'])
        if pd.notna(current_item_id):
            repository_id = current_item_to_repository.get(current_item_id)
            if pd.notna(repository_id):
                effective_media_permission_id = repository_to_media_permission.get(repository_id)

    if pd.notna(effective_media_permission_id):
        media_permission_uri = URIRef(f"http://digipal.eu/ontology#MediaPermission_{int(effective_media_permission_id)}")
        g.add((image_uri,  CRM.P104_is_subject_to, media_permission_uri))

for _, hand_image in data['hand_images'].iterrows():
    image_uri = URIRef(f"http://digipal.eu/ontology#Image_{int(hand_image['image_id'])}")
    hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{int(hand_image['hand_id'])}") 
    g.add((image_uri,  CRM.P138_represents, hand_uri))

for _, style in data['latinstyle'].iterrows():
    latin_style_uri = URIRef(f"http://digipal.eu/ontology#LatinStyle_{int(style['id'])}")
    g.add((latin_style_uri, RDF.type,      CRMtx.TX10_Style))
    if pd.notna(style['style']):
        g.add((latin_style_uri, RDFS.label, Literal(style['style'])))

# PAS: Added missing script table export
# Also NB that arch:Script is a TX10 Style, not a TX13 Script
for _, script in data['script'].iterrows():
    script_uri = URIRef(f"http://digipal.eu/ontology#Script_{int(script['id'])}")
    g.add((script_uri, RDF.type, CRMtx.TX10_Style))
    if pd.notna(script['name']):
        g.add((script_uri, RDFS.label, Literal(script['name'])))

# PAS: Fixed Appearance to be a Type associated with the Hand, rather than a formal Script associated with the Writing Activity
for _, appearance in data['appearance'].iterrows():
    appearance_uri = URIRef(f"http://digipal.eu/ontology#Appearance_{int(appearance['id'])}")
    g.add((appearance_uri, RDF.type, ARCH.Appearance))   # was: ARCH.Script
    g.add((appearance_uri, RDFS.label, Literal(f"Appearance {appearance['text']}")))   # was labelled "Script {...}"
    if pd.notna(appearance['text']):
        g.add((appearance_uri, EX.text, Literal(appearance['text'])))
    if pd.notna(appearance['sort_order']):
        g.add((appearance_uri, EX.sort_order, Literal(appearance['sort_order'])))
    if pd.notna(appearance['description']):
        g.add((appearance_uri, DCTERMS.description, Literal(appearance['description'])))

for _, media_permission in data['mediapermission'].iterrows():
    media_permission_uri = URIRef(f"http://digipal.eu/ontology#MediaPermission_{int(media_permission['id'])}")
    g.add((media_permission_uri, RDF.type, CRM.E30_Right))
    if pd.notna(media_permission['label']):
        g.add((media_permission_uri, RDFS.label, Literal(media_permission['label'])))
    if pd.notna(media_permission['display_message']):
        g.add((media_permission_uri, EX.display_message, Literal(media_permission['display_message'])))
    if pd.notna(media_permission['permission']):
        g.add((media_permission_uri, EX.permission, Literal(media_permission['permission'])))

for _, allograph in data['allograph'].iterrows():
    allograph_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{int(allograph['id'])}")
    g.add((allograph_uri, RDF.type, ARCH.Allograph))
    if pd.notna(allograph['name']):
        g.add((allograph_uri, RDFS.label, Literal(allograph['name'])))
    if pd.notna(allograph['default']):
        g.add((allograph_uri, EX.default, Literal(allograph['default'])))
    if pd.notna(allograph['hidden']):
        g.add((allograph_uri, EX.hidden, Literal(allograph['hidden'])))
    if pd.notna(allograph['illustration']):
        g.add((allograph_uri, EX.illustration, Literal(allograph['illustration'])))
    if pd.notna(allograph['character_id']):
        character_uri = URIRef(f"http://digipal.eu/ontology#Character_{int(allograph['character_id'])}")
        g.add((allograph_uri,  CRM.P138_represents, character_uri))

BEFORE_TYPE = URIRef("http://digipal.eu/ontology#Befor_Allograph")
g.add((BEFORE_TYPE, RDF.type, CRM.E55_Type))
g.add((BEFORE_TYPE, RDFS.label, Literal("Before", lang="en")))

AFTER_TYPE = URIRef("http://digipal.eu/ontology#After_Allograph")
g.add((AFTER_TYPE, RDF.type, CRM.E55_Type))
g.add((AFTER_TYPE, RDFS.label, Literal("After", lang="en")))

for _, annotation in data['annotation'].iterrows():
    annotation_uri = URIRef(f"http://digipal.eu/ontology#Annotation_{int(annotation['id'])}")
    g.add((annotation_uri, RDF.type, ANNO.Annotation)) 
    g.add((annotation_uri, RDFS.label, Literal(f"{annotation['id']}")))
    if pd.notna(annotation['cutout']):
        g.add((annotation_uri, EX.cutout, Literal(annotation['cutout'])))
    if pd.notna(annotation['geo_json']):
        g.add((annotation_uri, EX.geo_json, Literal(annotation['geo_json'])))
    if pd.notna(annotation['display_note']):
        g.add((annotation_uri, EX.display_note, Literal(annotation['display_note'])))
    if pd.notna(annotation['internal_note']):
        g.add((annotation_uri, EX.internal_note, Literal(annotation['internal_note'])))
    if pd.notna(annotation['rotation']):
        g.add((annotation_uri, EX.rotation, Literal(annotation['rotation'])))
    if pd.notna(annotation['holes']):
        g.add((annotation_uri, EX.holes, Literal(annotation['holes'])))
    if pd.notna(annotation['illustration_ductus']):
        g.add((annotation_uri, EX.illustration_ductus, Literal(annotation['illustration_ductus'])))
    if pd.notna(annotation['vector_id']):
        g.add((annotation_uri, EX.vector_id, Literal(annotation['vector_id'])))
    if pd.notna(annotation['image_id']):
        image_uri = URIRef(f"http://digipal.eu/ontology#Image_{int(annotation['image_id'])}")
        # PAS: Fixed annotation - image relationship. The annotation has a target which is the image, not the other way around,
        # and should use OpenAnnotations rather than CRM P138.
        g.add((annotation_uri, ANNO.hasTarget, image_uri))
    if pd.notna(annotation['status_id']):
        status_uri = URIRef(f"http://digipal.eu/ontology#Status_{int(annotation['status_id'])}")
        g.add((annotation_uri,  CRM.P2_has_type, status_uri)) #traiter status comme un E55_Type

    if pd.notna(annotation['graph_id']):
        graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{int(annotation['graph_id'])}")
        g.add((annotation_uri, ANNO.hasBody, graph_uri))
    #if pd.notna(annotation['author_id']): # est ce que c'est uile à garder 
        # PAS: Added relationship as dc.creator, but left commented out since this information is
        # systematically omitted from the export for all other cases.
        #author_uri = URIRef(f"http://digipal.eu/ontology#Author_{int(annotation['author_id'])}")
        #g.add((annotation_uri, DCTERMS.creator, author_uri))
# PAS: After/before barely used and not useful so ommited from export
#    if pd.notna(annotation['before_id']):
#        before_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{int(annotation['before_id'])}")
#        g.add((annotation_uri,  CRM.P148_has_component, before_uri))
#        g.add((before_uri, CRM.P2_has_type, BEFORE_TYPE))
#    if pd.notna(annotation['after_id']):
#        after_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{int(annotation['after_id'])}")
#        g.add((annotation_uri,  CRM.P148_has_component, after_uri)) 
#        g.add((after_uri, CRM.P2_has_type, AFTER_TYPE))

for _, graph in data['graph'].iterrows():
    graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{int(graph['id'])}")
    g.add((graph_uri, RDF.type, ARCH.Graph))
    if pd.notna(graph['display_label']):
        g.add((graph_uri, RDFS.label, Literal(graph['display_label'])))

    if pd.notna(graph['idiograph_id']):
        idiograph_uri = URIRef(f"http://digipal.eu/ontology#Idiograph_{int(graph['idiograph_id'])}")
        g.add((graph_uri,  CRM.P65_shows_visual_item, idiograph_uri))
    
    if pd.notna(graph['hand_id']):
        hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{int(graph['hand_id'])}")
        # PAS: Fixed hand - graph relationship. Hand and Graph are both E22_Man-Made_Object, so the relationship
        # should be P46_is_composed_of, not P106_is_composed_of which is for symbolic objects.
        g.add((hand_uri,  CRM.P46_is_composed_of, graph_uri))

for _, idiograph in data['idiograph'].iterrows():
    idiograph_uri = URIRef(f"http://digipal.eu/ontology#Idiograph_{int(idiograph['id'])}")
    g.add((idiograph_uri, RDF.type, ARCH.Idiograph))
    if pd.notna(idiograph['display_label']):
        g.add((idiograph_uri, RDFS.label, Literal(idiograph['display_label'])))

    if pd.notna(idiograph['allograph_id']):
        allograph_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{int(idiograph['allograph_id'])}")
        g.add((idiograph_uri,  CRM.P138_represents, allograph_uri))
    
for _, feature in data['feature'].iterrows():
    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{int(feature['id'])}")
    g.add((feature_uri, RDF.type, ARCH.Feature))
    if pd.notna(feature['name']):
        g.add((feature_uri, RDFS.label, Literal(feature['name'])))

for _, component in data['component'].iterrows():
    component_uri = URIRef(f"http://digipal.eu/ontology#Component_{int(component['id'])}")
    g.add((component_uri, RDF.type, ARCH.Component))
    if pd.notna(component['name']):
        g.add((component_uri, RDFS.label, Literal(component['name'])))

for _, allo_compo in data['allographcomponent'].iterrows():
    allo_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{int(allo_compo['allograph_id'])}")
    compo_uri = URIRef(f"http://digipal.eu/ontology#Component_{int(allo_compo['component_id'])}")
    # PAS: Fixed allograph - component relationship.
    g.add((allo_uri,  CRM['P148_has_component'], compo_uri)) 

# PAS: The fact that the RDB has two tables, graphcomponent and graphcomponent_feature, is an artefact of Django's M2M structure.
# Instead of reproducing that here, better to keep the conceptual part.
# Some properties are also adjusted to better reflect the conceptual model, particularly that 'Feature' in Archetype is really a Type in CIDOC-CRM.

# Component features, i.e. the list of all possible features that a given component could have.
# TODO: FIX!!
for _, compo_feature in data['component_features'].iterrows():
    compo_uri = URIRef(f"http://digipal.eu/ontology#Component_{int(compo_feature['component_id'])}")
    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{int(compo_feature['feature_id'])}")
    g.add((compo_uri, CRM['P2_has_type'], feature_uri))    # was P56_bears_feature

# Now we deal with actual Features recorded on Components of real annotated Graphs.
gc_features = data['graphcomponent_features'].merge(
    data['graphcomponent'],
    left_on='graphcomponent_id', right_on='id',
    suffixes=('', '_gc')
)
for _, gcf in gc_features.iterrows():
    graphcomponent_uri = URIRef(f"http://digipal.eu/ontology#GraphComponent_{int(gcf['graphcomponent_id'])}")
    g.add((graphcomponent_uri, RDF.type, ARCH.GraphComponent))

    graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{int(gcf['graph_id'])}")
    g.add((graph_uri, CRM['P46_is_composed_of'], graphcomponent_uri)) # TODO: What is superclass of GraphComponent? I guess E25, but then P138 doesn't work. CHECK! 

    component_uri = URIRef(f"http://digipal.eu/ontology#Component_{int(gcf['component_id'])}")
    g.add((graphcomponent_uri, CRM['P138_represents'], component_uri))

    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{int(gcf['feature_id'])}")
    g.add((graphcomponent_uri, CRM['P2_has_type'], feature_uri))


for _, item_owner in data['itempart_owners'].iterrows():
    itempart_uri = URIRef(f"http://digipal.eu/ontology#Item_Part_{int(item_owner['itempart_id'])}")
    owner_uri = URIRef(f"http://digipal.eu/ontology#Owner_{int(item_owner['owner_id'])}")
    g.add((itempart_uri,  CRM.P50_has_current_keeper, owner_uri)) 

for _, hand_desc in data['handdescription'].iterrows():
    hand_desc_uri = URIRef(f"http://digipal.eu/ontology#HandDescription_{int(hand_desc['id'])}")
    g.add((hand_desc_uri, RDF.type, CRM.E62_String))
    if pd.notna(hand_desc['label']):
        g.add((hand_desc_uri, RDFS.label, Literal(hand_desc['label'])))
    if pd.notna(hand_desc['description']):
        g.add((hand_desc_uri, DCTERMS.description, Literal(hand_desc['description'])))
    if pd.notna(hand_desc['hand_id']):
        hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{int(hand_desc['hand_id'])}")
        g.add((hand_uri,  CRM.P3_has_note, hand_desc_uri))
    if pd.notna(hand_desc['source_id']):
        source_uri = URIRef(f"http://digipal.eu/ontology#Source_{int(hand_desc['source_id'])}")
        g.add((source_uri,  CRM.P70i_is_documented_in, hand_desc_uri))

for _, scribe_ref in data['scribe_reference'].iterrows():
    scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{int(scribe_ref['scribe_id'])}")
    ref_uri = URIRef(f"http://digipal.eu/ontology#Reference_{int(scribe_ref['reference_id'])}")
    g.add((scribe_uri,  CRM.P70i_is_documented_in, ref_uri)) 

for _, reference in data['reference'].iterrows():
    ref_uri = URIRef(f"http://digipal.eu/ontology#Reference_{int(reference ['id'])}")
    g.add((ref_uri, RDF.type, CRM.E31_Document))
    if pd.notna(reference['name_index']):
        g.add((ref_uri, RDFS.label, Literal(reference['name_index'])))
    if pd.notna(reference['legacy_reference']):
        g.add((ref_uri, EX.legacy_reference, Literal(reference['legacy_reference'])))
    if pd.notna(reference['full_reference']):
        g.add((ref_uri, EX.full_reference, Literal(reference['full_reference'])))


for _, img_annot_status in data['imageannotationstatus'].iterrows():
    img_annot_status_uri = URIRef(f"http://digipal.eu/ontology#Status_{int(img_annot_status['id'])}")
    g.add((img_annot_status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(img_annot_status['name']):
        g.add((img_annot_status_uri, RDFS.label, Literal(img_annot_status['name'])))
    
for _, ontograph_type in data['ontographtype'].iterrows():
    ontograph_type_uri = URIRef(f"http://digipal.eu/ontology#OntographType_{int(ontograph_type['id'])}")
    g.add((ontograph_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(ontograph_type['name']):
        g.add((ontograph_type_uri, RDFS.label, Literal(ontograph_type['name'])))

for _, ontograph in data['ontograph'].iterrows():
    ontograph_uri = URIRef(f"http://digipal.eu/ontology#Ontograph_{int(ontograph['id'])}")
    g.add((ontograph_uri, RDF.type, ARCH.Ontograph))
    if pd.notna(ontograph['name']):
        g.add((ontograph_uri, RDFS.label, Literal(ontograph['name'])))
    if pd.notna(ontograph['ontograph_type_id']):
        ontograph_type_uri = URIRef(f"http://digipal.eu/ontology#OntographType_{int(ontograph['ontograph_type_id'])}")
        g.add((ontograph_uri,  CRM.P2_has_type, ontograph_type_uri )) 
    if pd.notna(ontograph['nesting_level']):
        g.add((ontograph_uri, EX.nesting_level, Literal(ontograph['nesting_level'])))
    if pd.notna(ontograph['sort_order']):
        g.add((ontograph_uri, EX.sort_order, Literal(ontograph['sort_order'])))

for _, scribe in data['scribe'].iterrows():
    scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{int(scribe['id'])}")
    g.add((scribe_uri, RDF.type, ARCH.Scribe))
    if pd.notna(scribe['name']):
        g.add((scribe_uri, RDFS.label, Literal(scribe['name'])))
    if pd.notna(scribe['scriptorium_id']):
        institution_uri = URIRef(f"http://digipal.eu/ontology#Institution_{int(scribe['scriptorium_id'])}")
        # PAS: Fixed reversed relationship between Scribe and Institution. The institution is the current or former member of the scribe, not the other way around.
        g.add((institution_uri, CRM.P107_has_current_or_former_member, scribe_uri))

for _, character in data['character'].iterrows():
    character_uri = URIRef(f"http://digipal.eu/ontology#Character_{int(character['id'])}")
    g.add((character_uri, RDF.type, ARCH.Character))
    if pd.notna(character['name']):
        g.add((character_uri, RDFS.label, Literal(character['name'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, EX.unicode_point, Literal(character['unicode_point'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, EX.unicode_point, Literal(character['unicode_point'])))
    if pd.notna((character['ontograph_id'])):
        ontograph_uri = URIRef(f"http://digipal.eu/ontology#Ontograph_{int(character['ontograph_id'])}")
        g.add((character_uri,  CRM.P138_represents, ontograph_uri)) 
    if pd.notna((character['form_id'])):
        form_uri = URIRef(f"http://digipal.eu/ontology#FormCharacter_{int(character['form_id'])}")
        g.add((character_uri,  CRM.P2_has_type, form_uri)) 

for _, character_compo in data['character_components'].iterrows():
    character_uri = URIRef(f"http://digipal.eu/ontology#Character_{int(character_compo['character_id'])}")
    component_uri = URIRef(f"http://digipal.eu/ontology#Component_{int(character_compo['component_id'])}")
    # PAS: Fixed character-component relationship.
    g.add((character_uri,  CRM['P148_has_component'], component_uri)) 

for _, form in data['characterform'].iterrows():
    form_uri = URIRef(f"http://digipal.eu/ontology#FormCharacter_{int(form['id'])}")
    g.add((form_uri, RDF.type, CRM.E55_Type))
    if pd.notna(form['name']):
        g.add((form_uri, RDFS.label, Literal(form['name'])))

for _, repository_type in data['ownertype'].iterrows():
    repository_type_uri = URIRef(f"http://digipal.eu/ontology#RepositoryType_{int(repository_type['id'])}")
    g.add((repository_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(repository_type['name']):
        g.add((repository_type_uri, RDFS.label, Literal(repository_type['name'])))

for _, source in data['source'].iterrows():
    source_uri = URIRef(f"http://digipal.eu/ontology#Source_{int(source['id'])}")
    g.add((source_uri, RDF.type, CRM.E31_Document))
    if pd.notna(source['label']):
        g.add((source_uri, RDFS.label, Literal(source['label'])))
    if pd.notna(source['name']):
        g.add((source_uri, EX.name, Literal(source['name'])))
    if pd.notna(source['priority']):
        g.add((source_uri, EX.priority, Literal(source['priority'])))
    if pd.notna(source['label_styled']):
        g.add((source_uri, EX.label_styled, Literal(source['label_styled'])))
    if pd.notna(source['label_slug']):
        g.add((source_uri, EX.label_slug, Literal(source['label_slug'])))

for _, status in data['status'].iterrows():
    status_uri = URIRef(f"http://digipal.eu/ontology#Status_{int(status['id'])}")
    g.add((status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(status['name']):
        g.add((status_uri, RDFS.label, Literal(status['name'])))
# -------------------------------------------------------- SERIALISATION --------------------------------------------------------
# PAS: Added timestamp to RDF output to help versioning and provenance tracking.

timestamp = datetime.now().strftime("%Y%m%d%H%M")
output_filename = f"data_rdf_digipal_cidoc_{timestamp}.rdf"
g.serialize(destination=output_filename, format="xml")
print(f"Exported to {output_filename}")
print(f"✓ Fichier RDF généré — {len(g)} triplets")
