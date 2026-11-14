#   TODO: Should unify the treatment of Latin and English in regard to arch:Script, arch:Style and arch:Appearance, and explicitly define relatinship between LatinStyle and Script, presumably via P69.
# TODO: Need to model, map and code the export for the text app.
# TODO: should really change everything to braket notation for consistency
# TODO: Modelling of Layout and Collation (and probably other 'minor' DigiPal tables) is not valid CIDOC-CRM and needs revision.
# Note: P198i for the patron saint is not valid CIDOC-CRM. Since the patron saint is not used anywhere in practice, it has
#    been removed from the export. It could be added back if needed but it's not clear how (perhaps P1 or P67; see report).
# TODO: Unify Descriptions across the database? CHECK if makes sense.
# TODO: Double-check DCTERMS.description vs E62 String for the description
# -------------------------------------------------------- LES IMPORTS -----------------------------------------------------------
import pandas as pd
import re
import argparse
from sqlalchemy import create_engine, inspect
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from datetime import datetime

DEFAULT_DB_NAME = "digipal"
DEFAULT_FORMAT = "turtle"
VALID_FORMATS = ["xml", "turtle"]

# -------------------------------------------------------- LES FONCTIONS ---------------------------------------------------------
def connection(dbname = DEFAULT_DB_NAME):
    try:
        mydb = create_engine("postgresql+psycopg://postgres:1234@localhost:5432/" + dbname)
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
        if re.match('digipal_', key):
            d[key.replace("digipal_", "")] = dico[key]
        elif re.match('django_content_type', key):
            d['django_content_type'] = dico[key]
    return d

def parse_args():
    parser = argparse.ArgumentParser(description="My script description")
    parser.add_argument(
        "-d", "--db-name",
        type=str,
        default=DEFAULT_DB_NAME,
        help="Name of the database to use"
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        default=DEFAULT_FORMAT,
        choices=VALID_FORMATS,
        help="File format for the output (XML, turtle, ...)"
    )
    return parser.parse_args()

# -------------------------------------------------------- CHARGEMENT -----------------------------------------------------------
args = parse_args()
DB_NAME = args.db_name
OUTPUT_FORMAT = args.format

digipal = connection(DB_NAME)
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
try:
    archive = data['archive'].merge(
        data['historicalitem'],
        left_on="historical_item_id", right_on="id",
        suffixes=("", "_historicalitem"), how="left"
    )
except Exception as e:
    print(f"**** Error merging archive with historicalitem: {e} ****")
    print("**** Check if the historicalitem table exists and has the expected columns. ****")
    archive = pd.DataFrame()

# -------------------------------------------------------- CREATION DU GRAPHE ---------------------------------------------------
g = Graph()

# --- Namespaces standards ---
CRM  = Namespace("http://www.cidoc-crm.org/cidoc-crm/")   # CIDOC-CRM
CRMtx  = Namespace("http://www.cidoc-crm.org/extensions/crmtex/")
LRMOO = Namespace("http://iflastandards.info/ns/lrm/lrmoo/")
ANNO=Namespace("http://www.w3.org/ns/oa#") #Annotation Web
ARCH = Namespace("https://w3id.org/archetype/ontology/") # For the Archetype ontology (model) TODO: NB STILL NEED TO REGISTER WITH W3ID.ORG! 
DATA   = Namespace("https://digipal.eu/data/")  # For the DigiPal data          
XSD_ = Namespace("http://www.w3.org/2001/XMLSchema#")
DCTERMS = Namespace("http://purl.org/dc/terms/")    # For annotation creators
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")   # For altLabel
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
ORG = Namespace("http://www.w3.org/ns/org#")

g.bind("crm",    CRM)
g.bind("lrmoo", LRMOO)
g.bind("crm-tx",    CRMtx)
g.bind("archetype", ARCH)
g.bind("web_annotation", ANNO)
g.bind("data",     DATA)
g.bind("owl",    OWL)
g.bind("xsd",    XSD_)
g.bind("dcterms", DCTERMS)
g.bind("skos",  SKOS)
g.bind("foaf", FOAF)

ontology = URIRef("http://digipal.eu/ontology")
g.add((ontology, RDF.type,   OWL.Ontology))
g.add((ontology, RDFS.label, Literal("Digipal Ontology", lang="en")))
g.add((ontology, OWL.imports, URIRef("https://w3id.org/archetype/ontology/0.1/")))

# Références documentaires (pas des ontologies, donc seeAlso et non imports)
g.add((ontology, RDFS.seeAlso, URIRef("https://www.w3.org/TR/annotation-vocab/")))
g.add((ontology, RDFS.seeAlso, URIRef("https://digipal.eu/")))

#--------------------------------------- Declaration des métadonnées -----------------------------------------------------
# TODO: distinguish properly between creators of the original data and creators of the export
# TODO: define Biblissima+ as its own entity to model the funding properly

RDFGRAPH_URI = URIRef("http://digipal.eu/graph")
PAS_URI = URIRef("https://orcid.org/0000-0002-9060-9340")
EG_URI = URIRef("https://github.com/Grim22E")
EPHE_URI = URIRef("https://ror.org/046b3cj80")
CESR_URI = URIRef("https://ror.org/03cv31q28")
AOROC_URI = URIRef("https://ror.org/05nsvn336")

g.add((RDFGRAPH_URI, RDF.type, DCTERMS['Dataset']))
g.add((RDFGRAPH_URI, DCTERMS['title'], Literal(f"Export of the {DB_NAME} dataset using the Archetype RDF export", lang="en")))
g.add((RDFGRAPH_URI, DCTERMS['creator'], PAS_URI))
g.add((RDFGRAPH_URI, DCTERMS['creator'], EG_URI))
g.add((RDFGRAPH_URI, DCTERMS['created'], Literal(datetime.now().strftime("%Y-%m-%d"))))
g.add((RDFGRAPH_URI, DCTERMS['license'], URIRef("https://creativecommons.org/licenses/by/4.0/")))
g.add((RDFGRAPH_URI, DCTERMS['description'], Literal(f"Export of the {DB_NAME} dataset using the Archetype RDF export. Mapping to RDF and export by Peter A. Stokes (EPHE/AOROC) and Eve Grimaud (CESR, Tours), in the context of Biblissima+ Cluster 4", lang="en")))
g.add((RDFGRAPH_URI, RDFS['comment'], Literal("Biblissima+ bénéficie d’une aide de l'Etat gérée par l'ANR au titre du Programme d’investissements d’avenir intégré à France 2030, portant la référence ANR-21-ESRE-0005.", lang="fr")))
g.add((RDFGRAPH_URI, DCTERMS['conformsTo'], ontology))

g.add((PAS_URI, RDF.type, FOAF['person']))
g.add((PAS_URI, FOAF['name'], Literal("Peter A. Stokes")))
g.add((PAS_URI, ORG['memberOf'], EPHE_URI))
g.add((PAS_URI, ORG['memberOf'], AOROC_URI))

g.add((EG_URI, RDF.type, FOAF['person']))
g.add((EG_URI, FOAF['name'], Literal("Eve Grimaud")))
g.add((EG_URI, ORG['memberOf'], CESR_URI))



# -------------------------------------------------------- HISTORICAL ITEM → frbr:F5 Item --------------------------------
TYPE_HISTITEM = DATA["TYPE_Historical_Item"]
g.add((TYPE_HISTITEM, RDF.type, CRM['E55_Type']))
g.add((TYPE_HISTITEM, RDFS.label, Literal("Type", lang="en")))

LOCUS_TYPE = DATA["Type_Locus"]
g.add((LOCUS_TYPE, RDF.type, CRM['E55_Type']))
g.add((LOCUS_TYPE, RDFS.label, Literal("Locus", lang="en")))

FORMAT_TYPE = DATA["Type_Format"]
g.add((FORMAT_TYPE, RDF.type, CRM['E55_Type']))
g.add((FORMAT_TYPE, RDFS.label, Literal("Format", lang="en")))

ACCEPTED_TYPE = DATA["Type_Accepted"]
g.add((ACCEPTED_TYPE, RDF.type, CRM['E55_Type']))
g.add((ACCEPTED_TYPE, RDFS.label, Literal("Accepted", lang="en")))

TYPE_DUBITABLE = DATA["Type_Dubitable"]
g.add((TYPE_DUBITABLE, RDF.type, CRM['E55_Type']))
g.add((TYPE_DUBITABLE, RDFS.label, Literal("Dubitable", lang="en")))

MEASUREMENT_UNIT = DATA["Measurement_Unit_millimeter"]
g.add((MEASUREMENT_UNIT, RDF.type, CRM['E58_Measurement_Unit']))
g.add((MEASUREMENT_UNIT, RDFS.label, Literal("Millimeter", lang="en")))

TYPE_PAGE_HEIGHT = DATA["Type_Page_Height"]
g.add((TYPE_PAGE_HEIGHT, RDF.type, CRM['E55_Type']))
g.add((TYPE_PAGE_HEIGHT, RDFS.label, Literal("Page Height", lang="en")))

