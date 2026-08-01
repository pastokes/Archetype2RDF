# -------------------------------------------------------- LES IMPORTS -----------------------------------------------------------
import pandas as pd
import re
from sqlalchemy import create_engine, inspect
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, XSD

# -------------------------------------------------------- LES FONCTIONS ---------------------------------------------------------
def connection():
    mydb = create_engine("postgresql+psycopg://postgres:1234@localhost:5432/digipal")
    return mydb

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
FRBRoo = Namespace("http://iflastandards.info/ns/fr/frbr/frbroo/")  # FRBRoo
CRMtx  = Namespace("https://cidoc-crm.org/extensions/crmtex/html/CRMtex_v2.0.html/")   # CIDOC-TX
Gold = Namespace("https://static.vocabs.clariah.nl/docs/gold/2010.html/")  # Gold
Idiomcat = Namespace("https://classicmayan.org/documentations/catalogue.html/")  # Idiomcat
ANNO=Namespace("http://www.w3.org/ns/oa#") #Annotation Web
ARCH = Namespace("https://digipal.huma-num.fr/") 
EX   = Namespace("http://digipal.eu/ontology#")            
XSD_ = Namespace("http://www.w3.org/2001/XMLSchema#")

g.bind("crm",    CRM)
g.bind("frbroo", FRBRoo)
g.bind("crm-tx",    CRMtx)
g.bind("gold", Gold)
g.bind("idiomcat",    Idiomcat)
g.bind("archetype", ARCH)
g.bind("web_annotation", ANNO)
g.bind("ex",     EX)
g.bind("owl",    OWL)
g.bind("xsd",    XSD_)

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
g.add((ontologie, RDFS.seeAlso, URIRef("https://classicmayan.org/documentations/catalogue.html")))
g.add((ontologie, RDFS.seeAlso, URIRef("https://digipal.huma-num.fr/")))

#--------------------------------------- Declaration lien parents/enfants -----------------------------------------------------
# --- Item / FRBRoo F5 ---
g.add((FRBRoo.F5_Item, RDFS.subClassOf, CRM.E22_Human_Made_Object))
g.add((ARCH.Historical_Item, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Item_Part, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Current_Item, RDFS.subClassOf, FRBRoo.F5_Item))
g.add((ARCH.Historical_Item, RDFS.subClassOf, FRBRoo.F3_Manifestation))
g.add((ARCH.Item_Part, RDFS.subClassOf, FRBRoo.F3_Manifestation))

# --- Script / Style ---
g.add((ARCH.Script, RDFS.subClassOf, CRMtx.TX10_Style))
g.add((CRMtx.TX10_Style, RDFS.subClassOf, CRM.E29_Design_or_Procedure))

# --- Scribe ---
g.add((ARCH.Scribe, RDFS.subClassOf, CRM.E21_Person))

# --- Writing / Trace ---
g.add((ARCH.Trace, RDFS.subClassOf, CRMtx.TX2_Writing))

# --- Written Text ---
g.add((ARCH.Hand, RDFS.subClassOf, CRMtx.TX7_Written_Text_Segment))
g.add((ARCH.Graph, RDFS.subClassOf, CRMtx.TX7_Written_Text_Segment))
g.add((CRMtx.TX7_Written_Text_Segment, RDFS.subClassOf, CRMtx.TX1_Written_Text))
g.add((CRMtx.TX1_Written_Text, RDFS.subClassOf, CRM.E25_Human_Made_Feature))

# --- Allograph / Idiograph / Character ---
g.add((ARCH.Idiograph, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Allograph, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Character, RDFS.subClassOf, ARCH.Generalised_Allograph))
g.add((ARCH.Generalised_Allograph, RDFS.subClassOf, CRM.E36_Visual_Item))
g.add((ARCH.Component, RDFS.subClassOf, CRM.E36_Visual_Item))

# --- Grapheme / Ontograph ---
g.add((Idiomcat.Graph, RDFS.subClassOf, ARCH.Ontograph))
g.add((ARCH.Ontograph, RDFS.subClassOf, CRMtx.TX8_Grapheme))
g.add((CRMtx.TX8_Grapheme, RDFS.subClassOf, CRM.E55_Type))
g.add((ARCH.Ontograph, RDFS.subClassOf, CRM.E90_Symbolic_Object))
g.add((CRMtx.TX12_Grapheme_Sequence, RDFS.subClassOf, CRM.E90_Symbolic_Object))
g.add((CRMtx.TX11_Grapheme_Occurance, RDFS.subClassOf, CRMtx.TX12_Grapheme_Sequence))

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
g.add((CRM.E52_Time_Span, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E53_Place, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E54_Dimension, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E59_Primitive_Value, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E61_Time_Primitive, RDFS.subClassOf, CRM.E59_Primitive_Value))
g.add((CRM.E62_String, RDFS.subClassOf, CRM.E59_Primitive_Value))
g.add((CRM.E77_Persistent_Item, RDFS.subClassOf, CRM.E1_CRM_Entity))
g.add((CRM.E39_Actor, RDFS.subClassOf, CRM.E77_Persistent_Item))
g.add((CRM.E70_Thing, RDFS.subClassOf, CRM.E77_Persistent_Item))

# --- GOLD  ---
g.add((Gold.Abstract, RDFS.subClassOf, CRM.E77_Persistent_Item))
g.add((Gold.LinguisticDataStructure, RDFS.subClassOf, Gold.Abstract))
g.add((Gold.FeatureSystem, RDFS.subClassOf, Gold.LinguisticDataStructure))

# --- E70 Thing : Human Made Thing / Legal Object ---
g.add((CRM.E71_Human_Made_Thing, RDFS.subClassOf, CRM.E70_Thing))
g.add((CRM.E72_Legal_Object, RDFS.subClassOf, CRM.E70_Thing))
g.add((CRM.E24_Physical_Human_Made_Thing, RDFS.subClassOf, CRM.E71_Human_Made_Thing))
g.add((CRM.E22_Human_Made_Object, RDFS.subClassOf, CRM.E24_Physical_Human_Made_Thing))
g.add((CRM.E25_Human_Made_Feature, RDFS.subClassOf, CRM.E24_Physical_Human_Made_Thing))
g.add((CRM.E28_Conceptual_Object, RDFS.subClassOf, CRM.E71_Human_Made_Thing))
g.add((ARCH.Element_of_Style, RDFS.subClassOf, CRM.E28_Conceptual_Object))

# --- E55 Type ---
g.add((CRM.E55_Type, RDFS.subClassOf, CRM.E28_Conceptual_Object))
g.add((ARCH.Feature, RDFS.subClassOf, CRM.E55_Type))
g.add((CRM.E56_Language, RDFS.subClassOf, CRM.E55_Type))
g.add((CRM.E57_Material, RDFS.subClassOf, CRM.E55_Type))
g.add((CRM.E58_Measurement_Unit, RDFS.subClassOf, CRM.E55_Type))
g.add((FRBRoo.F3_Manifestation, RDFS.subClassOf, CRM.E55_Type))

