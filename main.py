# -*- coding: utf-8 -*- 

# external imports
import os
from dotenv import load_dotenv
import re
import pymarc
from pymarc import Subfield
from enum import Enum
from typing import List, Dict
import xml.etree.ElementTree as ET
from unidecode import unidecode

# Internal import
import api.Koha_SRU as ksru
import fcr_func as fcf
from errors_manager import Errors_Manager, Errors

# ---------- Init ----------
load_dotenv()

RECORDS_FILE_PATH = os.getenv("RECORDS_FILE")
FILE_OUT = os.getenv("FILE_OUT")
ERRORS_FILE_PATH = os.path.abspath(os.getenv("ERRORS_FILE"))
ERR_MAN = Errors_Manager(ERRORS_FILE_PATH)
MANUAL_CHECKS_FILE = os.getenv("MANUAL_CHECKS_FILE")
KOHA_URL = os.getenv("KOHA_URL")
sru = ksru.Koha_SRU(KOHA_URL, ksru.SRU_Version.V1_1)
IGNORE_FIELDS = os.getenv("IGNORE_FIELDS")
ignored_fields = [ignored_field.strip() for ignored_field in IGNORE_FIELDS.split(",")]
U4XX_list = [str(nb) for nb in range(400, 500)]
for ignored_field in ignored_fields:
    if ignored_field in U4XX_list:
        U4XX_list.remove(ignored_field)
NS = {
    'marc': 'http://www.loc.gov/MARC21/slim'
}

# ---------- Class def ----------
# ----- Manual checks -----
class Manual_Subfield_Check(object):
    # This is mainly used to know if we have to normalise the field in the check
    def __init__(self, code:str, value:str, normalised:str="0") -> None:
        self.code = code
        self.normalised = normalised == "1"
        self.value = value.strip()
        if self.normalised == True:
            self.value = normalize_check_value(self.value)

class Manual_Check(object):
    def __init__(self, xml_check:ET.Element) -> None:
        self.bibnb = xml_check.attrib["bibnb"]
        self.subfields:Dict[str, Manual_Subfield_Check] = {}
        for xml_subf in xml_check.findall("subfield"):
            if "normalised" in xml_subf.attrib:
                self.subfields[xml_subf.attrib["code"]] = Manual_Subfield_Check(xml_subf.attrib["code"], xml_subf.text, xml_subf.attrib["normalised"])
            else:
                self.subfields[xml_subf.attrib["code"]] = Manual_Subfield_Check(xml_subf.attrib["code"], xml_subf.text)

    def check(self, field:pymarc.field.Field) -> bool:
        """Returns if the provided field passes the manual check"""
        valid_checks = 0
        # Loop through subfield to check
        for code in self.subfields:
            # Get this subfield in the record field
            subf = field.get(code)
            if subf:
                subf = subf.strip()
                # Normlized the content if this subfield is normalised
                if self.subfields[code].normalised:
                    subf = normalize_check_value(subf)
                # Actual check
                if self.subfields[code].value == subf:
                    valid_checks += 1 # Increase counter
        
        # Returns true if valdi checks are equal to the number of subfield checked
        return valid_checks == len(self.subfields)

# ----- Known list -----
class Steps(Enum):
    ISSN = 0
    MANUAL_CHECK = 1
    ISBN = 1

class Known_Element(object):
    def __init__(self, step:Steps, query:str, subfields:List[Subfield], manual_check:Manual_Check=None, issn:str=None, isbn:str=None) -> None:
        self.step = step
        self.query = query
        self.subfields = subfields
        self.has_link = subfields[0].code == "9"
        # Manual check
        self.manual_check = manual_check
        # ISSN
        self.issn = issn
        self.normalized_issn = None
        if self.issn is not None and self.step == Steps.ISSN:
            self.normalized_issn = normalize_intnat_id(self.issn, Steps.ISSN)
        # ISBN
        self.isbn = isbn
        self.normalized_isbn = None
        if self.isbn is not None and self.step == Steps.ISBN:
            self.normalized_isbn = normalize_intnat_id(self.isbn, Steps.ISBN)