TYPE_PAGE_WIDTH = DATA["Type_Page_Width"]
g.add((TYPE_PAGE_WIDTH, RDF.type, CRM['E55_Type']))
g.add((TYPE_PAGE_WIDTH, RDFS.label, Literal("Page Width", lang="en")))

TYPE_FRAME_HEIGHT = DATA["Type_Frame_Height"]
g.add((TYPE_FRAME_HEIGHT, RDF.type, CRM['E55_Type']))
g.add((TYPE_FRAME_HEIGHT, RDFS.label, Literal("Frame Height", lang="en")))

TYPE_FRAME_WIDTH = DATA["Type_Frame_Width"]
g.add((TYPE_FRAME_WIDTH, RDF.type, CRM['E55_Type']))
g.add((TYPE_FRAME_WIDTH, RDFS.label, Literal("Frame Width", lang="en")))

TYPE_TRAMLINE_WIDTH = DATA["Type_Tramline_Width"]
g.add((TYPE_TRAMLINE_WIDTH, RDF.type, CRM['E55_Type']))
g.add((TYPE_TRAMLINE_WIDTH, RDFS.label, Literal("Tramline Width", lang="en")))

# List of dimension fields for layout table — maps each Layout dimension field to its Type resource and URI fragment.
# (Used under layout loop below)
DIMENSION_FIELDS = [
    ('page_height', TYPE_PAGE_HEIGHT, 'Page_Height'),
    ('page_width', TYPE_PAGE_WIDTH, 'Page_Width'),
    ('frame_height', TYPE_FRAME_HEIGHT, 'Frame_Height'),
    ('frame_width', TYPE_FRAME_WIDTH, 'Frame_Width'),
    ('tramline_width', TYPE_TRAMLINE_WIDTH, 'Tramline_Width'),
]

# Helper function to build locus URIs
def get_locus_appellation_uri(item_part_id, locus_text):
    locus_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', str(locus_text))
    return DATA[f"Locus_Item_Part_{int(item_part_id)}_{locus_clean}"]

for _, row in data['historicalitem'].iterrows():

    hist_item = DATA[f"Historical_Item_{int(row['id'])}"]
    g.add((hist_item, RDF.type,      ARCH.Historical_Item))
    if pd.notna(row['name']):
        g.add((hist_item, RDFS.label, Literal(row['name'])))
    if pd.notna(row['catalogue_number']) and str(row['catalogue_number']).strip() != '':
        # Nettoyer la valeur pour l'URI : remplacer les caractères invalides par _
        catalogue_clean = re.sub(r'[^a-zA-Z0-9_-]', '_', str(row['catalogue_number']))
        catalogue_number_uri = DATA[f"CatalogueNumber_{catalogue_clean}"]

        g.add((catalogue_number_uri, RDF.type,   CRM['E42_Identifier']))
        g.add((catalogue_number_uri, RDF.value, Literal(str(row['catalogue_number']))))  # valeur originale conservée ici
        g.add((hist_item, CRM['P1_is_identified_by'], catalogue_number_uri))

    # --- Type de manuscrit → E55 Type (lien vers Historical_Item_Type) ---
    if pd.notna(row['historical_item_type_id']):
        type_uri = DATA[f"Historical_Item_Type_{int(row['historical_item_type_id'])}"]
        g.add((type_uri,   RDF.type,   CRM['E55_Type']))
        g.add((hist_item,  CRM['P2_has_type'], type_uri))             
        g.add((type_uri,  CRM['P2_has_type'], TYPE_HISTITEM))
        
    # --- Langue → E56 Language ---
    if pd.notna(row['language_id']):
        langue_uri = DATA[f"Language_{int(row['language_id'])}"]
        g.add((langue_uri, RDF.type,   CRM['E56_Language']))
        g.add((hist_item,  CRM['P72_has_language'], langue_uri))     

    if pd.notna(row['date']):
        g.add((hist_item, DCTERMS.date, Literal(str(row['date']))))

    if pd.notna(row['vernacular']):
        g.add((hist_item, ARCH.vernacular, Literal(bool(row['vernacular']))))
    if pd.notna(row['neumed']):
        g.add((hist_item, ARCH.neumed, Literal(bool(row['neumed']))))
    
    if pd.notna(row['historical_item_format_id']):
        format_uri = DATA[f"Historical_Item_Format_{int(row['historical_item_format_id'])}"]
        g.add((hist_item,  CRM['P2_has_type'], format_uri)) 

for _, hi_type in data['historicalitemtype'].iterrows():
    type_uri = DATA[f"Historical_Item_Type_{int(hi_type['id'])}"]
    if pd.notna(hi_type['name']):
        g.add((type_uri, RDFS.label, Literal(hi_type['name'])))

for _, format in data['format'].iterrows():
    hist_item_format = DATA[f"Historical_Item_Format_{int(format['id'])}"]
    g.add((hist_item_format, RDF.type, CRM['E55_Type']))
    g.add((hist_item_format, RDFS.label, Literal(str(format['name']))))
    g.add((hist_item_format, CRM['P2_has_type'], FORMAT_TYPE))               

for _, a in archive.iterrows():
    hist_uri = DATA[f"Historical_Item_{int(a['historical_item_id'])}"]
    attr_assignment = DATA[f"Archive_{int(a['id'])}"]
    g.add((attr_assignment, RDF.type, CRM['E13_Attribute_Assignment']))
    g.add((attr_assignment, CRM['P140_assigned_attribute_to'], hist_uri))
    if pd.notna(a['dubitable']) and bool(a['dubitable']):
        g.add((attr_assignment, CRM['P2_has_type'], TYPE_DUBITABLE))
    if pd.notna(a['object_id']) and str(a['content_type_id']) == '43':
        place_uri = DATA[f"Place_{int(a['object_id'])}"]
        g.add((attr_assignment, CRM['P141_assigned'], place_uri))
    elif pd.notna(a['object_id']) and str(a['content_type_id']) != '43':
        print("Le type de object_id dans historicalitem n'est pas pris en compte à modifier")

# --- DEFINITION DES TYPES DE PLACE ---
REGION_TYPE = DATA["Type_Region"]
g.add((REGION_TYPE, RDF.type, CRM['E55_Type']))
g.add((REGION_TYPE, RDFS.label, Literal("Région", lang="en")))

CURRENT_COUNTY_TYPE = DATA["Type_Current_County"]
g.add((CURRENT_COUNTY_TYPE, RDF.type, CRM['E55_Type']))
g.add((CURRENT_COUNTY_TYPE, RDFS.label, Literal("Current County", lang="en")))

HISTORICAL_COUNTY_TYPE = DATA["Type_Historical_County"]
g.add((HISTORICAL_COUNTY_TYPE, RDF.type, CRM['E55_Type']))
g.add((HISTORICAL_COUNTY_TYPE, RDFS.label, Literal("Historical County", lang="en")))

FONDATION_TYPE = DATA["Type_Fondation"]
g.add((FONDATION_TYPE, RDF.type, CRM['E55_Type']))
g.add((FONDATION_TYPE, RDFS.label, Literal("Fondation", lang="en")))

REFONDATION_TYPE = DATA["Type_Refondation"]
g.add((REFONDATION_TYPE, RDF.type, CRM['E55_Type']))
g.add((REFONDATION_TYPE, RDFS.label, Literal("Refondation", lang="en")))

for _, p in data['place'].iterrows():
    place_uri = DATA[f"Place_{int(p['id'])}"]
    g.add((place_uri, RDF.type,      CRM['E53_Place']))  
    g.add((place_uri, RDFS.label, Literal(str(p['name']))))
    if pd.notna(p['eastings']):
        g.add((place_uri, ARCH.eastings, Literal(int(p['eastings']))))
    if pd.notna(p['northings']):
        g.add((place_uri, ARCH.northings, Literal(int(p['northings']))))
    if pd.notna(p['region_id']): 
        region_uri = DATA[f"Region_{int(p['region_id'])}"]
        g.add((region_uri, CRM['P2_has_type'], REGION_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], region_uri))

    if pd.notna(p['current_county_id']):
        current_county_uri = DATA[f"County_{int(p['current_county_id'])}"] # PAS: removed CurrentCounty to unify with HistoricalCounty, since both point to the same County table
        g.add((current_county_uri, CRM['P2_has_type'], CURRENT_COUNTY_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], current_county_uri))
    
    if pd.notna(p['historical_county_id']):
        historical_county_uri = DATA[f"County_{int(p['historical_county_id'])}"]
        g.add((historical_county_uri, CRM['P2_has_type'], HISTORICAL_COUNTY_TYPE))
        g.add((place_uri, CRM['P89_falls_within'], historical_county_uri))

for _, county in data['county'].iterrows():
    county_uri = DATA[f"County_{int(county['id'])}"]
    g.add((county_uri, RDF.type,      CRM['E53_Place']))  
    g.add((county_uri, RDFS.label, Literal(str(county['name']))))

for _, region in data['region'].iterrows():
    region_uri = DATA[f"Region_{int(region['id'])}"]
    g.add((region_uri, RDF.type,      CRM['E53_Place']))  
    g.add((region_uri, RDFS.label, Literal(str(region['name']))))