# --- E89 Propositional Object / E73 Information Object ---
g.add((CRM.E89_Propositional_Object, RDFS.subClassOf, CRM.E28_Conceptual_Object))
g.add((CRM.E73_Information_Object, RDFS.subClassOf, CRM.E89_Propositional_Object))
g.add((CRM.E31_Document, RDFS.subClassOf, CRM.E73_Information_Object))
g.add((CRM.E33_Linguistic_Object, RDFS.subClassOf, CRM.E73_Information_Object))
g.add((CRM.E34_Inscription, RDFS.subClassOf, CRM.E33_Linguistic_Object))
g.add((Idiomcat.Sign, RDFS.subClassOf, CRM.E33_Linguistic_Object))
g.add((Idiomcat.Sign_Function, RDFS.subClassOf, CRM.E33_Linguistic_Object))
g.add((Idiomcat.Graph, RDFS.subClassOf, CRM.E33_Linguistic_Object))
g.add((CRM.E36_Visual_Item, RDFS.subClassOf, CRM.E73_Information_Object))
g.add((ARCH.Component, RDFS.subClassOf, CRM.E36_Visual_Item))
g.add((ARCH.Generalised_Allograph, RDFS.subClassOf, CRM.E36_Visual_Item))
g.add((CRM.E37_Mark, RDFS.subClassOf, CRM.E36_Visual_Item))
g.add((CRM.E34_Inscription, RDFS.subClassOf, CRM.E37_Mark))
g.add((CRM.E29_Design_or_Procedure, RDFS.subClassOf, CRM.E73_Information_Object))
g.add((ARCH.Script, RDFS.subClassOf, CRM.E29_Design_or_Procedure))
g.add((CRMtx.TX3_Writing_System, RDFS.subClassOf, CRM.E29_Design_or_Procedure))
g.add((CRM.E34_Inscription, RDFS.subClassOf, CRM.E73_Information_Object))

# --- E90 Symbolic Object ---
g.add((CRM.E90_Symbolic_Object, RDFS.subClassOf, CRM.E28_Conceptual_Object))
g.add((CRM.E41_Appellation, RDFS.subClassOf, CRM.E90_Symbolic_Object))
g.add((CRM.E42_Identifier, RDFS.subClassOf, CRM.E41_Appellation))
g.add((CRM.E61_Time_Primitive, RDFS.subClassOf, CRM.E41_Appellation))
g.add((CRM.E73_Information_Object, RDFS.subClassOf, CRM.E90_Symbolic_Object))

# --- E72 Legal Object ---
g.add((CRM.E18_Physical_Thing, RDFS.subClassOf, CRM.E72_Legal_Object))
g.add((CRM.E19_Physical_Object, RDFS.subClassOf, CRM.E18_Physical_Thing))
g.add((CRM.E20_Biological_Object, RDFS.subClassOf, CRM.E19_Physical_Object))
g.add((CRM.E21_Person, RDFS.subClassOf, CRM.E20_Biological_Object))
g.add((CRM.E22_Human_Made_Object, RDFS.subClassOf, CRM.E19_Physical_Object))
g.add((CRM.E24_Physical_Human_Made_Thing, RDFS.subClassOf, CRM.E18_Physical_Thing))
g.add((CRM.E26_Physical_Feature, RDFS.subClassOf, CRM.E72_Legal_Object))
g.add((CRM.E25_Human_Made_Feature, RDFS.subClassOf, CRM.E26_Physical_Feature))
g.add((CRM.E90_Symbolic_Object, RDFS.subClassOf, CRM.E72_Legal_Object))

# ------------------------- TX13 Script -----------------------------------
g.add((CRMtx.TX13_Script, RDFS.subClassOf, CRM.E89_Propositional_Object))
g.add((CRM.E89_Propositional_Object, RDFS.subClassOf, CRM.E28_Conceptual_Object ))

# -------------------------------------------------------- HISTORICALITEM → frbr:F5 Item --------------------------------
TYPE_HISTITEM = URIRef("http://digipal.eu/ontology#TYPE_HistoricalItem")
g.add((TYPE_HISTITEM, RDF.type, CRM.E55_Type))
g.add((TYPE_HISTITEM, RDFS.label, Literal("Type", lang="en")))

for _, row in data['historicalitem'].iterrows():

    hist_item = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{row['id']}")
    g.add((hist_item, RDF.type,      ARCH.Historical_Item))
    if pd.notna(row['name']):
        g.add((hist_item, RDFS.label, Literal(row['name'])))
    if pd.notna(row['catalogue_number']):
        # Nettoyer la valeur pour l'URI : remplacer les caractères invalides par _
        catalogue_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', str(row['catalogue_number']))
        catalogue_number_uri = URIRef(f"http://digipal.eu/ontology#CatalogueNumber_{catalogue_clean}")

        g.add((catalogue_number_uri, RDF.type,   CRM.E42_Identifier))
        g.add((catalogue_number_uri, EX.cataloguenumber, Literal(str(row['catalogue_number']))))  # valeur originale conservée ici
        g.add((hist_item, CRM.P1_is_identified_by, catalogue_number_uri))

    # --- Type de manuscrit → E55 Type (lien vers HistoricalItemType) ---
    if pd.notna(row['historical_item_type_id']):
        type_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItemType_{int(row['historical_item_type_id'])}")
        #g.add((type_uri,   RDF.type,   CRM.E55_Type))
        g.add((hist_item,  CRM.P2_has_type, type_uri))             
        g.add((type_uri,  CRM.P2_has_type, TYPE_HISTITEM))
        
    # --- Langue → E56 Language ---
    if pd.notna(row['language_id']):
        langue_uri = URIRef(f"http://digipal.eu/ontology#Language_{row['language_id']}")
        g.add((langue_uri, RDF.type,   CRM.E56_Language))
        g.add((hist_item,  CRM.P72_has_language, langue_uri))     

    if pd.notna(row['date']) or pd.notna(row['date_sort']):
        spacetime_volume_uri  = URIRef(f"http://digipal.eu/ontology#SpacetimeVolume_{row['id']}")

        g.add((spacetime_volume_uri,  RDF.type,              CRM.E92_Spacetime_Volume))     
        g.add((hist_item,  CRM.P196i_is_defined_by, spacetime_volume_uri))          
             
        if pd.notna(row['date']):
            g.add((spacetime_volume_uri, RDFS.label, Literal(str(row['date']))))

    if pd.notna(row['url']):
        g.add((hist_item, EX.url, Literal(str(row['url']))))

    if pd.notna(row['vernacular']):
        g.add((hist_item, EX.vernacular, Literal(bool(row['vernacular']))))
    if pd.notna(row['neumed']):
        g.add((hist_item, EX.neumed, Literal(bool(row['neumed']))))
    if pd.notna(row['legacy_reference']):
        g.add((hist_item, EX.legacy_reference, Literal(str(row['legacy_reference']))))
    
    if pd.notna(row['historical_item_format_id']):
        format_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItemFormat_{row['historical_item_format_id']}")
        g.add((hist_item,  CRM.P2_has_type, format_uri)) 

FORMAT_TYPE = URIRef("http://digipal.eu/ontology#type_Format")
g.add((FORMAT_TYPE, RDF.type, CRM.E55_Type))
g.add((FORMAT_TYPE, RDFS.label, Literal("Format", lang="en")))

for _, format in data['format'].iterrows():
    hist_item_format = URIRef(f"http://digipal.eu/ontology#HistoricalItemFormat_{format['id']}")
    g.add((hist_item_format, RDF.type, CRM.E55_Type))
    g.add((hist_item_format, RDFS.label, Literal(str(format['name']))))
    g.add((hist_item_format, CRM.P2_has_type, FORMAT_TYPE))               

for _, a in archive.iterrows():
    hist_item_archive = URIRef(f"http://digipal.eu/ontology#HistoricalItemArchive_{a['id']}")
    g.add((hist_item_archive, RDF.type, CRM.E73_Information_Object))
    g.add((hist_item_archive, RDFS.label, Literal(str(f"archive {a['id']}")))) 
    g.add((hist_item_archive, EX.dubitable, Literal(str(a['dubitable'])))) 
    if pd.notna(a['object_id']) and str(a['content_type_id']) == '43':
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{int(a['object_id'])}")
        g.add((hist_item_archive, CRM.P50_has_current_keeper, place_uri))
    elif pd.notna(a['object_id']) and str(a['content_type_id']) != '43':
        print("Le type de object_id dans historicalitem n'est pas pris en compte à modifier")