KNOWN_LIST:List[Known_Element] = []
MANUAL_CHECKS_KNOWN_LIST:List[Known_Element] = []

# ---------- Func def ----------

def normalize_intnat_id(txt:str, step: Steps) -> str:
    """Returned a normalized version of an international ID"""
    if step == Steps.ISSN:
        return re.sub("[^0-9]", "", txt)
    elif step == Steps.ISBN:
        return re.sub("[^0-9X]", "", txt.upper())
    return ""

def normalize_check_value(txt:str) -> str:
    """Returns the strig normalized for the manual checks"""
    return unidecode(txt).upper().strip()

def generate_intnat_id_sru_query(txt:str, step:Steps):
    """Returns the SRU request for an ISSN / ISBN"""
    txt = fcf.delete_for_sudoc(txt).strip()
    if txt == "":
        return ""
    # Chose the index
    index = None
    if step == Steps.ISSN:
        index = ksru.SRU_Indexes.ISSN
    elif step == Steps.ISBN:
        index = ksru.SRU_Indexes.ISBN
    # Leave if no Index
    if not index:
        return ""
    # Return the query
    sru_request = [ksru.Part_Of_Query(index,ksru.SRU_Relations.EQUALS,txt)]
    return sru.generate_query(sru_request)

def xml_return_all_subfields(record:ET.Element, tag:str, code:str) -> List[ET.Element]:
    """Returns all subfields for all field with this tag"""
    output = []
    for field in record.findall(f".//marc:datafield[@tag='{tag}']", NS):
        output += field.findall(f".//marc:subfield[@code='{code}']", NS)
    return output

def generate_4XX_author_from_7XX(field:ET.Element) -> str:
    """Returns the 7XX as a string for a 4XX$a from a 7XX"""
    # So here the plugin is funky
    # For some reasons, 700 & 702 are build similarly but 701 is not and is just bugged I think
    # Obviously, 711 is just not here because why put 701 & 711 when you can just put 701
    # For 710 & 712, there's a little twist : 710$b is bugged and never imported
    # Which was fixed in 712 
    output = ""
    tag = field.get("tag")

    # Gets $a, $b, $c, $d, $f
    a_node = field.find(".//marc:subfield[@code='a']", NS)
    b_node = field.find(".//marc:subfield[@code='b']", NS)
    c_node = field.find(".//marc:subfield[@code='c']", NS)
    d_node = field.find(".//marc:subfield[@code='d']", NS)
    e_node = field.find(".//marc:subfield[@code='e']", NS)
    f_node = field.find(".//marc:subfield[@code='f']", NS)

    # Easy common part for 70X
    if tag in ["700", "701", "702"]:
        # Entry ($a)
        if a_node is not None:
            output += a_node.text
        
        # Name Other than entry ($b)
        if b_node is not None:
            output += f", {b_node.text}"

        # Roman numerals ($d)
        if d_node is not None:
            output += f" {d_node.text}"

        # Handling $c & $f
        # 700's $c & $f handling should be correctly replicated
        # It writes ($c ; $f) if there's both, ($c) if only $c, ($f) if only $f
        # For 701, it's bugged and always writes " - " after $c, does not use ";""
        if c_node is not None and f_node is not None and tag in ["700", "702"]:
            output += f" ({c_node.text} ; {f_node.text})"
        elif c_node is not None and f_node is None and tag in ["700", "702"]:
            output += f" ({c_node.text})"
        elif c_node is None and f_node is not None and tag in ["700", "701", "702"]: # Works for 701 too
            output += f" ({f_node.text})"
        # 701 specifics
        elif c_node is not None and f_node is not None and tag in ["701"]:
            output += f" ({c_node.text} - {f_node.text})"
        elif c_node is not None and not f_node is None and tag in ["701"]:
            output += f" ({c_node.text} - )"
    
    # handling 710 & 712
    elif tag in ["710", "712"]:
        # Nb of meeting ($d)
        if d_node is not None:
            output += f"{d_node.text} "
        
        # Entry element ($a)
        if a_node is not None:
            output += a_node.text
        
        # Subdvision ($b)
        # Only for 712 because 710 is bugged
        if b_node is not None and tag in ["712"]:
            output += f", {b_node.text}"

        # Handling $e & $f
        # 710's $e & $f handling should be correctly replicated
        # It writes " ($f - $e)" if there's both, " ($f - )" if only $f
        # " ($e)" if only $e
        if e_node is not None and f_node is not None:
            output += f" ({f_node.text} - {e_node.text})"
        elif e_node is None and f_node is not None:
            output += f" ({f_node.text} - )"
        elif e_node is not None and f_node is None:
            output += f" ({e_node.text})"

    # Return the string
    return output