for _, i in data['institution'].iterrows():
    insti = DATA[f"Institution_{int(i['id'])}"]
    g.add((insti, RDF.type, CRM['E74_Group']))
    g.add((insti, RDFS.label, Literal(str(i['name']))))

    if pd.notna(i['foundation']):
        insti_foundation = DATA[f"InstiFoundation_{int(i['id'])}"]
        g.add((insti_foundation, RDF.type, CRM['E66_Formation']))
        g.add((insti_foundation, CRM['P95_has_formed'], insti))
        g.add((insti_foundation, DCTERMS.date, Literal(str(i['foundation']))))
        if pd.notna(i['founder_id']):
            founder_insti = DATA[f"Person_{int(i['founder_id'])}"]
            g.add((insti_foundation, CRM['P14_carried_out_by_founder'], founder_insti))
        g.add((insti_foundation, CRM['P2_has_type'], FONDATION_TYPE))

    if pd.notna(i['refoundation']):
        insti_refoundation = DATA[f"InstiRefoundation_{int(i['id'])}"]
        g.add((insti_refoundation, RDF.type, CRM['E66_Formation']))
        g.add((insti_refoundation, CRM['P95_has_formed'], insti))
        g.add((insti_refoundation, DCTERMS.date, Literal(str(i['refoundation']))))
        if pd.notna(i['founder_id']):
            founder_insti = DATA[f"Person_{int(i['founder_id'])}"]
            g.add((insti_refoundation, CRM['P14_carried_out_by_founder'], founder_insti))
        if pd.notna(i['reformer_id']):
            reformer_insti = DATA[f"Person_{int(i['reformer_id'])}"]
            g.add((insti_refoundation, CRM['P14_carried_out_by_reformer'], reformer_insti))
        g.add((insti_refoundation, CRM['P2_has_type'], REFONDATION_TYPE))

    if pd.notna(i['institution_type_id']):
        type_insti_uri = DATA[f"InstitutionType_{int(i['institution_type_id'])}"]
        g.add((insti, CRM['P2_has_type'], type_insti_uri))

    if pd.notna(i['place_id']):
        place_insti_uri = DATA[f"Place_{int(i['place_id'])}"]
        g.add((place_insti_uri, RDF.type, CRM['E53_Place']))
        g.add((insti, CRM['P74_has_current_or_former_residence'], place_insti_uri))

for _, inst_type in data['institutiontype'].iterrows():
    insti_type= DATA[f"InstitutionType_{int(inst_type['id'])}"]
    g.add((insti_type, RDF.type, CRM['E55_Type']))
    g.add((insti_type, RDFS.label, Literal(str(inst_type['name']))))

for _, pers in data['person'].iterrows():
    insti = DATA[f"Person_{int(pers['id'])}"]
    g.add((insti, RDF.type, CRM['E21_Person']))
    g.add((insti, RDFS.label, Literal(str(pers['name']))))

for _, item in data['itempart'].iterrows():
    itempart= DATA[f"Item_Part_{int(item['id'])}"]
    g.add((itempart, RDF.type,      ARCH.Item_Part))
    if pd.notna(item['display_label']):
        g.add((itempart, RDFS.label, Literal(item['display_label'])))
    if pd.notna(item['pagination']):
        g.add((itempart, ARCH.pagination, Literal(item['pagination'])))
    if pd.notna(item['notes']):
        g.add((itempart, CRM.P3_has_note, Literal(item['notes'])))
    if pd.notna(item['current_item_id']):
        F5_Item_uri = DATA[f"Item_{int(item['id'])}"]
        current_item_uri = DATA[f"Current_Item_{int(item['current_item_id'])}"]
        g.add((current_item_uri,  CRM['P46_is_composed_of'], itempart))
        g.add((current_item_uri,  OWL['sameAs'], F5_Item_uri))

for _, part in data['itempartitem'].iterrows():
    hist= DATA[f"Historical_Item_{int(part['historical_item_id'])}"]
    item= DATA[f"Item_Part_{int(part['item_part_id'])}"]
    g.add((hist,  CRM['P46_is_composed_of'], item))

for _, origin in data['itemorigin'].iterrows():
    hist_uri = DATA[f"Historical_Item_{int(origin['historical_item_id'])}"]
    attr_assignment = DATA[f"ItemOrigin_{int(origin['id'])}"]
    g.add((attr_assignment, RDF.type, CRM['E13_Attribute_Assignment']))
    g.add((attr_assignment, CRM['P140_assigned_attribute_to'], hist_uri))
    if pd.notna(origin['dubitable']) and bool(origin['dubitable']):
        g.add((attr_assignment, CRM['P2_has_type'], TYPE_DUBITABLE))
    if pd.notna(origin['place_id']):
        place_uri = DATA[f"Place_{int(origin['place_id'])}"]
        g.add((attr_assignment, CRM['P141_assigned'], place_uri))
    if pd.notna(origin['institution_id']):
        institution_uri = DATA[f"Institution_{int(origin['institution_id'])}"]
        g.add((attr_assignment, CRM['P141_assigned'], institution_uri))

for _, layout in data['layout'].iterrows():
    # Very many rows (close to 80%) in digipal_layout have no real content: all the measurement fields are null or
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
        (layout['bilinear_ruling'] == True) or
        (layout['insular_pricking'] == True)
    )
    if not has_content:
        continue

    # NB layout and dimension URIs assume linking to Historical Item since that is how DigiPal's data is structured.
    #  If other Archetype-based projects use Layout elsewhere, e.g. linked to Item Part, the URI naming should be changed accordingly.
    # - Changed model to implement full CIDOC-CRM Measurement structure
    # - Fixed issue of converting float to int for dimensions, since should be integers for these properties.
    # NB also, if no historical_item_id in Layout record then can't link to anything, so we drop it completely.
    # This is a data loss, but the data isn't meaningful without an HI anyway
    if pd.notna(layout['historical_item_id']):
        layout_uri = DATA[f"Layout_Historical_Item_{int(layout['historical_item_id'])}"] 
        g.add((layout_uri, RDF.type, CRM['E18_Physical_Thing']))
        g.add((layout_uri, RDFS.label, Literal(f"Layout {layout['id']}")))

        dimension_uris = []
        for field_name, type_uri, uri_fragment in DIMENSION_FIELDS:
            if pd.notna(layout[field_name]):
                dim_uri = DATA[f"Dimension_Historical_Item_{int(layout['historical_item_id'])}_{uri_fragment}"]
                g.add((dim_uri, RDF.type, CRM['E54_Dimension']))
                g.add((dim_uri, RDFS.label, Literal(f"{uri_fragment.replace('_', ' ')} {layout['id']}")))
                g.add((dim_uri, CRM['P2_has_type'], type_uri))
                g.add((dim_uri, CRM['P90_has_value'], Literal(int(layout[field_name]))))
                g.add((dim_uri, CRM['P91_has_unit'], MEASUREMENT_UNIT))
                dimension_uris.append(dim_uri)

        if pd.notna(layout['lines']):
            g.add((layout_uri, ARCH['lines'], Literal(int(layout['lines']))))
        if pd.notna(layout['columns']):
            g.add((layout_uri, ARCH['columns'], Literal(int(layout['columns']))))

        if pd.notna(layout['bilinear_ruling']):
            g.add((layout_uri, ARCH.bilinear_ruling, Literal(layout['bilinear_ruling'])))
        if pd.notna(layout['comments']):
            g.add((layout_uri, CRM.P3_has_note, Literal(layout['comments'])))
        if pd.notna(layout['insular_pricking']):
            g.add((layout_uri, ARCH['insular_pricking'], Literal(layout['insular_pricking'])))

        if pd.notna(layout['hair_arrangement_id']):
            hair =  DATA[f"Hair_{int(layout['hair_arrangement_id'])}"]
            g.add((layout_uri,  CRM['P45_consists_of'], hair))

        # PAS: This loop is redundant in practice as Layout is only linked to Historical Items in DigiPal,
        # but it could well be used for Item Parts in other implementations, so keep it in case.
        # NB that if this is implemented then the naming of the layout and dimension URIs should be changed accordingly (see above)
        # NB also that changed to implement full CIDOC-CRM Measurement model
        if pd.notna(layout['item_part_id']):
            itempart_layout = DATA[f"Item_Part_{int(layout['item_part_id'])}"]
            g.add((itempart_layout, CRM['P46_is_composed_of'], layout_uri))
            for dim_uri in dimension_uris:
                g.add((itempart_layout, CRM['P43_has_dimension'], dim_uri))

        # PAS: added — historical_item_id is the field actually populated in DigiPal's data;
        # item_part_id above is kept as a fallback for other Archetype-based projects that may use it.
        # Also: changed to implement full CIDOC-CRM Measurement model
        if pd.notna(layout['historical_item_id']):
            hist_uri = DATA[f"Historical_Item_{int(layout['historical_item_id'])}"]
            g.add((hist_uri, CRM['P46_is_composed_of'], layout_uri))
            for dim_uri in dimension_uris:
                g.add((hist_uri, CRM['P43_has_dimension'], dim_uri))

for _, hair in data['hair'].iterrows():
    hair_uri =  DATA[f"Hair_{int(hair['id'])}"]
    g.add((hair_uri, RDF.type,      CRM['E57_Material']))    
    if pd.notna(hair['label']):
        g.add((hair_uri, RDFS.label, Literal(hair['label'])))