# --- DEFINITION DES TYPES DE PLACE ---
REGION_TYPE = URIRef("http://digipal.eu/ontology#Type_Region")
g.add((REGION_TYPE, RDF.type, CRM.E55_Type))
g.add((REGION_TYPE, RDFS.label, Literal("Région", lang="en")))

CURRENT_COUNTY_TYPE = URIRef("http://digipal.eu/ontology#Type_Current_County")
g.add((CURRENT_COUNTY_TYPE, RDF.type, CRM.E55_Type))
g.add((CURRENT_COUNTY_TYPE, RDFS.label, Literal("Current County", lang="en")))

HISTORICAL_COUNTY_TYPE = URIRef("http://digipal.eu/ontology#Type_Historical_County")
g.add((HISTORICAL_COUNTY_TYPE, RDF.type, CRM.E55_Type))
g.add((HISTORICAL_COUNTY_TYPE, RDFS.label, Literal("Historical County", lang="en")))

FONDATION_TYPE = URIRef("http://digipal.eu/ontology#Type_Fondation")
g.add((FONDATION_TYPE, RDF.type, CRM.E55_Type))
g.add((FONDATION_TYPE, RDFS.label, Literal("Fondation", lang="en")))

REFONDATION_TYPE = URIRef("http://digipal.eu/ontology#Type_Refondation")
g.add((REFONDATION_TYPE, RDF.type, CRM.E55_Type))
g.add((REFONDATION_TYPE, RDFS.label, Literal("Refondation", lang="en")))

for _, p in data['place'].iterrows():
    place_uri = URIRef(f"http://digipal.eu/ontology#Place_{p['id']}")
    g.add((place_uri, RDF.type,      CRM.E53_Place))  
    g.add((place_uri, RDFS.label, Literal(str(p['name']))))
    if pd.notna(p['eastings']):
        g.add((place_uri, EX.eastings, Literal(str(p['eastings']))))
    if pd.notna(p['northings']):
        g.add((place_uri, EX.northings, Literal(str(p['northings']))))
    if pd.notna(p['region_id']): 
        region_uri = URIRef(f"http://digipal.eu/ontology#Region_{p['region_id']}")
        g.add((region_uri, CRM.P2_has_type, REGION_TYPE))
        g.add((place_uri, CRM.P89_falls_within, region_uri))

    if pd.notna(p['current_county_id']):
        current_county_uri = URIRef(f"http://digipal.eu/ontology#CurrentCounty_{p['current_county_id']}")
        g.add((current_county_uri, CRM.P2_has_type, CURRENT_COUNTY_TYPE))
        g.add((place_uri, CRM.P89_falls_within, current_county_uri))
    
    if pd.notna(p['historical_county_id']):
        historical_county_uri = URIRef(f"http://digipal.eu/ontology#County_{p['historical_county_id']}")
        g.add((historical_county_uri, CRM.P2_has_type, HISTORICAL_COUNTY_TYPE))
        g.add((place_uri, CRM.P89_falls_within, historical_county_uri))

for _, county in data['county'].iterrows():
    county_uri = URIRef(f"http://digipal.eu/ontology#County_{county['id']}")
    g.add((county_uri, RDF.type,      CRM.E53_Place))  
    g.add((county_uri, RDFS.label, Literal(str(county['name']))))

for _, county in data['county'].iterrows():
    county_uri = URIRef(f"http://digipal.eu/ontology#County_{county['id']}")
    g.add((county_uri, RDF.type,      CRM.E53_Place))  
    g.add((county_uri, RDFS.label, Literal(str(county['name']))))

for _, region in data['region'].iterrows():
    region_uri = URIRef(f"http://digipal.eu/ontology#Region_{region['id']}")
    g.add((region_uri, RDF.type,      CRM.E53_Place))  
    g.add((region_uri, RDFS.label, Literal(str(region['name']))))

for _, i in data['institution'].iterrows():
    insti = URIRef(f"http://digipal.eu/ontology#Institution_{i['id']}")
    g.add((insti, RDF.type, CRM.E74_Group))
    g.add((insti, RDFS.label, Literal(str(i['name']))))

    if pd.notna(i['foundation']):
        insti_foundation = URIRef(f"http://digipal.eu/ontology#InstiFoundation_{i['id']}")
        g.add((insti_foundation, RDF.type, CRM.E66_Formation))
        g.add((insti, CRM.P95_has_formed, insti_foundation))
        g.add((insti_foundation, EX.foundation, Literal(str(i['foundation']))))
        if pd.notna(i['founder_id']): 
            founder_insti=URIRef(f"http://digipal.eu/ontology#Person_{i['founder_id']}")
            g.add((insti_foundation, CRM.P14_carried_out_by, founder_insti))
        g.add((insti_foundation, CRM.P2_has_type, FONDATION_TYPE))
    
    if pd.notna(i['refoundation']):
        if pd.notna(i['founder_id']):
            founder_insti=URIRef(f"http://digipal.eu/ontology#Person_{i['founder_id']}")
            insti_refoundation = URIRef(f"http://digipal.eu/ontology#InstiFoundation_{i['id']}")
            g.add((insti_refoundation, RDF.type, CRM.E8_Acquisition))
            g.add((founder_insti, CRM.P95_has_formed, insti_refoundation))
            g.add((insti_refoundation, EX.refoundation, Literal(str(i['refoundation']))))
            if pd.notna(i['reformer_id']): 
                reformer_insti=URIRef(f"http://digipal.eu/ontology#Person_{i['reformer_id']}")
                g.add((insti_refoundation, CRM.P22_transferred_title_to, reformer_insti))
        else : 
            insti_refoundation = URIRef(f"http://digipal.eu/ontology#InstiRefoundation_{i['id']}")
            g.add((insti_refoundation, RDF.type, CRM.E66_Formation))
            g.add((insti, CRM.P95_has_formed, insti_refoundation))
            g.add((insti_refoundation, EX.refoundation, Literal(str(i['refoundation']))))
            if pd.notna(i['reformer_id']): 
                refounder_insti=URIRef(f"http://digipal.eu/ontology#Person_{i['reformer_id']}")
                g.add((insti_refoundation, CRM.P14_carried_out_by, refounder_insti))
        g.add((insti_refoundation, CRM.P2_has_type, REFONDATION_TYPE))

    if pd.notna(i['institution_type_id']):
        type_insti_uri = URIRef(f"http://digipal.eu/ontology#InstitutionType_{i['institution_type_id']}")
        g.add((insti, CRM.P2_has_type, type_insti_uri))

    if pd.notna(i['place_id']):
        place_insti_uri = URIRef(f"http://digipal.eu/ontology#Place_{i['place_id']}")
        g.add((place_insti_uri, RDF.type, CRM.E53_Place))
        g.add((insti, CRM.P74_has_current_or_former_residence, place_insti_uri))
    
    if pd.notna(i['patron_id']): 
        patron_insti=URIRef(f"http://digipal.eu/ontology#Person_{i['patron_id']}")
        g.add((insti, CRM.P198i_held_or_supported_by, patron_insti))

for _, inst_type in data['institutiontype'].iterrows():
    insti_type= URIRef(f"http://digipal.eu/ontology#InstitutionType_{inst_type['id']}")
    g.add((insti_type, RDF.type, CRM.E55_Type))
    g.add((insti_type, RDFS.label, Literal(str(inst_type['name']))))

for _, pers in data['person'].iterrows():
    insti = URIRef(f"http://digipal.eu/ontology#Person_{pers['id']}")
    g.add((insti, RDF.type, CRM.E21_Person))
    g.add((insti, RDFS.label, Literal(str(pers['name']))))