def generate_4XX_subfields(record:ET.Element) -> List[str]:
    """Returns all subfields formatted for pymarc for the 4XX in Koha.
    It seems that Koha always go for first occurrence, so we do this"""
    output = []
    # Get bibnb ($9 & $0)
    bibnb_node = record.find(".//marc:controlfield[@tag='001']", NS)
    if bibnb_node is not None: # DON'T DO if bibnb_node, it evaluates to false as there's no children
        output.append(Subfield(code="9", value=bibnb_node.text))
        output.append(Subfield(code="0", value=bibnb_node.text))
    
    # Subfield $a
    # Why the fuck is the order 700 → 702 → 710 → 701 → 712 → 200$f
    # I'm going to assume there's a logic I'm too lazy to write here
    # But tbh, I'm not convinced if it's that
    # First check 700
    authors_fields = record.findall(".//marc:datafield[@tag='700']", NS)
    # If no 700, check 702
    if len(authors_fields) == 0:
        authors_fields += record.findall(".//marc:datafield[@tag='702']", NS) # += just in case
    # If no 700 or 702, check 710
    if len(authors_fields) == 0: # Not a elif
        authors_fields += record.findall(".//marc:datafield[@tag='710']", NS) # += just in case
    # If no 700 or 702 or 710, check 701
    if len(authors_fields) == 0: # Not a elif
        authors_fields += record.findall(".//marc:datafield[@tag='701']", NS) # += just in case
    # If no 700 or 702 or 710 or 701, check 712
    if len(authors_fields) == 0: # Not a elif
        authors_fields += record.findall(".//marc:datafield[@tag='712']", NS) # += just in case
    # Add the subfield if we have a value    
    if len(authors_fields) > 0:
        author_text = generate_4XX_author_from_7XX(authors_fields[0])
        if author_text != "":
            output.append(Subfield(code="a", value=author_text))
    # If no 7XX, try 200$f
    else:
        authors_200_nodes = xml_return_all_subfields(record, "200", "f")
        if len(authors_200_nodes) > 0: # Not a elif
            output.append(Subfield(code="a", value=authors_200_nodes[0].text))

    # Get publication place ($c)
    # Does not look for 214 ?
    publication_place_nodes = xml_return_all_subfields(record, "210", "a")
    if len(publication_place_nodes) > 0:
        output.append(Subfield(code="c", value=publication_place_nodes[0].text))
    
    # Get publication date ($d)
    # Does not look for 214 ?
    publication_date_nodes = xml_return_all_subfields(record, "210", "d")
    if len(publication_date_nodes) > 0:
        output.append(Subfield(code="d", value=publication_date_nodes[0].text))

    # Get edition ($e)
    edition_nodes = xml_return_all_subfields(record, "205", "a")
    if len(edition_nodes) > 0:
        output.append(Subfield(code="e", value=edition_nodes[0].text))
    
    # Get Section / part number ($h)
    # First check 200$h
    section_nb_nodes = xml_return_all_subfields(record, "200", "h")
    # If no 200$h, check 225$h
    if len(section_nb_nodes) == 0:
        section_nb_nodes += xml_return_all_subfields(record, "225", "h") # += just in case
    # If no 200$h && no 225$h, check 500$h
    if len(section_nb_nodes) == 0: # Not a elif
        section_nb_nodes += xml_return_all_subfields(record, "500", "h") # += just in case
    # Add the subfield if we have a value    
    if len(section_nb_nodes) > 0:
        output.append(Subfield(code="h", value=section_nb_nodes[0].text))

    # Get Section / part name ($i)
    # First check 200$i
    section_name_nodes = xml_return_all_subfields(record, "200", "i")
    # If no 200$i, check 225$i
    if len(section_name_nodes) == 0:
        section_name_nodes += xml_return_all_subfields(record, "225", "i") # += just in case
    # If no 200$i && no 225$i, check 500$i
    if len(section_name_nodes) == 0: # Not a elif
        section_name_nodes += xml_return_all_subfields(record, "500", "i") # += just in case
    # Add the subfield if we have a value    
    if len(section_name_nodes) > 0:
        output.append(Subfield(code="i", value=section_name_nodes[0].text))

    # Get parallel title ($l)
    parallel_title_nodes = xml_return_all_subfields(record, "200", "d")
    if len(parallel_title_nodes) > 0:
        output.append(Subfield(code="l", value=parallel_title_nodes[0].text))
    
    # Get Publisher's name ($n)
    # Does not look for 214 ?
    publisher_name_nodes = xml_return_all_subfields(record, "210", "c")
    if len(publisher_name_nodes) > 0:
        output.append(Subfield(code="n", value=publisher_name_nodes[0].text))

    # Get Other title information ($o)
    other_title_nodes = xml_return_all_subfields(record, "200", "e")
    if len(other_title_nodes) > 0:
        output.append(Subfield(code="o", value=other_title_nodes[0].text))

    # Get physical description ($p)
    physical_desc_nodes = xml_return_all_subfields(record, "215", "a")
    if len(physical_desc_nodes) > 0:
        output.append(Subfield(code="p", value=physical_desc_nodes[0].text))

    # Get title ($t)
    # First check 200$a
    title_nodes = xml_return_all_subfields(record, "200", "a")
    # If no 200$a, check 225$a
    if len(title_nodes) == 0:
        title_nodes += xml_return_all_subfields(record, "225", "a") # += just in case
    # If no 200$a && no 225$a, check 500$a
    if len(title_nodes) == 0: # Not a elif
        title_nodes += xml_return_all_subfields(record, "500", "a") # += just in case
    # Add the subfield if we have a value
    if len(title_nodes) > 0:
        output.append(Subfield(code="t", value=title_nodes[0].text))

    # Get URI ($u)
    uri_nodes = xml_return_all_subfields(record, "856", "u")
    if len(uri_nodes) > 0:
        output.append(Subfield(code="u", value=uri_nodes[0].text))

    # Get volume number ($v)
    # First check 225$v
    volume_nb_nodes = xml_return_all_subfields(record, "225", "v")
    # If no 225$v, check 200$h
    if len(volume_nb_nodes) == 0:
        volume_nb_nodes += xml_return_all_subfields(record, "200", "h")
    # Add the subfield if we have a value
    if len(volume_nb_nodes) > 0:
        output.append(Subfield(code="v", value=volume_nb_nodes[0].text))

    # Get the ISSN ($x)
    # First check if there are 011$y or 011$x
    wrong_issn_nodes = xml_return_all_subfields(record, "011", "y")
    wrong_issn_nodes += xml_return_all_subfields(record, "011", "z") 
    # ONLY if there are none we check if there's a 011$a
    if len(wrong_issn_nodes) == 0:
        issn_nodes = xml_return_all_subfields(record, "011", "a")
        if len(issn_nodes) > 0:
            output.append(Subfield(code="x", value=issn_nodes[0].text))

    # Get the ISBN ($y)
    # So the plugin is kinda strange here but :
    # I t first checks if there is a 013 and if there is, gets its $a
    # Then (and not ELSE IF) it checks if there is a 010 (not if there's a 010$a)
    # If there is, gets its $a, but if there's no $a, empties the value it previously had
    # So we're tweaking the process but replicating it
    # First get 010$a
    isbn_nodes = xml_return_all_subfields(record, "010", "a")
    # We have a match, use it
    if len(isbn_nodes) > 0:
        output.append(Subfield(code="y", value=isbn_nodes[0].text))
    # If no 010$a, we check if there were 010 at all, if not, check 013$a
    elif len(record.findall(".//marc:datafield[@tag='010']", NS)) == 0:
        ismn_nodes = xml_return_all_subfields(record, "013", "a")
        # Add the subfield if we have a value
        if len(ismn_nodes) > 0:
            output.append(Subfield(code="y", value=ismn_nodes[0].text))

    # Return the subfields
    return output