CAT_HISTITEM = DATA["Category_Historical_Item"]
g.add((CAT_HISTITEM , RDF.type, CRM['E55_Type']))
g.add((CAT_HISTITEM , RDFS.label, Literal("Category", lang="en")))

for _, category in data['category'].iterrows(): 
    category_uri = DATA[f"Category_{int(category['id'])}"]
    g.add((category_uri,  CRM['P2_has_type'], CAT_HISTITEM))
    g.add((category_uri, RDF.type,      CRM['E55_Type']))
    if pd.notna(category['name']):
        g.add((category_uri, RDFS.label, Literal(category['name'])))
    if pd.notna(category['sort_order']):
        g.add((category_uri, ARCH.sort_order, Literal(int(category['sort_order']))))

for _, hist_cat in data['historicalitem_categories'].iterrows():
    cat_uri = DATA[f"Category_{int(hist_cat['category_id'])}"]
    hist_uri = DATA[f"Historical_Item_{int(hist_cat['historicalitem_id'])}"]
    g.add((hist_uri,  CRM['P2_has_type'], cat_uri))

for _, language in data['language'].iterrows():
    language_uri = DATA[f"Language_{int(language['id'])}"]
    g.add((language_uri, RDF.type,      CRM['E56_Language']))          # classe locale pour filtrer facilement
    if pd.notna(language['name']):
        g.add((language_uri, RDFS.label, Literal(language['name'])))

COLLATION_type = DATA["Collation"]
g.add((COLLATION_type, RDF.type, CRM['E55_Type']))
g.add((COLLATION_type,  RDFS.label, Literal("Collation", lang="en")))

DECORATION_type = DATA["Decoration"]
g.add((DECORATION_type, RDF.type, CRM['E55_Type']))
g.add((DECORATION_type,  RDFS.label, Literal("Decoration", lang="en")))

for _, collation in data['collation'].iterrows():
    # Filter for collation rows that have no content (all fields null or empty) to avoid creating meaningless nodes in the graph.
    has_content = (
        (collation['fragment'] == True) or
        (pd.notna(collation['leaves']) and collation['leaves'] != 0)
    )
    if not has_content:
        continue

    collation_uri = DATA[f"Collation_{int(collation['id'])}"]
    g.add((collation_uri, RDF.type,      CRM['E18_Physical_Thing']))
    g.add((collation_uri,  CRM['P2_has_type'], COLLATION_type))
    g.add((collation_uri, RDFS.label, Literal(f"Collation {collation['id']}")))
    if pd.notna(collation['fragment']):
        g.add((collation_uri, ARCH.fragment, Literal(collation['fragment'])))
    if pd.notna(collation['leaves']):
        g.add((collation_uri, ARCH.leaves, Literal(int(collation['leaves']))))
    if pd.notna(collation['front_flyleaves']):
        g.add((collation_uri, ARCH.front_flyleaves, Literal(int(collation['front_flyleaves']))))
    if pd.notna(collation['back_flyleaves']):
        g.add((collation_uri, ARCH.back_flyleaves, Literal(int(collation['back_flyleaves']))))
    if pd.notna(collation['historical_item_id']):
        hist_uri = DATA[f"Historical_Item_{int(collation['historical_item_id'])}"]
        g.add((hist_uri,  CRM['P46_is_composed_of'], collation_uri))

for _, deco in data['decoration'].iterrows():
    deco_uri = DATA[f"Decoration_{int(deco['id'])}"]
    g.add((deco_uri, RDF.type,      CRM['E18_Physical_Thing']))
    g.add((deco_uri,  CRM['P2_has_type'], DECORATION_type))
    g.add((deco_uri, RDFS.label, Literal(f"Decoration {deco['id']}")))
    if pd.notna(deco['illustrated']):
        g.add((deco_uri, ARCH.illustrated, Literal(deco['illustrated'])))

    if pd.notna(deco['decorated']):
        g.add((deco_uri, ARCH.decorated, Literal(deco['decorated'])))

    if pd.notna(deco['illuminated']):
        g.add((deco_uri, ARCH.illuminated, Literal(deco['illuminated'])))

    if pd.notna(deco['num_colours']):
        g.add((deco_uri, ARCH.num_colours, Literal(int(deco['num_colours']))))
    if pd.notna(deco['num_inks']):
        g.add((deco_uri, ARCH.num_inks, Literal(int(deco['num_inks']))))

    if pd.notna(deco['colours']):
        g.add((deco_uri, ARCH.colours, Literal(deco['colours'])))
    
    if pd.notna(deco['inks']):
        g.add((deco_uri, ARCH.inks, Literal(deco['inks'])))
    
    if pd.notna(deco['style']):
        g.add((deco_uri, ARCH.style, Literal(deco['style'])))
    
    if pd.notna(deco['description']):
        g.add((deco_uri, DCTERMS.description, Literal(deco['description'])))

    if pd.notna(deco['catalogue_references']):
        g.add((deco_uri, ARCH.catalogue_references, Literal(deco['catalogue_references'])))

    if pd.notna(deco['historical_item_id']):
        hist_uri = DATA[f"Historical_Item_{int(deco['historical_item_id'])}"]
        g.add((hist_uri,  CRM['P46_is_composed_of'], deco_uri))


for _, date in data['date'].iterrows():
    date_period_uri = DATA[f"Date_Period_{int(date['id'])}"]
    g.add((date_period_uri, RDF.type,      CRM.E4_Period))
    g.add((date_period_uri, RDFS.label, Literal(f"Date {date['id']}")))
    g.add((date_period_uri, DCTERMS.date, Literal(date['date'])))
    g.add((date_period_uri, ARCH.weight, Literal(date['weight'])))
    if pd.notna(date['post_conquest']):
        g.add((date_period_uri, ARCH.post_conquest, Literal(bool(date['post_conquest']))))
    if pd.notna(date['s_xi']):
        g.add((date_period_uri, ARCH.s_xi, Literal(bool(date['s_xi']))))

    if pd.notna(date['sort_order']):
        g.add((date_period_uri, ARCH.sort_order, Literal(int(date['sort_order']))))
    if pd.notna(date['band']):
        g.add((date_period_uri, ARCH.band, Literal(int(date['band']))))
    if pd.notna(date['additional_band']):
        g.add((date_period_uri, ARCH.additional_band, Literal(int(date['additional_band']))))

    
    date_timespan_uri = DATA[f"Date_Time_Span_{int(date['id'])}"]
    g.add((date_period_uri,  CRM['P4_has_time-span'], date_timespan_uri))
    g.add((date_timespan_uri, RDF.type,      CRM['E52_Time-Span']))
    g.add((date_timespan_uri, RDFS.label, Literal(f"Time-span {date['id']}")))
    if pd.notna(date['min_weight']):
        g.add((date_timespan_uri, ARCH.min_weight, Literal(date['min_weight'])))
    if pd.notna(date['max_weight']):
        g.add((date_timespan_uri, ARCH.max_weight, Literal(date['max_weight'])))

    if pd.notna(date['evidence']):
        date_document_uri = DATA[f"Date_Document_{int(date['id'])}"]
        g.add((date_period_uri,  CRM.P70i_is_documented_in, date_document_uri))
        g.add((date_document_uri, RDF.type,      CRM.E31_Document)) 
        g.add((date_document_uri, ARCH.has_evidence_note, Literal(date['evidence'])))

for _, desc in data['description'].iterrows():
    description_uri = DATA[f"Description_{int(desc['id'])}"]
    g.add((description_uri, RDF.type, CRM['E31_Document']))
    if pd.notna(desc['description']):
        g.add((description_uri, DCTERMS.description, Literal(desc['description'])))
    if pd.notna(desc['comments']):
        g.add((description_uri, CRM.P3_has_note, Literal(desc['comments'])))
    if pd.notna(desc['summary']): # Never used in practice...
        g.add((description_uri, ARCH.summary, Literal(desc['summary'])))
    if pd.notna(desc['source_id']): 
        source_uri = DATA[f"Source_{int(desc['source_id'])}"]
        g.add((description_uri,  CRM['P70i_is_documented_in'], source_uri))
    if pd.notna(desc['text_id']): 
        text_uri = DATA[f"Text_{int(desc['text_id'])}"]
        g.add((description_uri,  CRM['P70_documents'], text_uri))
    if pd.notna(desc['historical_item_id']): 
        historical_item_uri = DATA[f"Historical_Item_{int(desc['historical_item_id'])}"]
        g.add((description_uri,  CRM['P70_documents'], historical_item_uri))


for _, current in data['currentitem'].iterrows():
    current_uri = DATA[f"Current_Item_{int(current['id'])}"]
    g.add((current_uri, RDF.type,      ARCH.Current_Item)) 
    if pd.notna(current['shelfmark']):
        shelfmark_uri = DATA[f"Shelfmark_Current_Item_{int(current['id'])}"]
        g.add((shelfmark_uri, RDF.type, CRM['E42_Identifier']))
        g.add((shelfmark_uri, RDF.value, Literal(current['shelfmark'])))
        g.add((current_uri, CRM['P1_is_identified_by'], shelfmark_uri))
    if pd.notna(current['description']):
        g.add((current_uri, DCTERMS.description, Literal(current['description'])))
    if pd.notna(current['display_label']):
        g.add((current_uri, RDFS.label, Literal(current['display_label'])))
    if pd.notna(current['repository_id']):
        repository_uri = DATA[f"Repository_{int(current['repository_id'])}"]
        g.add((current_uri,  CRM.P50_has_current_keeper, repository_uri))
    
