# Background/previous work

- In the DigiPal project and resulting Archetype software we developed a model and RDB for palaeographical annotations which is now used for a dozen or more projects, including particularly Archetype but also Models of Authority, Exon Domesday and others.
- We always wanted to formalise this model but never really managed.
- The objective of the current project is to do this, mapping from the original Archetype SQL to a semantic web/LOD structure (formalising the model, aligning it with CIDOC-CRM, producing RDF and SKOS outputs)
- The previous stage has produced a first full draft conceptual model of Archetype, and a full draft mapping and export of the DigiPal database in RDF (about 1.4M triples)
    - Concretely, this involves a copy of the DigiPal database (running locally in Postgres), and python code to access the database and convert it to RDF
    - The model is partly in the RDF, and also represented in a drawio diagram
    - The mapping from SQL to RDF is implicit in the python code
    - The previous stage was itself based on an earlier draft ('v1'), and two reports were produced as part of that work, explaining changes from 'v1' to 'v2' and then to the current 'v3', the main design decisions behind these changes, and some points noted for future work.
    - The current 'v3' state is represented by the drawio diagram, python code, RDF output and two reports, all of which are attached for your reference.
- Other useful resources that you can find online include the CIDOC-CRM standard, the CRMtex standard, and the Django code used for the DigiPal/Archetype software (particularly the models.py file which is available at https://raw.githubusercontent.com/kcl-ddh/digipal/refs/heads/master/digipal/models.py)

# Current Phase

The goal of this phase is to further refine and correct the model and code, and to produce more usable results in new formats, particularly a better diagram and a formalisation of the model as a standalone OWL file. The main tasks/objectives are as follows, in this order:

1.  Check the existing RDF and python code against the reports to ensure consistency, and to update the reports as necessary, particularly regarding what has and has not been fixed already in the code.
2.  Propose changes to the code for cases in the reports which have been resolved but not implemented yet, and I will then implement each change one by one and regenerate the new RDF. This will be done iteratively, one fix at a time, and checking the resulting code each time to ensure consistency and avoid any regression errors.
3.  We then run a full check of the RDF and python code to ensure that everything is stable and consistent with the relevant standards (CIDOC-CRM, etc.). If this is good then we can move on, otherwise we return to (1).
4.  Fix the drawio diagram. This was generated from the RDF and reports, but spot checking reveals a number of errors/inconsistencies. The RDF should be considered 'ground truth' and the diagram adjusted to reflect the RDF, not the other way around.
5.  Once the diagram is corrected, I will check it myself for conceptual consistency. If there are any issues then we will discuss them and update the diagram and/or RDF and python code as necessary.
6.  A relatively large number of triples use custom 'EX' properties as a catch-all for data that was not mapped to CIDOC-CRM or other standards. However, my suspicion is that many of these map relatively easily to other standards such as RDFS or Dublin Core. A small number of these have been done already, but most have not, so the remaining cases should be analysed to decide whether to make them more standard or leave them as they are, particularly considering the trade-off of standards-compliance vs unhelpful complexity of the model.
7.  Repeat steps 3 and 4 for the updated model, diagram and code/RDF
8.  Once the model is established then we produce a standalone OWL file that formalises the ontology independently of the RDF.
9.  We then produce a formal statement of the mapping, for instance in R2RML

This then concludes the current phase. The next phase will be to produce the SKOS vocabulary file, as noted under 'other work' in the report, but this will be done in a separate discussion.

# General Instructions

You are to proceed slowly and carefully, step by step. You are to check with me each step of the way, and any uncertainties or ambiguities must be discussed. You are encouraged to suggest solutions, but you should not guess answers or implement any changes without asking me first. I have a very good knowledge of the underlying database and the design decisions behind it, and I have access to the original data, so in almost all cases I will be able to answer questions about what things mean or why they were done a certain way, and I can run any SQL queries to verify the data if necessary.

The principal goal is a model and export that covers the DigiPal database. However, as noticed, the same structure was used for other projects, so it is normal that the model will include some elements that are not included in DigiPal and so are not in the RDF. These should be noted but it is not a problem as such.

It is likely (and normal) that not all the data in DigiPal will be included in the export. In addition to the normal reasons (e.g. interface or implementation details that are not useful to be shared), the DigiPal database also contains some fields that were never used or that later became redundant and were not deleted. Again, any data that is not included should be noted and checked with me, but it is not a problem as such.