def add_known_element(known_element:Known_Element):
    """Adds a new known element"""
    KNOWN_LIST.append(known_element)

def add_manual_check_known_element(known_element:Known_Element):
    """Adds a new known element"""
    MANUAL_CHECKS_KNOWN_LIST.append(known_element)

def get_known_element_by_intnat_id(id:str, step:Steps) -> Known_Element:
    """Checks if this international ID is a known element"""
    for known_element in KNOWN_LIST:
        # ISSN
        if step == Steps.ISSN:
            if known_element.issn == id:
                return known_element
            elif known_element.normalized_issn == normalize_intnat_id(id, Steps.ISSN):
                return known_element
            elif known_element.query == generate_intnat_id_sru_query(id, Steps.ISSN) and known_element.query != "":
                return known_element
        # ISBN
        elif step == Steps.ISBN:
            if known_element.isbn == id:
                return known_element
            elif known_element.normalized_isbn == normalize_intnat_id(id, Steps.ISBN):
                return known_element
            elif known_element.query == generate_intnat_id_sru_query(id, Steps.ISBN) and known_element.query != "":
                return known_element

    return None

def get_manual_check_known_elements() -> List[Known_Element]:
    """Returns all knwonw elements using manual checks"""
    return MANUAL_CHECKS_KNOWN_LIST