for _, item in data['itempart'].iterrows():
    itempart= URIRef(f"http://digipal.eu/ontology#Itempart_{item['id']}")
    g.add((itempart, RDF.type,      ARCH.Item_Part))
    if pd.notna(item['display_label']):
        g.add((itempart, RDFS.label, Literal(item['display_label'])))
    if pd.notna(item['pagination']):
        g.add((itempart, EX.pagination, Literal(item['pagination'])))
    if pd.notna(item['notes']):
        g.add((itempart, RDFS.comment, Literal(item['notes'])))
    if pd.notna(item['current_item_id']):
        F5_item_uri = URIRef(f"http://digipal.eu/ontology#Item_{item['id']}")
        current_item_uri = URIRef(f"http://digipal.eu/ontology#CurrentItem_{item['current_item_id']}")
        g.add((current_item_uri,  CRM.P46_is_composed_of, itempart))
        g.add((current_item_uri,  OWL.sameAs, F5_item_uri))

for _, part in data['itempartitem'].iterrows():
    hist= URIRef(f"http://digipal.eu/ontology#HistoricalItem_{part['historical_item_id']}")
    item= URIRef(f"http://digipal.eu/ontology#Itempart_{part['item_part_id']}")
    g.add((hist,  CRM.P46_is_composed_of, item))
    

    #Création lien entre hand et historicaldate/Writing
    F5_item_uri = URIRef(f"http://digipal.eu/ontology#Itempart_{part['item_part_id']}")
    histdate= URIRef(f"http://digipal.eu/ontology#Writing_{part['historical_item_id']}")
    g.add((histdate,  CRM.P92_brought_into_existance, F5_item_uri))

    #Création F5 item et F3 Manifestation 
    F3_Manifestation_uri = URIRef(f"http://digipal.eu/ontology#Manifestation_{part['item_part_id']}")
    g.add((F3_Manifestation_uri, RDF.type, FRBRoo.F3_Manifestation))
    g.add((F5_item_uri, RDF.type, FRBRoo.F3_Item))
    g.add((hist, OWL.sameAs, F5_item_uri))
    g.add((item, OWL.sameAs, F5_item_uri))
    g.add((hist, OWL.sameAs, F3_Manifestation_uri))
    g.add((item, OWL.sameAs,F3_Manifestation_uri))


for _, origin in data['itemorigin'].iterrows():
    #origin_uri= URIRef(f"http://digipal.eu/ontology#ItemOrigin_{origin['id']}")
    histdate= URIRef(f"http://digipal.eu/ontology#Writing_{origin['historical_item_id']}")
    #g.add((origin_uri, RDF.type, CRMtx.TX))
    g.add((histdate, EX.dubitable, Literal(origin['dubitable'])))

    if pd.notna(origin['place_id']):
        place= URIRef(f"http://digipal.eu/ontology#Place_{origin['place_id']}")
        g.add((histdate,  CRM.P7_took_place_at, place))
    if pd.notna(origin['institution_id']):
        institution =  URIRef(f"http://digipal.eu/ontology#Institution_{origin['institution_id']}")
        g.add((histdate,  CRM.P11_had_participant, institution))

MEASUREMENT_UNIT = URIRef("http://digipal.eu/ontology#Measurement_Unit_millimeter")
g.add((MEASUREMENT_UNIT, RDF.type, CRM.E58_Measurement_Unit))
g.add((MEASUREMENT_UNIT, RDFS.label, Literal("Millimeter", lang="en")))

for _, layout in data['layout'].iterrows():
    layout_uri = URIRef(f"http://digipal.eu/ontology#Layout_historicalItem_{layout['historical_item_id']}") 
    dimension_uri = URIRef(f"http://digipal.eu/ontology#Dimension_historicalItem_{layout['historical_item_id']}")
    g.add((layout_uri, RDF.type, CRM.E18_Physical_Thing))
    g.add((dimension_uri, RDF.type, CRM.E54_Dimension))

    g.add((layout_uri, RDFS.label, Literal(f"Layout {layout['id']}")))
    g.add((dimension_uri, RDFS.label, Literal(f"Dimension {layout['id']}")))

    if pd.notna(layout['page_height']):
        g.add((dimension_uri, EX.page_height, Literal(layout['page_height'])))
    if pd.notna(layout['page_width']):
        g.add((dimension_uri, EX.page_width, Literal(layout['page_width'])))
    if pd.notna(layout['frame_height']):
        g.add((dimension_uri, EX.frame_height, Literal(layout['frame_height'])))
    if pd.notna(layout['frame_width']):
        g.add((dimension_uri, EX.frame_width, Literal(layout['frame_width'])))
    if pd.notna(layout['tramline_width']):
        g.add((dimension_uri, EX.tramline_width, Literal(layout['tramline_width'])))
    
    if pd.notna(layout['lines']):
        g.add((layout_uri, EX.lines, Literal(layout['lines'])))
    if pd.notna(layout['columns']):
        g.add((layout_uri, EX.columns, Literal(layout['columns'])))
    if pd.notna(layout['on_top_line']):
        g.add((layout_uri, EX.on_top_line, Literal(layout['on_top_line'])))
    if pd.notna(layout['multiple_sheet_rulling']):
        g.add((layout_uri, EX.columns, Literal(layout['multiple_sheet_rulling'])))
    if pd.notna(layout['bilinear_ruling']):
        g.add((layout_uri, EX.bilinear_ruling, Literal(layout['bilinear_ruling'])))
    if pd.notna(layout['comments']):
        g.add((layout_uri, RDFS.comment, Literal(layout['comments'])))
    if pd.notna(layout['insular_pricking']):
        g.add((layout_uri, EX.columns, Literal(layout['insular_pricking'])))

    if pd.notna(layout['hair_arrangement_id']):
        hair =  URIRef(f"http://digipal.eu/ontology#Hair_{layout['hair_arrangement_id']}")
        g.add((layout_uri,  CRM.P45_consits_of, hair))

    if pd.notna(layout['item_part_id']):
        itempart_layout =  URIRef(f"http://digipal.eu/ontology#Itempart_{layout['item_part_id']}")
        g.add((itempart_layout,  CRM.P46_is_composed_of, layout_uri))

        if pd.notna(layout['page_height']) or pd.notna(layout['page_width']) or pd.notna(layout['frame_height']) or pd.notna(layout['frame_width']) or pd.notna(layout['tramline_width']):
            g.add((itempart_layout,  CRM.P43_has_dimension, dimension_uri))

for _, hair in data['hair'].iterrows():
    hair_uri =  URIRef(f"http://digipal.eu/ontology#Hair_{hair['id']}")
    g.add((hair_uri, RDF.type,      CRM.E57_Material))    
    if pd.notna(hair['label']):
        g.add((hair_uri, RDFS.label, Literal(hair['label'])))

CAT_HISTITEM = URIRef("http://digipal.eu/ontology#Category_HistoricalItem")
g.add((CAT_HISTITEM , RDF.type, CRM.E55_Type))
g.add((CAT_HISTITEM , RDFS.label, Literal("Category", lang="en")))

for _, category in data['category'].iterrows(): 
    category_uri = URIRef(f"http://digipal.eu/ontology#Category_{category['id']}")
    g.add((category_uri,  CRM.P2_has_type, CAT_HISTITEM))
    g.add((category_uri, RDF.type,      CRM.E55_Type))
    if pd.notna(category['name']):
        g.add((category_uri, RDFS.label, Literal(category['name'])))
    if pd.notna(category['sort_order']):
        g.add((category_uri, EX.sort_order, Literal(category['sort_order'])))

for _, hist_cat in data['historicalitem_categories'].iterrows():
    cat_uri = URIRef(f"http://digipal.eu/ontology#Category_{hist_cat['category_id']}")
    hist_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{hist_cat['historicalitem_id']}")
    g.add((hist_uri,  CRM.P2_has_type, cat_uri))