for _, repository in data['repository'].iterrows():
    repository_uri = DATA[f"Repository_{int(repository['id'])}"]
    g.add((repository_uri, RDF.type,      CRM.E74_Group)) #Peut-être mettre en document 
    if pd.notna(repository['name']):
        g.add((repository_uri, RDFS.label, Literal(repository['name'])))
    if pd.notna(repository['short_name']):
        g.add((repository_uri, SKOS.altLabel, Literal(repository['short_name'])))
    if pd.notna(repository['comma']):
        g.add((repository_uri, ARCH.comma, Literal(repository['comma'])))
    if pd.notna(repository['british_isles']):
        g.add((repository_uri, ARCH.british_isles, Literal(repository['british_isles'])))
    if pd.notna(repository['copyright_notice']):
        g.add((repository_uri, DCTERMS.rights, Literal(repository['copyright_notice'])))
    if pd.notna(repository['place_id']):
        place_uri = DATA[f"Place_{int(repository['place_id'])}"]
        g.add((repository_uri,  CRM.P74_has_current_or_former_residence, place_uri))
    if pd.notna(repository['type_id']):
        type_uri = DATA[f"RepositoryType_{int(repository['type_id'])}"]
        g.add((repository_uri,  CRM.P2_has_type, type_uri))
    # P10 is clearly the wrong relationship (should only apply to Time-Spans), but it's unclear what the right one should be.
    # DigiPal only has obe occurrence which is an error, and no other projects use it AFAIK, so omit for now.
    # TODO: Add a proper solution for potential future projects
#    if pd.notna(repository['part_of_id']):
#        part_of_uri = DATA[f"Repository_{int(repository['part_of_id'])}"]
#        g.add((repository_uri,  CRM.P10_falls_within, part_of_uri))
    
for _, text in data['text'].iterrows():
    text_uri = DATA[f"Text_{int(text['id'])}"]
    g.add((text_uri, RDF.type,      CRMtx.TX1_Written_Text))  # TODO: No, TX1 is a Physical Feature, not a Linguistic Object, so this is wrong. arch:Text should be E33_Linguistic_Object (or FRBRoo Expression)
    if pd.notna(text['name']):
        g.add((text_uri, RDFS.label, Literal(text['name'])))
    if pd.notna(text['date']):
        g.add((text_uri, DCTERMS.date, Literal(text['date'])))

    if pd.notna(text['date_sort']):
        g.add((text_uri, ARCH.date_sort, Literal(text['date_sort'])))

for _, text_cat in data['text_categories'].iterrows():
    text_uri = DATA[f"Text_{int(text_cat['text_id'])}"]
    cat_uri = DATA[f"Category_{int(text_cat['category_id'])}"]
    g.add((text_uri, CRM['P2_has_type'], cat_uri))

for _, text_lang in data['text_languages'].iterrows():
    text_uri = DATA[f"Text_{int(text_lang['text_id'])}"]
    lang_uri = DATA[f"Language_{int(text_lang['language_id'])}"]
    # TODO: NB that P72 is not strictly correct as Text here is TX1 so a Physical Feature, not a E33 Linguistic Object
    g.add((text_uri, CRM['P72_has_language'], lang_uri))

for _, text_item in data['textitempart'].iterrows():
    text_item_uri = DATA[f"Text_Item_part_{int(text_item['id'])}"]
    g.add((text_item_uri, RDF.type,      CRMtx.TX7_Written_Text_Segment))
    if pd.notna(text_item['name']):
        g.add((text_item_uri, RDFS.label, Literal(text_item['name'])))
    if pd.notna(text_item['date']):
        g.add((text_item_uri, DCTERMS.date, Literal(text_item['date'])))
    if pd.notna(text_item['locus']) and str(text_item['locus']).strip() != '' and pd.notna(text_item['item_part_id']):
        locus_uri = get_locus_appellation_uri(text_item['item_part_id'], text_item['locus'])
        g.add((locus_uri, RDF.type, CRM['E41_Appellation']))
        g.add((locus_uri, RDFS.label, Literal(text_item['locus'])))
        g.add((locus_uri, CRM['P2_has_type'], LOCUS_TYPE))
        g.add((text_item_uri, CRM['P1_is_identified_by'], locus_uri))
        itempart_uri = DATA[f"Item_Part_{int(text_item['item_part_id'])}"]
        g.add((itempart_uri, CRM['P1_is_identified_by'], locus_uri))
    if pd.notna(text_item['text_id']):
        text_uri = DATA[f"Text_{int(text_item['text_id'])}"]
        g.add((text_uri,  CRMtx.TXP4_has_segment, text_item_uri))

for _, owner in data['owner'].iterrows():
    owner_uri = DATA[f"Owner_{int(owner['id'])}"]
    g.add((owner_uri, RDF.type,      CRM['E13_Attribute_Assignment']))
    if pd.notna(owner['date']):
        g.add((owner_uri, DCTERMS.date, Literal(owner['date'])))
    if pd.notna(owner['evidence']):
        g.add((owner_uri, ARCH.has_evidence_note, Literal(owner['evidence'])))
    if pd.notna(owner['rebound']):
        g.add((owner_uri, ARCH.rebound, Literal(owner['rebound'])))
    if pd.notna(owner['annotated']):
        g.add((owner_uri, ARCH.annotated, Literal(owner['annotated'])))
    if pd.notna(owner['dubitable']) and bool(owner['dubitable']):
        g.add((owner_uri, CRM['P2_has_type'], TYPE_DUBITABLE))
    if pd.notna(owner['display_label']):
        g.add((owner_uri, RDFS.label, Literal(owner['display_label'])))
    if pd.notna(owner['person_id']):
        person_uri = DATA[f"Person_{int(owner['person_id'])}"] 
        g.add((owner_uri,  CRM['P141_assigned'], person_uri))
    if pd.notna(owner['institution_id']):
        institution_uri = DATA[f"Institution_{int(owner['institution_id'])}"] 
        g.add((owner_uri,  CRM['P141_assigned'], institution_uri))
    if pd.notna(owner['repository_id']):
        repository_uri = DATA[f"Repository_{int(owner['repository_id'])}"] 
        g.add((owner_uri,  CRM['P141_assigned'], repository_uri))
    