# ---------- Preparing Main ----------
MARC_READER = pymarc.MARCReader(open(RECORDS_FILE_PATH, 'rb'), to_unicode=True, force_utf8=True) # DON'T FORGET ME
MARC_WRITER = open(FILE_OUT, "wb") # DON'T FORGET ME
# ----- Load manual checks -----
with open(MANUAL_CHECKS_FILE, mode="r+", encoding="utf-8") as f:
    root = ET.fromstring(f.read())
    for xml_check in root.findall("check"):
        check = Manual_Check(xml_check)
        sru_request = [ksru.Part_Of_Query(ksru.SRU_Indexes.BIBLIONUMBER, ksru.SRU_Relations.EQUALS, check.bibnb)]
        query = sru.generate_query(sru_request)
        res = sru.search(
                    query,
                    record_schema=ksru.SRU_Record_Schemas.MARCXML,
                    start_record=1,
                    maximum_records=10
                )
        if (res.status == "Error"):
            ERR_MAN.trigger_error(-1, "Ø", Errors.MANUAL_CHECK_SRU, "Error occured during SRU request for a manual check", res.get_error_msg())
            continue
        # Adds to the known list if at least a result returned
        if len(res.get_records()) > 0:
            add_manual_check_known_element(Known_Element(Steps.ISSN, query, generate_4XX_subfields(res.get_records()[0]), manual_check=check))