for _, language in data['language'].iterrows():
    language_uri = URIRef(f"http://digipal.eu/ontology#Language_{language['id']}")
    g.add((language_uri, RDF.type,      CRM.E56_Language))          # classe locale pour filtrer facilement
    if pd.notna(language['name']):
        g.add((language_uri, RDFS.label, Literal(language['name'])))

COLLATION_type = URIRef("http://digipal.eu/ontology#Collation")
g.add((COLLATION_type, RDF.type, CRM.E55_Type))
g.add((COLLATION_type,  RDFS.label, Literal("Collation", lang="en")))

DECORATION_type = URIRef("http://digipal.eu/ontology#Decoration")
g.add((DECORATION_type, RDF.type, CRM.E55_Type))
g.add((DECORATION_type,  RDFS.label, Literal("Decoration", lang="en")))

for _, collation in data['collation'].iterrows():
    collation_uri = URIRef(f"http://digipal.eu/ontology#Collation_{collation['id']}")
    g.add((collation_uri, RDF.type,      CRM.E18_Physical_Thing))
    g.add((collation_uri,  CRM.P2_has_type, COLLATION_type))
    g.add((collation_uri, RDFS.label, Literal(f"Collation {collation['id']}")))
    if pd.notna(collation['fragment']):
        g.add((collation_uri, EX.fragment, Literal(collation['fragment'])))
    if pd.notna(collation['leaves']):
        g.add((collation_uri, EX.fragment, Literal(collation['leaves'])))
    if pd.notna(collation['front_flyleaves']):
        g.add((collation_uri, EX.fragment, Literal(collation['front_flyleaves'])))
    if pd.notna(collation['back_flyleaves']):
        g.add((collation_uri, EX.fragment, Literal(collation['back_flyleaves'])))
    if pd.notna(collation['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{collation['historical_item_id']}")
        g.add((hist_uri,  CRM.P46_is_composed_of, collation_uri))

for _, deco in data['decoration'].iterrows():
    deco_uri = URIRef(f"http://digipal.eu/ontology#Decoration_{deco['id']}")
    g.add((deco_uri, RDF.type,      CRM.E18_Physical_Thing))
    g.add((deco_uri,  CRM.P2_has_type, DECORATION_type))
    g.add((deco_uri, RDFS.label, Literal(f"Decoration {deco['id']}")))
    if pd.notna(deco['illustrated']):
        g.add((deco_uri, EX.illustrated, Literal(deco['illustrated'])))

    if pd.notna(deco['decorated']):
        g.add((deco_uri, EX.decorated, Literal(deco['decorated'])))

    if pd.notna(deco['num_colours']):
        g.add((deco_uri, EX.num_colours, Literal(deco['num_colours'])))

    if pd.notna(deco['colours']):
        g.add((deco_uri, EX.colours, Literal(deco['colours'])))
    
    if pd.notna(deco['num_inks']):
        g.add((deco_uri, EX.num_inks, Literal(deco['num_inks'])))
    
    if pd.notna(deco['inks']):
        g.add((deco_uri, EX.inks, Literal(deco['inks'])))
    
    if pd.notna(deco['style']):
        g.add((deco_uri, EX.style, Literal(deco['style'])))
    
    if pd.notna(deco['description']):
        g.add((deco_uri, EX.description, Literal(deco['description'])))

    if pd.notna(deco['catalogue_references']):
        g.add((deco_uri, EX.catalogue_references, Literal(deco['catalogue_references'])))

    if pd.notna(deco['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{deco['historical_item_id']}")
        g.add((hist_uri,  CRM.P46_is_composed_of, deco_uri))

for _, hist_date in data['historicalitemdate'].iterrows():
    writing_uri = URIRef(f"http://digipal.eu/ontology#Writing_{hist_date['id']}")
    g.add((writing_uri, RDF.type,      CRMtx.TX2_Writing))
    g.add((writing_uri, RDFS.label, Literal(f"Writing {hist_date['id']}")))
    if pd.notna(hist_date['historical_item_id']):
        hist_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{hist_date['historical_item_id']}")
        g.add((hist_uri,  CRM.P65_shows_visual_item, writing_uri))
    if pd.notna(hist_date['date_id']):
        date_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{hist_date['date_id']}")
        g.add((writing_uri,  CRM.P8_took_place_on_or_within, date_uri))
        
    if pd.notna(hist_date['evidence']):
        g.add((writing_uri, EX.evidence, Literal(hist_date['evidence'])))
    if pd.notna(hist_date['vernacular']):
        g.add((writing_uri, EX.vernacular, Literal(hist_date['vernacular'])))
    if pd.notna(hist_date['addition']):
        g.add((writing_uri, EX.addition, Literal(hist_date['addition'])))
    if pd.notna(hist_date['dubitable']):
        g.add((writing_uri, EX.dubitable, Literal(hist_date['dubitable'])))
    
    

for _, date in data['date'].iterrows():
    date_period_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{date['id']}")
    g.add((date_period_uri, RDF.type,      CRM.E4_Period))
    g.add((date_period_uri, RDFS.label, Literal(f"Date {date['id']}")))
    g.add((date_period_uri, EX.date, Literal(date['date'])))
    g.add((date_period_uri, EX.sort_order, Literal(date['sort_order'])))
    g.add((date_period_uri, EX.band, Literal(date['band'])))
    g.add((date_period_uri, EX.weight, Literal(date['weight'])))
    g.add((date_period_uri, EX.additional_band, Literal(date['additional_band'])))
    g.add((date_period_uri, EX.post_conquest, Literal(date['post_conquest'])))
    g.add((date_period_uri, EX.s_xi, Literal(date['s_xi'])))
    
    date_timespan_uri = URIRef(f"http://digipal.eu/ontology#Date_TimeSpan_{date['id']}")
    g.add((date_period_uri,  CRM.P4_has_time_span, date_timespan_uri))
    g.add((date_timespan_uri, RDF.type,      CRM.E52_Time_Span)) 
    g.add((date_timespan_uri, RDFS.label, Literal(f"Timespan {date['id']}")))
    g.add((date_timespan_uri, EX.min_weight, Literal(date['min_weight'])))
    g.add((date_timespan_uri, EX.max_weight, Literal(date['max_weight'])))

    if pd.notna(date['evidence']):
        date_document_uri = URIRef(f"http://digipal.eu/ontology#Date_Document_{date['id']}")
        g.add((date_period_uri,  CRM.P70i_is_documented_in, date_document_uri))
        g.add((date_document_uri, RDF.type,      CRM.E31_Document)) 
        g.add((date_document_uri, EX.evidence, Literal(date['evidence'])))

for _, desc in data['description'].iterrows():
    description_uri = URIRef(f"http://digipal.eu/ontology#Description_{desc['id']}")
    g.add((description_uri, RDF.type, CRM.E26_Physical_Feature)) 
    g.add((description_uri, RDFS.label, Literal(f"Description {desc['description']}")))
    if pd.notna(desc['description']):
        g.add((description_uri, EX.description, Literal(desc['description'])))
    if pd.notna(desc['comments']):
        g.add((description_uri, EX.comments, Literal(desc['comments'])))
    if pd.notna(desc['summary']):
        g.add((description_uri, EX.summary, Literal(desc['summary'])))
    if pd.notna(desc['text_id']): 
        text_uri = URIRef(f"http://digipal.eu/ontology#Text_{desc['text_id']}")
        g.add((description_uri,  CRM.P56_bears_feature, text_uri))  
    if pd.notna(desc['source_id']): 
        source_uri = URIRef(f"http://digipal.eu/ontology#Source_{desc['source_id']}")
        g.add((description_uri,  CRM.P70_is_documented_in, source_uri))
    if pd.notna(desc['historical_item_id']): 
        historical_item_uri = URIRef(f"http://digipal.eu/ontology#HistoricalItem_{desc['historical_item_id']}")
        g.add((description_uri,  CRM.P56_bears_feature, historical_item_uri))


for _, current in data['currentitem'].iterrows():
    current_uri = URIRef(f"http://digipal.eu/ontology#CurrentItem_{current['id']}")
    g.add((current_uri, RDF.type,      ARCH.Current_Item)) 
    if pd.notna(current['shelfmark']):
        g.add((current_uri, EX.shelfmark, Literal(current['shelfmark'])))
    if pd.notna(current['description']):
        g.add((current_uri, EX.shelfmark, Literal(current['description'])))
    if pd.notna(current['display_label']):
        g.add((current_uri, RDFS.label, Literal(current['display_label'])))
    if pd.notna(current['repository_id']):
        repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{current['repository_id']}")
        g.add((current_uri,  CRM.P50_has_current_keeper, repository_uri))
    
for _, repository in data['repository'].iterrows():
    repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{repository['id']}")
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
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{repository['place_id']}")
        g.add((repository_uri,  CRM.P74_has_current_or_former_residence, place_uri))
    if pd.notna(repository['media_permission_id']):
        media_permission_uri = URIRef(f"http://digipal.eu/ontology#MediaPermission_{repository['media_permission_id']}")
        g.add((repository_uri,  CRM.P104_is_subject_to, media_permission_uri))
    if pd.notna(repository['type_id']):
        type_uri = URIRef(f"http://digipal.eu/ontology#RepositoryType_{repository['type_id']}")
        g.add((repository_uri,  CRM.P2_has_type, type_uri))
    if pd.notna(repository['part_of_id']):
        part_of_uri = URIRef(f"http://digipal.eu/ontology#Repository_{repository['part_of_id']}")
        g.add((repository_uri,  CRM.P10_falls_within, part_of_uri))
    
for _, text in data['text'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{text['id']}")
    g.add((text_uri, RDF.type,      CRMtx.TX1_Written_Text))
    if pd.notna(text['name']):
        g.add((text_uri, RDFS.label, Literal(text['name'])))
    if pd.notna(text['date']):
        g.add((text_uri, EX.date, Literal(text['date'])))
    if pd.notna(text['url']):
        g.add((text_uri, EX.url, Literal(text['url'])))
    if pd.notna(text['date_sort']):
        g.add((text_uri, EX.date, Literal(text['date_sort'])))

for _, text_cat in data['text_categories'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{text_cat['text_id']}")
    cat_uri = URIRef(f"http://digipal.eu/ontology#Category_{text_cat['category_id']}")

for _, text_lang in data['text_languages'].iterrows():
    text_uri = URIRef(f"http://digipal.eu/ontology#Text_{text_lang['text_id']}")
    lang_uri = URIRef(f"http://digipal.eu/ontology#Language_{text_lang['language_id']}")

for _, text_item in data['textitempart'].iterrows():
    text_item_uri = URIRef(f"http://digipal.eu/ontology#Text_Item_part_{text_item['id']}")
    g.add((text_item_uri, RDF.type,      CRMtx.TX7_Written_Text_Segment))
    if pd.notna(text_item['name']):
        g.add((text_item_uri, RDFS.label, Literal(text_item['name'])))
    if pd.notna(text_item['date']):
        g.add((text_item_uri, EX.date, Literal(text_item['date'])))
    if pd.notna(text_item['locus']):
        g.add((text_item_uri, EX.locus, Literal(text_item['locus'])))
    if pd.notna(text_item['text_id']):
        text_uri = URIRef(f"http://digipal.eu/ontology#Text_{text_item['text_id']}")
        g.add((text_item_uri,  CRMtx.TXP4_has_segment, text_uri))
    # if pd.notna(text_item['item_part_id']):
    #     itempart_uri = URIRef(f"http://digipal.eu/ontology#Itempart_{text_item['item_part_id']}") 
    #     g.add((text_item_uri,  CRM.P_DEFINIR, itempart_uri)) # Lien non définit pour l'ontologie mais peut être rajouté si souhaité

for _, owner in data['owner'].iterrows():
    owner_uri = URIRef(f"http://digipal.eu/ontology#Owner_{owner['id']}")
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
        person_uri = URIRef(f"http://digipal.eu/ontology#Person_{owner['person_id']}") 
        g.add((owner_uri,  OWL.sameAs, person_uri))
    if pd.notna(owner['institution_id']):
        institution_uri = URIRef(f"http://digipal.eu/ontology#Institution_{owner['institution_id']}") 
        g.add((owner_uri,  OWL.sameAs, institution_uri))
    if pd.notna(owner['repository_id']):
        repository_uri = URIRef(f"http://digipal.eu/ontology#Repository_{owner['repository_id']}") 
        g.add((owner_uri,  CRM.P74_has_current_or_former_residence, repository_uri))
    
for _, hand in data['hand'].iterrows():
    hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{hand['id']}")
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
    if pd.notna(hand['num_glosses']):
        g.add((hand_uri, EX.num_glosses, Literal(hand['num_glosses'])))
    if pd.notna(hand['num_glossing_hands']):
        g.add((hand_uri, EX.num_glossing_hands, Literal(hand['num_glossing_hands'])))
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
    if pd.notna(hand['assigned_date_id']):
        date_uri = URIRef(f"http://digipal.eu/ontology#Date_Period_{hand['assigned_date_id']}") 
        g.add((hand_uri,  CRM.P8_took_place_on_or_within, date_uri))
    if pd.notna(hand['assigned_place_id']):
        place_uri = URIRef(f"http://digipal.eu/ontology#Place_{hand['assigned_place_id']}") 
        g.add((hand_uri,  CRM.P74_has_current_or_former_residence, place_uri))
    if pd.notna(hand['scribe_id']):
        scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{hand['scribe_id']}") 
        g.add((hand_uri,  CRM.P108_has_produced, scribe_uri))
    if pd.notna(hand['script_id']):
        writing_system_uri = URIRef(f"http://digipal.eu/ontology#Writing_System_{hand['id']}")
        g.add((writing_system_uri, RDF.type,      CRMtx.TX3_Writing_System))
        g.add((hand_uri,  CRMtx.TXP1_used_writing_system, writing_system_uri)) 
        script_uri = URIRef(f"http://digipal.eu/ontology#Script_{hand['script_id']}") 
        g.add((script_uri, RDF.type,      CRMtx.TX13_Script))
        g.add((writing_system_uri,  CRMtx.TXP16_employs_script, script_uri))
    if pd.notna(hand['item_part_id']):
        item_uri = URIRef(f"http://digipal.eu/ontology#Item_{hand['item_part_id']}")
        g.add((item_uri, RDF.type,      FRBRoo.F5_Item))
        g.add((hand_uri,  CRM.P46_is_composed_of, item_uri))
        itempart_uri = URIRef(f"http://digipal.eu/ontology#Itempart_{hand['item_part_id']}") 
        g.add((item_uri,  CRM.P65_shows_visual_item, itempart_uri))
    if pd.notna(hand['appearance_id']):
        appearance_uri = URIRef(f"http://digipal.eu/ontology#Appearance_{hand['appearance_id']}") 
        g.add((hand_uri,  CRM.P33_used_specific_technique, appearance_uri))
    if pd.notna(hand['glossed_text_id']):
        glossed_text_uri = URIRef(f"http://digipal.eu/ontology#Category_{hand['glossed_text_id']}") 
        g.add((hand_uri,  CRM.P2_has_type, glossed_text_uri))
    if pd.notna(hand['latin_style_id']):
        latin_style_uri = URIRef(f"http://digipal.eu/ontology#LatinStyle_{hand['latin_style_id']}") 
        g.add((hand_uri,  CRMtx.TXP12_has_style, latin_style_uri)) #Latin Style OU Appearance 

for _, image in data['image'].iterrows():
    image_uri = URIRef(f"http://digipal.eu/ontology#Image_{image['id']}")
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
        itempart_uri = URIRef(f"http://digipal.eu/ontology#Itempart_{image['item_part_id']}")
        g.add((image_uri,  CRM.P138_represents, itempart_uri))
    if pd.notna(image['media_permission_id']):
        media_permission_uri = URIRef(f"http://digipal.eu/ontology#MediaPermission_{image['media_permission_id']}")
        g.add((image_uri,  CRM.P104_is_subject_to, media_permission_uri))

for _, hand_image in data['hand_images'].iterrows():
    image_uri = URIRef(f"http://digipal.eu/ontology#Image_{hand_image['image_id']}")
    hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{hand_image['hand_id']}") 
    g.add((image_uri,  CRM.P138_represents, hand_uri))

for _, style in data['latinstyle'].iterrows():
    latin_style_uri = URIRef(f"http://digipal.eu/ontology#LatinStyle_{style['id']}")
    g.add((latin_style_uri, RDF.type,      CRMtx.TX10_Style))
    if pd.notna(style['style']):
        g.add((latin_style_uri, RDFS.label, Literal(style['style'])))

for _, appearance in data['appearance'].iterrows():
    appearance_uri = URIRef(f"http://digipal.eu/ontology#Appearance_{appearance['id']}")
    g.add((appearance_uri, RDF.type, ARCH.Script))
    g.add((appearance_uri, RDFS.label, Literal(f"Script {appearance['text']}")))
    if pd.notna(appearance['text']):
        g.add((appearance_uri, EX.text, Literal(appearance['text'])))
    if pd.notna(appearance['sort_order']):
        g.add((appearance_uri, EX.sort_order, Literal(appearance['sort_order'])))
    if pd.notna(appearance['description']):
        g.add((appearance_uri, EX.description, Literal(appearance['description'])))

for _, media_permission in data['mediapermission'].iterrows():
    media_permission_uri = URIRef(f"http://digipal.eu/ontology#MediaPermission_{media_permission['id']}")
    g.add((media_permission_uri, RDF.type, CRM.E30_Right))
    if pd.notna(media_permission['label']):
        g.add((media_permission_uri, RDFS.label, Literal(media_permission['label'])))
    if pd.notna(media_permission['display_message']):
        g.add((media_permission_uri, EX.display_message, Literal(media_permission['display_message'])))
    if pd.notna(media_permission['permission']):
        g.add((media_permission_uri, EX.permission, Literal(media_permission['permission'])))

for _, allograph in data['allograph'].iterrows():
    allograph_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{allograph['id']}")
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
        character_uri = URIRef(f"http://digipal.eu/ontology#Character_{allograph['character_id']}")
        g.add((allograph_uri,  CRM.P138_represents, character_uri))

BEFORE_TYPE = URIRef("http://digipal.eu/ontology#Befor_Allograph")
g.add((BEFORE_TYPE, RDF.type, CRM.E55_Type))
g.add((BEFORE_TYPE, RDFS.label, Literal("Before", lang="en")))

AFTER_TYPE = URIRef("http://digipal.eu/ontology#After_Allograph")
g.add((AFTER_TYPE, RDF.type, CRM.E55_Type))
g.add((AFTER_TYPE, RDFS.label, Literal("After", lang="en")))

for _, annotation in data['annotation'].iterrows():
    annotation_uri = URIRef(f"http://digipal.eu/ontology#Annotation_{annotation['id']}")
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
        image_uri = URIRef(f"http://digipal.eu/ontology#Image_{annotation['image_id']}")
        g.add((image_uri,  CRM.P138_represents, annotation_uri))
    if pd.notna(annotation['status_id']):
        status_uri = URIRef(f"http://digipal.eu/ontology#Status_{annotation['status_id']}")
        g.add((annotation_uri,  CRM.P2_has_type, status_uri)) #traiter status comme un E55_Type
    if pd.notna(annotation['before_id']):
        before_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{annotation['before_id']}")
        g.add((annotation_uri,  CRM.P148_has_component, before_uri))
        g.add((before_uri, CRM.P2_has_type, BEFORE_TYPE))
    if pd.notna(annotation['after_id']):
        after_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{annotation['after_id']}")
        g.add((annotation_uri,  CRM.P148_has_component, after_uri)) 
        g.add((after_uri, CRM.P2_has_type, AFTER_TYPE))

    #if pd.notna(annotation['graph_id']):
        #graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{annotation['graph_id']}")
        #g.add((annotation_uri,  CRM.P_A_DEFINIR, graph_uri)) #le lien entre graph et allograph est fait par idiograph dans le schéma sauf q
    #if pd.notna(annotation['author_id']): # est ce que c'est uile à garder 
        #author_uri = URIRef(f"http://digipal.eu/ontology#Author_{annotation['author_id']}")
        #g.add((annotation_uri,  CRM.P_A_DEFINIR, author_uri))

for _, graph in data['graph'].iterrows():
    graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{graph['id']}")
    g.add((graph_uri, RDF.type, ARCH.Graph))
    if pd.notna(graph['display_label']):
        g.add((graph_uri, RDFS.label, Literal(graph['display_label'])))

    if pd.notna(graph['idiograph_id']):
        idiograph_uri = URIRef(f"http://digipal.eu/ontology#Idiograph_{graph['idiograph_id']}")
        g.add((graph_uri,  CRM.P65_shows_visual_item, idiograph_uri))
    
    if pd.notna(graph['hand_id']):
        hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{graph['hand_id']}")
        g.add((hand_uri,  CRM.P106_is_composed_of, graph_uri))

for _, idiograph in data['idiograph'].iterrows():
    idiograph_uri = URIRef(f"http://digipal.eu/ontology#Idiograph_{idiograph['id']}")
    g.add((idiograph_uri, RDF.type, ARCH.Idiograph))
    if pd.notna(idiograph['display_label']):
        g.add((idiograph_uri, RDFS.label, Literal(idiograph['display_label'])))

    if pd.notna(idiograph['allograph_id']):
        allograph_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{idiograph['allograph_id']}")
        g.add((idiograph_uri,  CRM.P138_represents, allograph_uri))
    
    #if pd.notna(idiograph['scribe_id']): #je ne sais pas si c'est une bonne chose de le garder
        #scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{idiograph['scribe_id']}")
        #g.add((scribe_uri,  CRM.P_A_DEFINIR, idiograph_uri)) # Lien pas défini dans le schéma 

for _, feature in data['feature'].iterrows():
    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{feature['id']}")
    g.add((feature_uri, RDF.type, ARCH.Feature))
    if pd.notna(feature['name']):
        g.add((feature_uri, RDFS.label, Literal(feature['name'])))

for _, component in data['component'].iterrows():
    component_uri = URIRef(f"http://digipal.eu/ontology#Component_{component['id']}")
    g.add((component_uri, RDF.type, ARCH.Component))
    if pd.notna(component['name']):
        g.add((component_uri, RDFS.label, Literal(component['name'])))

for _, allo_compo in data['allographcomponent'].iterrows():
    allo_uri = URIRef(f"http://digipal.eu/ontology#Allograph_{allo_compo['allograph_id']}")
    compo_uri = URIRef(f"http://digipal.eu/ontology#Component_{allo_compo['component_id']}")
    g.add((allo_uri,  CRM.P65_shows_visual_item, compo_uri)) 

for _, graph_compo in data['graphcomponent'].iterrows():
    graph_uri = URIRef(f"http://digipal.eu/ontology#Graph_{graph_compo['graph_id']}")
    compo_uri = URIRef(f"http://digipal.eu/ontology#Component_{graph_compo['component_id']}")
    g.add((graph_uri,  CRM.P65_shows_visual_item, compo_uri)) 

for _, compo_feature in data['component_features'].iterrows():
    compo_uri = URIRef(f"http://digipal.eu/ontology#Component_{compo_feature['component_id']}")
    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{compo_feature['feature_id']}")
    g.add((compo_uri,  CRM.P56_bears_feature, feature_uri)) 

for _, graphcompo_feature in data['graphcomponent_features'].iterrows():
    graph_compo_uri = URIRef(f"http://digipal.eu/ontology#GraphCompo_{graphcompo_feature['graphcomponent_id']}")
    feature_uri = URIRef(f"http://digipal.eu/ontology#Feature_{graphcompo_feature['feature_id']}")
    g.add((graph_compo_uri,  CRM.P56_bears_feature, feature_uri)) 

for _, item_owner in data['itempart_owners'].iterrows():
    itempart_uri = URIRef(f"http://digipal.eu/ontology#Itempart_{item_owner['itempart_id']}")
    owner_uri = URIRef(f"http://digipal.eu/ontology#Owner_{item_owner['owner_id']}")
    g.add((itempart_uri,  CRM.P50_has_current_keeper, owner_uri)) 

for _, hand_desc in data['handdescription'].iterrows():
    hand_desc_uri = URIRef(f"http://digipal.eu/ontology#HandDescription_{hand_desc['id']}")
    g.add((hand_desc_uri, RDF.type, CRM.E62_String))
    if pd.notna(hand_desc['label']):
        g.add((hand_desc_uri, RDFS.label, Literal(hand_desc['label'])))
    if pd.notna(hand_desc['description']):
        g.add((hand_desc_uri, EX.description, Literal(hand_desc['description'])))
    if pd.notna(hand_desc['hand_id']):
        hand_uri = URIRef(f"http://digipal.eu/ontology#Hand_{hand_desc['hand_id']}")
        g.add((hand_uri,  CRM.P3_has_note, hand_desc_uri))
    if pd.notna(hand_desc['source_id']):
        source_uri = URIRef(f"http://digipal.eu/ontology#Source_{hand_desc['source_id']}")
        g.add((source_uri,  CRM.P70i_is_documented_in, hand_desc_uri))

for _, scribe_ref in data['scribe_reference'].iterrows():
    scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{scribe_ref['scribe_id']}")
    ref_uri = URIRef(f"http://digipal.eu/ontology#Reference_{scribe_ref['reference_id']}")
    g.add((scribe_uri,  CRM.P70i_is_documented_in, ref_uri)) 

for _, reference in data['reference'].iterrows():
    ref_uri = URIRef(f"http://digipal.eu/ontology#Reference_{reference ['id']}")
    g.add((ref_uri, RDF.type, CRM.E31_Document))
    if pd.notna(reference['name_index']):
        g.add((ref_uri, RDFS.label, Literal(reference['name_index'])))
    if pd.notna(reference['legacy_reference']):
        g.add((ref_uri, EX.legacy_reference, Literal(reference['legacy_reference'])))
    if pd.notna(reference['full_reference']):
        g.add((ref_uri, EX.full_reference, Literal(reference['full_reference'])))


for _, img_annot_status in data['imageannotationstatus'].iterrows():
    img_annot_status_uri = URIRef(f"http://digipal.eu/ontology#Status_{img_annot_status['id']}")
    g.add((img_annot_status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(img_annot_status['name']):
        g.add((img_annot_status_uri, RDFS.label, Literal(img_annot_status['name'])))
    
for _, ontograph_type in data['ontographtype'].iterrows():
    ontograph_type_uri = URIRef(f"http://digipal.eu/ontology#OntographType_{ontograph_type['id']}")
    g.add((ontograph_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(ontograph_type['name']):
        g.add((ontograph_type_uri, RDFS.label, Literal(ontograph_type['name'])))

for _, ontograph in data['ontograph'].iterrows():
    ontograph_uri = URIRef(f"http://digipal.eu/ontology#Ontograph_{ontograph['id']}")
    g.add((ontograph_uri, RDF.type, ARCH.Ontograph))
    if pd.notna(ontograph['name']):
        g.add((ontograph_uri, RDFS.label, Literal(ontograph['name'])))
    if pd.notna(ontograph['ontograph_type_id']):
        ontograph_type_uri = URIRef(f"http://digipal.eu/ontology#OntographType_{ontograph['ontograph_type_id']}")
        g.add((ontograph_uri,  CRM.P2_has_type, ontograph_type_uri )) 
    if pd.notna(ontograph['nesting_level']):
        g.add((ontograph_uri, EX.nesting_level, Literal(ontograph['nesting_level'])))
    if pd.notna(ontograph['sort_order']):
        g.add((ontograph_uri, EX.sort_order, Literal(ontograph['sort_order'])))

for _, scribe in data['scribe'].iterrows():
    scribe_uri = URIRef(f"http://digipal.eu/ontology#Scribe_{scribe['id']}")
    g.add((scribe_uri, RDF.type, ARCH.Scribe))
    if pd.notna(scribe['name']):
        g.add((scribe_uri, RDFS.label, Literal(scribe['name'])))
    if pd.notna(scribe['scriptorium_id']):
        institution_uri = URIRef(f"http://digipal.eu/ontology#Institution_{int(scribe['scriptorium_id'])}")
        g.add((scribe_uri, CRM.P107_is_current_or_former_member_of, institution_uri))

for _, character in data['character'].iterrows():
    character_uri = URIRef(f"http://digipal.eu/ontology#Character_{character['id']}")
    g.add((character_uri, RDF.type, ARCH.Character))
    if pd.notna(character['name']):
        g.add((character_uri, RDFS.label, Literal(character['name'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, EX.unicode_point, Literal(character['unicode_point'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, EX.unicode_point, Literal(character['unicode_point'])))
    if pd.notna((character['ontograph_id'])):
        ontograph_uri = URIRef(f"http://digipal.eu/ontology#Ontograph_{character['ontograph_id']}")
        g.add((character_uri,  CRM.P138_represents, ontograph_uri)) 
    if pd.notna((character['form_id'])):
        form_uri = URIRef(f"http://digipal.eu/ontology#FormCharacter_{character['form_id']}")
        g.add((character_uri,  CRM.P2_has_type, form_uri)) 

for _, character_compo in data['character_components'].iterrows():
    character_uri = URIRef(f"http://digipal.eu/ontology#Character_{character_compo['character_id']}")
    component_uri = URIRef(f"http://digipal.eu/ontology#Component_{character_compo['component_id']}")
    g.add((character_uri,  CRM.P65_shows_visual_item, component_uri)) 

for _, form in data['characterform'].iterrows():
    form_uri = URIRef(f"http://digipal.eu/ontology#FormCharacter_{form['id']}")
    g.add((form_uri, RDF.type, CRM.E55_Type))
    if pd.notna(form['name']):
        g.add((form_uri, RDFS.label, Literal(form['name'])))

for _, repository_type in data['ownertype'].iterrows():
    repository_type_uri = URIRef(f"http://digipal.eu/ontology#RepositoryType_{repository_type['id']}")
    g.add((repository_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(repository_type['name']):
        g.add((repository_type_uri, RDFS.label, Literal(repository_type['name'])))

for _, source in data['source'].iterrows():
    source_uri = URIRef(f"http://digipal.eu/ontology#Source_{source['id']}")
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
    status_uri = URIRef(f"http://digipal.eu/ontology#Status_{status['id']}")
    g.add((status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(status['name']):
        g.add((status_uri, RDFS.label, Literal(status['name'])))
# -------------------------------------------------------- SERIALISATION --------------------------------------------------------
g.serialize(destination="data_rdf_digipal_cidoc.rdf", format="xml")
print(f"✓ Fichier RDF généré — {len(g)} triplets")