for _, hand in data['hand'].iterrows():
    handinstance_uri = DATA[f"HandInstance_{int(hand['id'])}"]
    g.add((handinstance_uri, RDF.type, ARCH.HandInstance))
    if pd.notna(hand['num']):
        g.add((handinstance_uri, ARCH.num, Literal(hand['num'])))
    if pd.notna(hand['scragg']):
        g.add((handinstance_uri, ARCH.scragg, Literal(hand['scragg'])))
    if pd.notna(hand['em_title']):
        g.add((handinstance_uri, ARCH.em_title, Literal(hand['em_title'])))
    if pd.notna(hand['label']):
        g.add((handinstance_uri, RDFS.label, Literal(hand['label'])))
    if pd.notna(hand['display_note']) and str(hand['display_note']).strip() != '':
        g.add((handinstance_uri, ARCH.display_note, Literal(hand['display_note'])))
    if pd.notna(hand['relevant']):
        g.add((handinstance_uri, ARCH.relevant, Literal(hand['relevant'])))
    if pd.notna(hand['latin_only']):
        g.add((handinstance_uri, ARCH.latin_only, Literal(hand['latin_only'])))
    if pd.notna(hand['gloss_only']):
        g.add((handinstance_uri, ARCH.gloss_only, Literal(hand['gloss_only'])))
    if pd.notna(hand['membra_disjecta']):
        g.add((handinstance_uri, ARCH.membra_disjecta, Literal(hand['membra_disjecta'])))
    if pd.notna(hand['num_glosses']):
        g.add((handinstance_uri, ARCH.num_glosses, Literal(int(hand['num_glosses']))))
    if pd.notna(hand['num_glossing_hands']):
        g.add((handinstance_uri, ARCH.num_glossing_hands, Literal(int(hand['num_glossing_hands']))))
    if pd.notna(hand['scribble_only']):
        g.add((handinstance_uri, ARCH.scribble_only, Literal(hand['scribble_only'])))
    if pd.notna(hand['imitative']):
        g.add((handinstance_uri, ARCH.imitative, Literal(hand['imitative'])))
    if pd.notna(hand['comments']):
        g.add((handinstance_uri, CRM.P3_has_note, Literal(hand['comments'])))
    if pd.notna(hand['display_label']):
        g.add((handinstance_uri, ARCH.display_label, Literal(hand['display_label'])))
    if pd.notna(hand['locus']) and str(hand['locus']).strip() != '' and pd.notna(hand['item_part_id']):
        locus_uri = get_locus_appellation_uri(hand['item_part_id'], hand['locus'])
        g.add((locus_uri, RDF.type, CRM['E41_Appellation']))
        g.add((locus_uri, RDFS.label, Literal(hand['locus'])))
        g.add((locus_uri, CRM['P2_has_type'], LOCUS_TYPE))
        g.add((handinstance_uri, CRM['P1_is_identified_by'], locus_uri))
        itempart_uri = DATA[f"Item_Part_{int(hand['item_part_id'])}"]
        g.add((itempart_uri, CRM['P1_is_identified_by'], locus_uri))

    if pd.notna(hand['ker']):
        g.add((handinstance_uri, ARCH.ker, Literal(hand['ker'])))

    # NB no direct link from Writing to Item Part — relies on the transitive Writing—P108→Hand←P56—ItemPart path.
    # This is because Hand is a human-made feature so is already closely connected to the Item Part,
    # and is in a sense exactly the link between the Activity and the physical surface.
    writing_uri = DATA[f"Writing_{int(hand['id'])}"]
    g.add((writing_uri, RDF.type, CRMtx.TX2_Writing))
    g.add((writing_uri, CRM.P108_has_produced, handinstance_uri))
    if pd.notna(hand['scribe_id']):
        scribe_uri = DATA[f"Scribe_{int(hand['scribe_id'])}"]
        g.add((writing_uri, CRM.P14_carried_out_by, scribe_uri))

    # PAS: Hand's accepted date/place now via E13 Attribute Assignment, per hand — not via the Writing event.
    # Seems closer toto the way palaeographers think: 'this is a hand of the eleventh century' often means
    # 'this hand has the style/characteristics of writing from the eleventh century, and therefore we attribute
    # the date of the writing event to that period'
    if pd.notna(hand['assigned_date_id']):
        date_uri = DATA[f"Date_Period_{int(hand['assigned_date_id'])}"]
        attr_assignment_date = DATA[f"HandDate_{int(hand['id'])}"]
        g.add((attr_assignment_date, RDF.type, CRM['E13_Attribute_Assignment']))
        g.add((attr_assignment_date, CRM['P140_assigned_attribute_to'], handinstance_uri))
        g.add((attr_assignment_date, CRM['P141_assigned'], date_uri))
        g.add((attr_assignment_date, CRM['P2_has_type'], ACCEPTED_TYPE))
    if pd.notna(hand['assigned_place_id']):
        place_uri = DATA[f"Place_{int(hand['assigned_place_id'])}"]
        attr_assignment_place = DATA[f"HandPlace_{int(hand['id'])}"]
        g.add((attr_assignment_place, RDF.type, CRM['E13_Attribute_Assignment']))
        g.add((attr_assignment_place, CRM['P140_assigned_attribute_to'], handinstance_uri))
        g.add((attr_assignment_place, CRM['P141_assigned'], place_uri))
        g.add((attr_assignment_place, CRM['P2_has_type'], ACCEPTED_TYPE))

    # arch:Script as TX10 Style is now linked to the TX2 Writing event, not the arch:Hand result, since TX10 is a Design or Procedure
    # and so describes the activity rather than the result. This is a deliberate decision *not* to follow CRMtex's use
    # of TXP12 has_style, which is defined as a property of the result of the activity (the writing) rather than the activity itself,
    # because this seems to directly contradict the definition of TX10 Style as subclass of E29 Design or Procedure.
    # TODO: CHECK and follow up with the CRMtex folk.
    if pd.notna(hand['script_id']):
        script_uri = DATA[f"Script_{int(hand['script_id'])}"]
        g.add((writing_uri, CRM.P33_used_specific_technique, script_uri))   # not TXP12, not handinstance_uri
    if pd.notna(hand['item_part_id']):
        itempart_uri = DATA[f"Item_Part_{int(hand['item_part_id'])}"] 
        # PAS: Fixed itempart - hand relationship.
        g.add((itempart_uri, CRM['P56_bears_feature'], handinstance_uri))
    if pd.notna(hand['appearance_id']):
        appearance_uri = DATA[f"Appearance_{int(hand['appearance_id'])}"]
        g.add((handinstance_uri, CRM.P2_has_type, appearance_uri))
    if pd.notna(hand['glossed_text_id']):
        glossed_text_uri = DATA[f"Category_{int(hand['glossed_text_id'])}"] 
        g.add((handinstance_uri,  CRM.P2_has_type, glossed_text_uri))
    # PAS: Latin Style is in fact a finer typology applied to arch:Script (e.g. Style I Anglo-Caroline minuscule),
    # so it's here modelled in the same way as arch:Script.
    # TODO: It would be easy and desirable to formally link the arch:LatinStyle to the arch:Script it's a substyle of,
    # and to unify the treatment of Latin and English in regard to arch:Script, arch:Style and arch:Appearance.
    if pd.notna(hand['latin_style_id']):
        latin_style_uri = DATA[f"LatinStyle_{int(hand['latin_style_id'])}"] 
        g.add((writing_uri, CRM.P33_used_specific_technique, latin_style_uri))   # was: handinstance_uri, CRMtx.TXP12_has_style

# PAS: First, we build the chain for MediaPermission inheritance taken from Repository->MediaPermission.
# Repository-MediaPermission is not a direct legal assertion about the Repository (a repository doesn't hold rights over
# itself) — it's a fallback policy applied to all Images at that repository unless the Image
# has its own override. So we apply it here per-Image instead of at Repository level.
itempart_to_current_item = data['itempart'].set_index('id')['current_item_id'].to_dict()
current_item_to_repository = data['currentitem'].set_index('id')['repository_id'].to_dict()
repository_to_media_permission = data['repository'].set_index('id')['media_permission_id'].to_dict()

for _, image in data['image'].iterrows():
    image_uri = DATA[f"Image_{int(image['id'])}"]
    g.add((image_uri, RDF.type,      CRM.E36_Visual_Item))

    if pd.notna(image['locus']) and str(image['locus']).strip() != '' and pd.notna(image['item_part_id']):
        locus_uri = get_locus_appellation_uri(image['item_part_id'], image['locus'])
        g.add((locus_uri, RDF.type, CRM['E41_Appellation']))
        g.add((locus_uri, RDFS.label, Literal(image['locus'])))
        g.add((locus_uri, CRM['P2_has_type'], LOCUS_TYPE))
        g.add((image_uri, CRM['P138_represents'], locus_uri))
        itempart_uri = DATA[f"Item_Part_{int(image['item_part_id'])}"]
        g.add((itempart_uri, CRM['P1_is_identified_by'], locus_uri))

    if pd.notna(image['caption']):
        g.add((image_uri, ARCH.caption, Literal(image['caption'])))
    # No valid data in DigiPal or MoA, I assume is obsolete
#    if pd.notna(image['image']):
#        g.add((image_uri, ARCH.image, Literal(image['image'])))
    if pd.notna(image['display_label']):
        g.add((image_uri, RDFS.label, Literal(image['display_label'])))
    if pd.notna(image['folio_side']):
        g.add((image_uri, ARCH.folio_side, Literal(image['folio_side'])))
    if pd.notna(image['iipimage']):
        g.add((image_uri, ARCH.iipimage, Literal(image['iipimage'])))
    if pd.notna(image['custom_label']):
        g.add((image_uri, ARCH.custom_label, Literal(image['custom_label'])))
    if pd.notna(image['width']): # à mettre dans un truc dimension 
        g.add((image_uri, ARCH.width, Literal(image['width'])))
    if pd.notna(image['height']): # à mettre dans un truc dimension
        g.add((image_uri, ARCH.height, Literal(image['height'])))
    # In DigiPal, image.size is always zero, but this is clearly an invalid data, so we drop it from export
    if pd.notna(image['size']) and image['size'] != 0: # à mettre dans un truc dimension
        g.add((image_uri, ARCH.size, Literal(image['size'])))
    if pd.notna(image['quire']):
        g.add((image_uri, ARCH.quire, Literal(image['quire'])))
    if pd.notna(image['page_boundaries']):
        g.add((image_uri, ARCH.page_boundaries, Literal(image['page_boundaries'])))
    if pd.notna(image['item_part_id']):
        itempart_uri = DATA[f"Item_Part_{int(image['item_part_id'])}"]
        g.add((image_uri,  CRM.P138_represents, itempart_uri))
    # ImagePermission logic to pull from Repository if no Image-specific permission is provided.
    effective_media_permission_id = image['media_permission_id']
    if pd.isna(effective_media_permission_id) and pd.notna(image['item_part_id']):
        current_item_id = itempart_to_current_item.get(image['item_part_id'])
        if pd.notna(current_item_id):
            repository_id = current_item_to_repository.get(current_item_id)
            if pd.notna(repository_id):
                effective_media_permission_id = repository_to_media_permission.get(repository_id)

    if pd.notna(effective_media_permission_id):
        media_permission_uri = DATA[f"MediaPermission_{int(effective_media_permission_id)}"]
        g.add((image_uri,  CRM.P104_is_subject_to, media_permission_uri))

for _, hand_image in data['hand_images'].iterrows():
    image_uri = DATA[f"Image_{int(hand_image['image_id'])}"]
    handinstance_uri = DATA[f"HandInstance_{int(hand_image['hand_id'])}"] 
    g.add((image_uri,  CRM.P138_represents, handinstance_uri))