# ---------- Main ----------
# Loop through records
for record_index, record in enumerate(MARC_READER):
    # If record is invalid
    if record is None:
        ERR_MAN.trigger_error(record_index, "", Errors.CHUNK_ERROR, "", "")
        continue # Fatal error, skipp

    # Gets the record ID
    record_id = record.get("001")
    if not record_id:
        # if no 001, check 035
        if not record.get("035"):
            ERR_MAN.trigger_error(record_index, "", Errors.NO_RECORD_ID, "No 001 or 035", "")
        elif not record.get("035").get("a"):
            ERR_MAN.trigger_error(record_index, "", Errors.NO_RECORD_ID, "No 001 or 035$a", "")
        else:
            record_id = record.get("035").get("a")
    else:
        record_id = record_id.data

    for field in record.get_fields(*U4XX_list): # *[] to iterate, using just [] returns nothing
        # Manual check
        step = Steps.MANUAL_CHECK
        leave = False
        for known_element in get_manual_check_known_elements():
            if known_element.manual_check.check(field):
                field.subfields = known_element.subfields
                leave = True
                continue
        # Manual check succeeded, leave
        if leave:
            continue

        # Get first $x and treats it like an ISSN
        step = Steps.ISSN
        issn = field.get("x")
        if issn:
            # Checks if this ISSN is known
            known_element = get_known_element_by_intnat_id(issn, step)
            if known_element:
                field.subfields = known_element.subfields
                continue
            query = generate_intnat_id_sru_query(issn, step)
            if query != "":
                res = sru.search(
                    query,
                    record_schema=ksru.SRU_Record_Schemas.MARCXML,
                    start_record=1,
                    maximum_records=10
                )
                if (res.status == "Error"):
                    ERR_MAN.trigger_error(record_index, record_id, Errors.SRU_ERROR, "Error occured during SRU request on ISSN", res.get_error_msg())
                    continue
                
                if len(res.get_records_id()) > 1:
                    # Informative error, we use 1st record if the query is ISSN
                    ERR_MAN.trigger_error(record_index, record_id, Errors.SRU_MULTIPLE_MATCHES, "SRU returned multiple matches for this ISSN", f"ISSN {issn} : {','.join(res.get_records_id())}")
                
                if len(res.get_records()) > 0: # Not a elif, we want to call it even with multiple matyched records
                    new_known_element = Known_Element(step, query, generate_4XX_subfields(res.get_records()[0]), issn=issn)
                    add_known_element(new_known_element)
                    # Change 463 only if there's a link
                    if new_known_element.has_link:
                        field.subfields = new_known_element.subfields
                    
                    continue
        
        # If no ISSN, check for ISBN
        # Get first $y and treats it like an ISBN
        step = Steps.ISBN
        isbn = field.get("y")
        if isbn:
            # Checks if this ISBN is known
            known_element = get_known_element_by_intnat_id(isbn, step)
            if known_element:
                field.subfields = known_element.subfields
                continue
            query = generate_intnat_id_sru_query(isbn, step)
            if query != "":
                res = sru.search(
                    query,
                    record_schema=ksru.SRU_Record_Schemas.MARCXML,
                    start_record=1,
                    maximum_records=10
                )
                if (res.status == "Error"):
                    ERR_MAN.trigger_error(record_index, record_id, Errors.SRU_ERROR, "Error occured during SRU request on ISBN", res.get_error_msg())
                    continue
                
                if len(res.get_records_id()) > 1:
                    # Informative error, we use 1st record if the query is ISSN
                    ERR_MAN.trigger_error(record_index, record_id, Errors.SRU_MULTIPLE_MATCHES, "SRU returned multiple matches for this ISBN", f"ISBN {isbn} : {','.join(res.get_records_id())}")
                
                if len(res.get_records()) > 0: # Not a elif, we want to call it even with multiple matyched records
                    new_known_element = Known_Element(step, query, generate_4XX_subfields(res.get_records()[0]), isbn=isbn)
                    add_known_element(new_known_element)
                    # Change 463 only if there's a link
                    if new_known_element.has_link:
                        field.subfields = new_known_element.subfields
                    
                    continue

    # Writes the record
    MARC_WRITER.write(record.as_marc())

MARC_READER.close()
MARC_WRITER.close()
ERR_MAN.close()