for _, style in data['latinstyle'].iterrows():
    latin_style_uri = DATA[f"LatinStyle_{int(style['id'])}"]
    g.add((latin_style_uri, RDF.type,      CRMtx.TX10_Style))
    if pd.notna(style['style']):
        g.add((latin_style_uri, RDFS.label, Literal(style['style'])))

# NB that arch:Script is a TX10 Style, not a TX13 Script
for _, script in data['script'].iterrows():
    script_uri = DATA[f"Script_{int(script['id'])}"]
    g.add((script_uri, RDF.type, CRMtx.TX10_Style))
    if pd.notna(script['name']):
        g.add((script_uri, RDFS.label, Literal(script['name'])))

for _, appearance in data['appearance'].iterrows():
    appearance_uri = DATA[f"Appearance_{int(appearance['id'])}"]
    g.add((appearance_uri, RDF.type, ARCH.Appearance))   # was: ARCH.Script
    g.add((appearance_uri, RDFS.label, Literal(f"Appearance {appearance['text']}")))   # was labelled "Script {...}"
    if pd.notna(appearance['text']):
        g.add((appearance_uri, ARCH.text, Literal(appearance['text'])))
    if pd.notna(appearance['sort_order']):
        g.add((appearance_uri, ARCH.sort_order, Literal(appearance['sort_order'])))
    if pd.notna(appearance['description']):
        g.add((appearance_uri, DCTERMS.description, Literal(appearance['description'])))

for _, media_permission in data['mediapermission'].iterrows():
    media_permission_uri = DATA[f"MediaPermission_{int(media_permission['id'])}"]
    g.add((media_permission_uri, RDF.type, CRM.E30_Right))
    if pd.notna(media_permission['label']):
        g.add((media_permission_uri, RDFS.label, Literal(media_permission['label'])))
    if pd.notna(media_permission['display_message']):
        g.add((media_permission_uri, ARCH.display_message, Literal(media_permission['display_message'])))
    if pd.notna(media_permission['permission']):
        g.add((media_permission_uri, ARCH.permission, Literal(media_permission['permission'])))

for _, allograph in data['allograph'].iterrows():
    allograph_uri = DATA[f"Allograph_{int(allograph['id'])}"]
    g.add((allograph_uri, RDF.type, ARCH.Allograph))
    if pd.notna(allograph['name']):
        g.add((allograph_uri, RDFS.label, Literal(allograph['name'])))
    if pd.notna(allograph['character_id']):
        character_uri = DATA[f"Character_{int(allograph['character_id'])}"]
        g.add((allograph_uri,  CRM.P138_represents, character_uri))

BEFORE_TYPE = DATA["Befor_Allograph"]
g.add((BEFORE_TYPE, RDF.type, CRM.E55_Type))
g.add((BEFORE_TYPE, RDFS.label, Literal("Before", lang="en")))

AFTER_TYPE = DATA["After_Allograph"]
g.add((AFTER_TYPE, RDF.type, CRM.E55_Type))
g.add((AFTER_TYPE, RDFS.label, Literal("After", lang="en")))

for _, annotation in data['annotation'].iterrows():
    annotation_uri = DATA[f"Annotation_{int(annotation['id'])}"]
    g.add((annotation_uri, RDF.type, ANNO.Annotation)) 
    g.add((annotation_uri, RDFS.label, Literal(f"{annotation['id']}")))
    if pd.notna(annotation['cutout']):
        g.add((annotation_uri, ARCH.cutout, Literal(annotation['cutout'])))
    if pd.notna(annotation['geo_json']):
        g.add((annotation_uri, ARCH.geo_json, Literal(annotation['geo_json'])))
    if pd.notna(annotation['display_note']) and str(annotation['display_note']).strip() != '' and str(annotation['display_note']).strip().lower() != 'undefined':
        g.add((annotation_uri, ARCH.display_note, Literal(annotation['display_note'])))
    if pd.notna(annotation['rotation']):
        g.add((annotation_uri, ARCH.rotation, Literal(annotation['rotation'])))
    if pd.notna(annotation['holes']):
        g.add((annotation_uri, ARCH.holes, Literal(annotation['holes'])))
    if pd.notna(annotation['vector_id']):
        g.add((annotation_uri, ARCH.vector_id, Literal(annotation['vector_id'])))
    if pd.notna(annotation['image_id']):
        image_uri = DATA[f"Image_{int(annotation['image_id'])}"]
        g.add((annotation_uri, ANNO.hasTarget, image_uri))
    if pd.notna(annotation['status_id']):
        status_uri = DATA[f"Status_{int(annotation['status_id'])}"]
        g.add((annotation_uri,  CRM.P2_has_type, status_uri)) #traiter status comme un E55_Type

    if pd.notna(annotation['graph_id']):
        graph_uri = DATA[f"Graph_{int(annotation['graph_id'])}"]
        g.add((annotation_uri, ANNO.hasBody, graph_uri))

for _, graph in data['graph'].iterrows():
    graph_uri = DATA[f"Graph_{int(graph['id'])}"]
    g.add((graph_uri, RDF.type, ARCH.Graph))
    if pd.notna(graph['display_label']):
        g.add((graph_uri, RDFS.label, Literal(graph['display_label'])))

    if pd.notna(graph['idiograph_id']):
        idiograph_uri = DATA[f"Idiograph_{int(graph['idiograph_id'])}"]
        g.add((graph_uri,  CRM.P65_shows_visual_item, idiograph_uri))
    
    if pd.notna(graph['hand_id']):
        handinstance_uri = DATA[f"HandInstance_{int(graph['hand_id'])}"]
        g.add((handinstance_uri,  CRM.P46_is_composed_of, graph_uri))

for _, idiograph in data['idiograph'].iterrows():
    idiograph_uri = DATA[f"Idiograph_{int(idiograph['id'])}"]
    g.add((idiograph_uri, RDF.type, ARCH.Idiograph))
    if pd.notna(idiograph['display_label']):
        g.add((idiograph_uri, RDFS.label, Literal(idiograph['display_label'])))

    if pd.notna(idiograph['allograph_id']):
        allograph_uri = DATA[f"Allograph_{int(idiograph['allograph_id'])}"]
        g.add((idiograph_uri,  CRM.P138_represents, allograph_uri))

    if pd.notna(idiograph['scribe_id']):
        scribalpractice_uri = DATA[f"Scribal_Practice_{int(idiograph['scribe_id'])}"]
        g.add((scribalpractice_uri,  CRM.P148_has_component, idiograph_uri))
    
for _, feature in data['feature'].iterrows():
    feature_uri = DATA[f"Feature_{int(feature['id'])}"]
    g.add((feature_uri, RDF.type, ARCH.Feature))
    if pd.notna(feature['name']):
        g.add((feature_uri, RDFS.label, Literal(feature['name'])))

for _, component in data['component'].iterrows():
    genericcomponent_uri = DATA[f"GenericComponent_{int(component['id'])}"]
    g.add((genericcomponent_uri, RDF.type, ARCH.GenericComponent))
    if pd.notna(component['name']):
        g.add((genericcomponent_uri, RDFS.label, Literal(component['name'])))

for _, allo_compo in data['allographcomponent'].iterrows():
    allo_uri = DATA[f"Allograph_{int(allo_compo['allograph_id'])}"]
    compo_uri = DATA[f"GenericComponent_{int(allo_compo['component_id'])}"]
    # PAS: Fixed allograph - component relationship.
    g.add((allo_uri,  CRM['P148_has_component'], compo_uri)) 

# PAS: The fact that the RDB has two tables, graphcomponent and graphcomponent_feature, is an artefact of Django's M2M structure.
# Instead of reproducing that here, better to keep the conceptual part.
# Some properties are also adjusted to better reflect the conceptual model, particularly that 'Feature' in Archetype is really a Type in CIDOC-CRM.

# Component features, i.e. the list of all possible features that a given component could have.
# TODO: FIX!!
for _, compo_feature in data['component_features'].iterrows():
    compo_uri = DATA[f"GenericComponent_{int(compo_feature['component_id'])}"]
    feature_uri = DATA[f"Feature_{int(compo_feature['feature_id'])}"]
    g.add((compo_uri, CRM['P2_has_type'], feature_uri))    # was P56_bears_feature

# Now we deal with actual Features recorded on Components of real annotated Graphs.
gc_features = data['graphcomponent_features'].merge(
    data['graphcomponent'],
    left_on='graphcomponent_id', right_on='id',
    suffixes=('', '_gc')
)
for _, gcf in gc_features.iterrows():
    graphcomponent_uri = DATA[f"GraphComponent_{int(gcf['graphcomponent_id'])}"]
    g.add((graphcomponent_uri, RDF.type, ARCH.GraphComponent))

    graph_uri = DATA[f"Graph_{int(gcf['graph_id'])}"]
    g.add((graph_uri, CRM['P46_is_composed_of'], graphcomponent_uri))

    genericcomponent_uri = DATA[f"GenericComponent_{int(gcf['component_id'])}"]
    g.add((graphcomponent_uri, CRM['P65_shows_visual_item'], genericcomponent_uri))

    feature_uri = DATA[f"Feature_{int(gcf['feature_id'])}"]
    g.add((graphcomponent_uri, CRM['P2_has_type'], feature_uri))

ic_features = data['idiographcomponent_features'].merge(
    data['idiographcomponent'],
    left_on='idiographcomponent_id', right_on='id',
    suffixes=('', '_ic')
)
for _, icf in ic_features.iterrows():
    idiographcomponent_uri = DATA[f"IdiographComponent_{int(icf['idiographcomponent_id'])}"]
    g.add((idiographcomponent_uri, RDF.type, ARCH.VisualComponent))

    idiograph_uri = DATA[f"Idiograph_{int(icf['idiograph_id'])}"]
    g.add((idiograph_uri, CRM['P148_has_component'], idiographcomponent_uri))

    genericcomponent_uri = DATA[f"GenericComponent_{int(icf['component_id'])}"]
    g.add((idiographcomponent_uri, CRM['P138_represents'], genericcomponent_uri))

    feature_uri = DATA[f"Feature_{int(icf['feature_id'])}"]
    g.add((idiographcomponent_uri, CRM['P2_has_type'], feature_uri))


# PAS: Remember, the Archetype Owners table does *not* record owners, but rather assertions of current or historical 
# Ownership.
for _, item_owner in data['itempart_owners'].iterrows():
    itempart_uri = DATA[f"Item_Part_{int(item_owner['itempart_id'])}"]
    owner_uri = DATA[f"Owner_{int(item_owner['owner_id'])}"]
    g.add((owner_uri,  CRM['P140_assigned_attribute_to'], itempart_uri)) 

for _, hand_desc in data['handdescription'].iterrows():
    hand_desc_uri = DATA[f"HandDescription_{int(hand_desc['id'])}"]
    g.add((hand_desc_uri, RDF.type, CRM.E31_Document))
    if pd.notna(hand_desc['label']):
        g.add((hand_desc_uri, RDFS.label, Literal(hand_desc['label'])))
    if pd.notna(hand_desc['description']):
        g.add((hand_desc_uri, DCTERMS.description, Literal(hand_desc['description'])))
    if pd.notna(hand_desc['hand_id']):
        handinstance_uri = DATA[f"HandInstance_{int(hand_desc['hand_id'])}"]
        g.add((hand_desc_uri, CRM.P67_refers_to, handinstance_uri))   # subject/object flipped
    if pd.notna(hand_desc['source_id']):
        source_uri = DATA[f"Source_{int(hand_desc['source_id'])}"]
        g.add((hand_desc_uri,  CRM.P70i_is_documented_in, source_uri))

for _, scribe_ref in data['scribe_reference'].iterrows():
    scribe_uri = DATA[f"Scribe_{int(scribe_ref['scribe_id'])}"]
    ref_uri = DATA[f"Reference_{int(scribe_ref['reference_id'])}"]
    g.add((scribe_uri,  CRM.P70i_is_documented_in, ref_uri))

for _, reference in data['reference'].iterrows():
    ref_uri = DATA[f"Reference_{int(reference ['id'])}"]
    g.add((ref_uri, RDF.type, CRM.E31_Document))
    if pd.notna(reference['name_index']):
        g.add((ref_uri, RDFS.label, Literal(reference['name_index'])))
    if pd.notna(reference['full_reference']):
        g.add((ref_uri, ARCH.full_reference, Literal(reference['full_reference'])))


for _, img_annot_status in data['imageannotationstatus'].iterrows():
    img_annot_status_uri = DATA[f"Status_{int(img_annot_status['id'])}"]
    g.add((img_annot_status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(img_annot_status['name']):
        g.add((img_annot_status_uri, RDFS.label, Literal(img_annot_status['name'])))
    
for _, ontograph_type in data['ontographtype'].iterrows():
    ontograph_type_uri = DATA[f"OntographType_{int(ontograph_type['id'])}"]
    g.add((ontograph_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(ontograph_type['name']):
        g.add((ontograph_type_uri, RDFS.label, Literal(ontograph_type['name'])))

for _, ontograph in data['ontograph'].iterrows():
    ontograph_uri = DATA[f"Ontograph_{int(ontograph['id'])}"]
    g.add((ontograph_uri, RDF.type, ARCH.Ontograph))
    if pd.notna(ontograph['name']):
        g.add((ontograph_uri, RDFS.label, Literal(ontograph['name'])))
    if pd.notna(ontograph['ontograph_type_id']):
        ontograph_type_uri = DATA[f"OntographType_{int(ontograph['ontograph_type_id'])}"]
        g.add((ontograph_uri,  CRM.P2_has_type, ontograph_type_uri )) 
    if pd.notna(ontograph['nesting_level']):
        g.add((ontograph_uri, ARCH.nesting_level, Literal(ontograph['nesting_level'])))
    if pd.notna(ontograph['sort_order']):
        g.add((ontograph_uri, ARCH.sort_order, Literal(ontograph['sort_order'])))

for _, scribe in data['scribe'].iterrows():
    scribe_uri = DATA[f"Scribe_{int(scribe['id'])}"]
    g.add((scribe_uri, RDF.type, ARCH.Scribe))
    if pd.notna(scribe['name']):
        g.add((scribe_uri, RDFS.label, Literal(scribe['name'])))
    if pd.notna(scribe['scriptorium_id']):
        institution_uri = DATA[f"Institution_{int(scribe['scriptorium_id'])}"]
        g.add((institution_uri, CRM.P107_has_current_or_former_member, scribe_uri))

    scribalpractice_uri = DATA[f"Scribal_Practice_{int(scribe['id'])}"]
    g.add((scribalpractice_uri, RDF.type, ARCH.Scribal_Practice))
    g.add((scribe_uri, ARCH.characterised_by, scribalpractice_uri))


for _, character in data['character'].iterrows():
    character_uri = DATA[f"Character_{int(character['id'])}"]
    g.add((character_uri, RDF.type, ARCH.Character))
    if pd.notna(character['name']):
        g.add((character_uri, RDFS.label, Literal(character['name'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, ARCH.unicode_point, Literal(character['unicode_point'])))
    if pd.notna(character['unicode_point']):
        g.add((character_uri, ARCH.unicode_point, Literal(character['unicode_point'])))
    if pd.notna((character['ontograph_id'])):
        ontograph_uri = DATA[f"Ontograph_{int(character['ontograph_id'])}"]
        g.add((character_uri,  CRM.P138_represents, ontograph_uri)) 
    if pd.notna((character['form_id'])):
        form_uri = DATA[f"FormCharacter_{int(character['form_id'])}"]
        g.add((character_uri,  CRM.P2_has_type, form_uri)) 

for _, character_compo in data['character_components'].iterrows():
    character_uri = DATA[f"Character_{int(character_compo['character_id'])}"]
    genericcomponent_uri = DATA[f"GenericComponent_{int(character_compo['component_id'])}"]
    g.add((character_uri,  CRM['P148_has_component'], genericcomponent_uri)) 

for _, form in data['characterform'].iterrows():
    form_uri = DATA[f"FormCharacter_{int(form['id'])}"]
    g.add((form_uri, RDF.type, CRM.E55_Type))
    if pd.notna(form['name']):
        g.add((form_uri, RDFS.label, Literal(form['name'])))

for _, repository_type in data['ownertype'].iterrows():
    repository_type_uri = DATA[f"RepositoryType_{int(repository_type['id'])}"]
    g.add((repository_type_uri, RDF.type, CRM.E55_Type))
    if pd.notna(repository_type['name']):
        g.add((repository_type_uri, RDFS.label, Literal(repository_type['name'])))

for _, source in data['source'].iterrows():
    source_uri = DATA[f"Source_{int(source['id'])}"]
    g.add((source_uri, RDF.type, CRM.E31_Document))
    if pd.notna(source['label']):
        g.add((source_uri, RDFS.label, Literal(source['label'])))
    if pd.notna(source['name']):
        g.add((source_uri, ARCH.name, Literal(source['name'])))
    if pd.notna(source['priority']):
        g.add((source_uri, ARCH.priority, Literal(source['priority'])))
    if pd.notna(source['label_styled']):
        g.add((source_uri, ARCH.label_styled, Literal(source['label_styled'])))
    if pd.notna(source['label_slug']):
        g.add((source_uri, ARCH.label_slug, Literal(source['label_slug'])))

for _, status in data['status'].iterrows():
    status_uri = DATA[f"Status_{int(status['id'])}"]
    g.add((status_uri, RDF.type, CRM.E55_Type))
    if pd.notna(status['name']):
        g.add((status_uri, RDFS.label, Literal(status['name'])))

# -------------------------------------------------------- SERIALISATION --------------------------------------------------------
# Add timestamp, database and file format to filename help versioning and provenance tracking.

timestamp = datetime.now().strftime("%Y%m%d%H%M")
output_filename = f"data_{DB_NAME}_{OUTPUT_FORMAT}_{timestamp}.rdf"
g.serialize(destination=output_filename, format=OUTPUT_FORMAT)
print(f"Exported to {output_filename}")
print(f"✓ Fichier RDF généré — {len(g)} triplets")
