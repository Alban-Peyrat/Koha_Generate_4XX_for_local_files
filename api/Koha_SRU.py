# -*- coding: utf-8 -*- 

# external imports
from enum import Enum
import logging
import requests
import xml.etree.ElementTree as ET
import urllib.parse

#https://koha-community.org/manual/20.11/fr/html/webservices.html#sru-server
# https://www.loc.gov/standards/sru/sru-1-1.html
# https://www.loc.gov/standards/sru/cql/contextSets/cql-context-set-v1-2.html

# See README.md for more informations

# --------------- Enums ---------------

XML_NS = {
    "zs2.0": "http://docs.oasis-open.org/ns/search-ws/sruResponse",
    "zs1.1": "http://www.loc.gov/zing/srw/",
    "zs1.2": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim"
    }

class SRU_Version(Enum):
    V1_1 = "1.1"
    V1_2 = "1.2"
    V2_0 = "2.0"

class SRU_Operations(Enum):
    # SCAN = "scan"  # Not supported (my instance ?)
    EXPLAIN = "explain"
    SEARCH = "searchRetrieve"

class SRU_Record_Schemas(Enum):
    MARCXML = "marcxml"
    # UNIMARC = "unimarc"
    # MARC21 = "marc21"

class SRU_Indexes(Enum):
    CQL_SERVERCHOICE = "cql.serverChoice"
    ANY = "cql.serverChoice"
    BIB1_1016 = "cql.serverChoice"
    DC_ANY = "dc.any"
    BIBLIONUMBER = "rec.id"
    REC_ID = "rec.id"
    BIB1_12 = "rec.id"
    KOHA_LOCAL_NUMBER = "rec.id"
    IDENTIFIER = "dc.identifier"
    DC_IDENTIFIER = "dc.identifier"
    BIB1_1007 = "dc.identifier"
    KOHA_IDENTIFIER_STANDART = "dc.identifier"
    TITLE = "dc.title"
    DC_TITLE = "dc.title"
    BIB1_4 = "dc.title"
    KOHA_TITLE = "dc.title"
    SUBJECT = "dc.subject"
    DC_SUBJECT = "dc.subject"
    BIB1_21 = "dc.subject"
    KOHA_SUBJECT = "dc.subject"
    DC_CREATOR = "dc.creator"
    AUTHOR = "dc.author"
    DC_AUTHOR = "dc.author"
    BIB1_1003 = "dc.author"
    KOHA_AUTHOR = "dc.author"
    ITEMTYPE = "dc.itemtype"
    DC_ITEMTYPE = "dc.itemtype"
    BIB1_1031 = "dc.itemtype"
    KOHA_ITYPE = "dc.itemtype"
    BARCODE = "dc.barcode"
    DC_BARCODE = "dc.barcode"
    BIB1_1028 = "dc.barcode"
    KOHA_BARCODE = "dc.barcode"
    SET_IDENTIFIER = "dc.branch"
    DC_BRANCH = "dc.branch"
    BIB1_1033 = "dc.branch"
    KOHA_HOST_ITEM_NUMBER = "dc.branch"
    ISBN = "dc.isbn"
    DC_ISBN = "dc.isbn"
    BIB1_7 = "dc.isbn"
    KOHA_ISBN = "dc.isbn"
    ISSN = "dc.issn"
    DC_ISSN = "dc.issn"
    BIB1_8 = "dc.issn"
    KOHA_ISSN = "dc.issn"
    # "dc.any" / BIB1_1016 UNUSED
    # "dc.note" / BIB1_63 UNUSED
    DC_PNAME = "dc.pname"
    BIB1_1 = "dc.pname"
    # "dc.editor" / BIB1_1020 UNUSED
    PUBLISHER = "dc.publisher"
    DC_PUBLISHER = "dc.publisher"
    BIB1_1018 = "dc.publisher"
    KOHA_PUBLISHER = "dc.publisher"
    # "dc.description" / BIB1_62 UNUSED
    DATE = "dc.date"
    DC_DATE = "dc.date"
    BIB1_30 = "dc.date"
    KOHA_ACQDATE = "dc.date"
    KOHA_COPYDATE = "dc.date"
    KOHA_PUBDATE = "dc.date"
    DC_RESOURCETYPE = "dc.resourceType"
    # "dc.format" / BIB1_1034 UNUSED
    DC_RESOURCEIDENTIFIER = "dc.resourceIdentifier"
    # DC_SOURCE = "dc.source" COMMENTED    
    # BIB1_1019 = "dc.source" COMMENTED    
    # KOHA_RECORD_SOURCE = "dc.source" COMMENTED    
    # "dc.language" / BIB1_54 UNUSED
    # "dc.Place-publication" / BIB1_59 UNUSED
    # "dc.relation" COMMENTED
    # "dc.coverage" COMMENTED
    # "dc.rights" COMMENTED
    # "bath.keyTitle" / BIB1_33 UNUSED
    # "bath.possessingInstitution" / BIB1_1044 UNUSED
    # "bath.name" / BIB1_1002 UNUSED
    BATH_PERSONALNAME = "bath.personalName"
    BATH_CORPORATENAME = "bath.corporateName"
    BIB1_2 = "bath.corporateName"
    BATH_CONFERENCENAME = "bath.conferenceName"
    BIB1_3 = "bath.conferenceName"
    # "bath.uniformTitle" / BIB1_6 UNUSED
    BATH_ISBN = "bath.isbn"
    BATH_ISSN = "bath.issn"
    # "bath.geographicName" / BIB1_58 UNUSED
    # "bath.notes" / BIB1_63 UNUSED
    # "bath.topicalSubject" / BIB1_1079 UNUSED
    # "bath.genreForm" / BIB1_1075 UNUSED

class Status(Enum):
    ERROR = "Error"
    SUCCESS = "Success"

class Errors(Enum):
    HTTP_ERROR = "Service unavailable"
    GENERIC = "Generic exception, read logs for more information"

class SRU_Relations(Enum):
    EQUALS = "="
    EXACT = " exact "
    ANY = " any "
    ALL = " all "
    STRITCLY_INFERIOR = "<"
    STRITCLY_SUPERIOR = ">"
    INFERIOR_OR_EQUAL = "<="
    SUPERIOR_OR_EQUAL = ">="
    NOT = " not "

class SRU_Boolean_Operators(Enum):
    AND = " and "
    OR = " or "
    NOT = " not "

# --------------- Class Objects ---------------

# ---------- SRU Query ----------

class Part_Of_Query(object):
    """Part_Of_Query
    =======
    Generate a Part_Of_Query that can be used in Sudoc_SRU.generate_query() or Sudoc_SRU.generate_scan_clause().
    On init, takes as argument (must provide the right data type) :
        - index {SRU_Indexes or SRU_Filters} : the index to use
        - relation {SRU_Relations} : the relation to use
        - value {str, int, SRU_Filter_TDO, SRU_Filter_LAN or SRU_Filter_PAY} : the value to search in the index
        - [optional] bool_operator {SRU_Boolean_Operators} : the boolean operator to use, defauts to AND"""
    
    def __init__(self, index: SRU_Indexes, relation: SRU_Relations, value: str | int, bool_operator=SRU_Boolean_Operators.AND):
        self.bool_operator = bool_operator
        self.index = index
        self.relation = relation
        self.value = value 
        self.invalid = False
        if (
                type(self.bool_operator) != SRU_Boolean_Operators
                or type(self.relation) != SRU_Relations
            ):
            self.invalid = True
        if type(self.index) != SRU_Indexes:
            self.invalid = True
        
        # Calculated infos
        self.as_string_with_operator = self.to_string(True)
        self.as_string_without_operator = self.to_string(False)

    def to_string(self, include_operator=True):
        """Returns the Part_Of_Query as a string.
        Takes as parameter :
            - [optional] incule_operator {bool} : include the operator in the output. Defaults to True"""
        if not include_operator:
            return f"{self.index.value}{self.relation.value}{self.value}"
        else:
            return f"{self.bool_operator.value}{self.index.value}{self.relation.value}{self.value}"
        
# ---------- SRU ----------

class Koha_SRU(object):
    """Koha_SRU
    =======
    A set of function to query Koha SRU
    On init take as arguments :
        - Koha server URL
        - the version (defaults to 2.0)
        - [optional] service {str} : Name of the service for the logs"""
    def __init__(self, url:str, version:SRU_Version.V1_1, service="Koha_SRU"):
        # Const
        if url[-1:] in ["/", "\\"]:
            url = url[:len(url)-1]
        self.endpoint = url + "/biblios"
        # Control provided version and set it to its string form
        if type(version) == SRU_Version:
            self.version = version.value
        elif version not in [e.value for e in SRU_Version]:
                self.version = SRU_Version.V2_0.value
        else:
            self.version = version
        # logs
        self.logger = logging.getLogger(service)
        self.service = service

    def explain(self):
        """GET an explain request from the SRU and returns a SRU_Result_Explain instance"""

        url = f'{self.endpoint}?operation={SRU_Operations.EXPLAIN.value}&version={self.version}'
        status = None
        error_msg = None
        result = ""

        # Request
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            status = Status.ERROR
            error_msg = Errors.HTTP_ERROR
            self.logger.error(f"Explain :: Koha_SRU Explain :: HTTP Status: {r.status_code} || Method: {r.request.method} || URL: {r.url} || Response: {r.text}")
        except requests.exceptions.RequestException as generic_error:
            status = Status.ERROR
            error_msg = Errors.GENERIC
            self.logger.error(f"Explain :: Koha_SRU Explain :: Generic exception || URL: {url} || {generic_error}")
        else:
            status = Status.SUCCESS
            self.logger.debug(f"Explain :: Koha_SRU Explain :: Success")
            result = r.content.decode('utf-8')
        
        return SRU_Result_Explain(status, error_msg, result, url)

    # Not supported (my instance ?)
    # def scan(self, scan_clause: str, maximum_terms=25, response_position=1):
    #     """GET a scan request from the SRU and returns a SRU_Result_Scan instance
    #     Takes as arguments :
    #         - scan_clause {str} : the query
    #         - [optional] maximum_terms {int} : the number of returned terms (between 1 and 1000)
    #         - [optional] response_position {int} : the position of the scanned term in the returned list (> 0)"""
        
    #     # Query part
    #     scan_clause = urllib.parse.quote(scan_clause)

    #     # Checks some input values validity
    #     maximum_terms = self.to_int(maximum_terms)
    #     if not maximum_terms:
    #         maximum_terms = 25
    #     elif maximum_terms > 1001:
    #         maximum_terms = 1000
    #     elif maximum_terms < 1:
    #         maximum_terms = 10
    #     response_position = self.to_int(response_position)
    #     if not response_position:
    #         response_position = 1
    #     elif response_position < 1:
    #         response_position = 1
    #     elif response_position > maximum_terms:
    #         response_position = maximum_terms

    #     # Defines the URL
    #     url = f'{self.endpoint}?operation={SRU_Operations.SCAN.value}&version={self.version}'\
    #         f"&responsePosition={response_position}&maximumTerms={maximum_terms}&scanClause={scan_clause}"
    #     status = None
    #     error_msg = None
    #     result = ""
        
    #     # request
    #     try:
    #         r = requests.get(url)
    #         r.raise_for_status()
    #     except requests.exceptions.HTTPError:
    #         status = Status.ERROR
    #         error_msg = Errors.HTTP_ERROR
    #         self.logger.error(f"{scan_clause} :: Sudoc_SRU Scan :: HTTP Status: {r.status_code} || Method: {r.request.method} || URL: {r.url} || Response: {r.text}")
    #     except requests.exceptions.RequestException as generic_error:
    #         status = Status.ERROR
    #         error_msg = Errors.GENERIC
    #         self.logger.error(f"{scan_clause} :: Sudoc_SRU Scan :: Generic exception || URL: {url} || {generic_error}")
    #     else:
    #         status = Status.SUCCESS
    #         self.logger.debug(f"{scan_clause} :: Sudoc_SRU Scan :: Success")
    #         result = r.content.decode('utf-8')
        
    #     print("Ara ara")
    #     return SRU_Result_Scan(status, error_msg, result,
    #             maximum_terms, response_position, scan_clause, url)

    def search(self, query:str, record_schema=SRU_Record_Schemas.MARCXML, start_record=1, maximum_records=100):
        """GET a search retrieve request from the SRU and returns a SRU_Result_Search instance
        Takes as arguments :
            - query {str} : the query
            - [optional] record_schema {SRU_Record_Schema} : the record schema
            - [optional] start_record {int} : the position of the first result in the query result list (> 0)
            - [optional] maximum_records {int} : the maximum records to be returned (between 1 and 1000)"""

        # Query part
        query = urllib.parse.quote(query)

        # Control provided record schema and set it to its string form
        if type(record_schema) == SRU_Record_Schemas:
            record_schema = record_schema.value
        elif record_schema not in [e.value for e in SRU_Record_Schemas]:
                record_schema = SRU_Record_Schemas.MARCXML.value

        # Checks some input values validity
        maximum_records = self.to_int(maximum_records)
        if not maximum_records:
            maximum_records = 100
        elif maximum_records > 1001:
            maximum_records = 1000
        elif maximum_records < 1:
            maximum_records = 10
        start_record = self.to_int(start_record)
        if not start_record:
            start_record = 1
        elif start_record < 1:
            start_record = 1

        # Defines the URL
        url = f"{self.endpoint}?version={self.version}&recordSchema={record_schema}"\
            f"&operation={SRU_Operations.SEARCH.value}&query={query}"\
                f"&startRecord={start_record}&maximumRecords={maximum_records}"                                
        status = None
        error_msg = None
        result = ""

        # Request
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            status = Status.ERROR
            error_msg = Errors.HTTP_ERROR
            self.logger.error(f"{query} :: Koha_SRU Search Retrieve :: HTTP Status: {r.status_code} || Method: {r.request.method} || URL: {r.url} || Response: {r.text}")
        except requests.exceptions.RequestException as generic_error:
            status = Status.ERROR
            error_msg = Errors.GENERIC
            self.logger.error(f"{query} :: Koha_SRU Search Retrieve :: Generic exception || URL: {url} || {generic_error}")
        else:
            status = Status.SUCCESS
            self.logger.debug(f"{query} :: Koha_SRU Search Retrieve :: Success")
            result = r.content.decode('utf-8')

        return SRU_Result_Search(status, error_msg, result,
                record_schema, self.version, maximum_records,
                start_record, query, url)

    def generate_query(self, list: list):
        """Returns a query from multiple parts of query as a string.
        Takes as arguments :
            - list {list of strings or Part_Of_Query instances} : all parts of query to merge
        Any non string or Part_Of_Query instance will be ignored
        Can be use to add parenthesis to a list of Part_Of_Query."""

        output = ""
        for index, query_part in enumerate(list):
            if type(query_part) == str:
                output += query_part
            elif type(query_part) == Part_Of_Query:
                if not query_part.invalid:
                    output += query_part.to_string(bool(index))
        return output

    def to_int(self, val):
        """Returns None if val can't be a int, else return an int"""
        try:
            int(val) # Works with 2000-2023
        except TypeError:
            return None

        return int(val)

# ---------- SRU Explain Result ----------

class SRU_Result_Explain(object):
    """SRU_Result_Explain
    =======
    A set of function to handle an explain request response from Sudoc's SRU"""

    def __init__(self, status: Status, error: Errors, result: str, url: str):
        self.operation = SRU_Operations.EXPLAIN.value
        self.url = url
        self.status = status.value
        if error:
            self.error = error.value
            return
        else:
            self.error = None
        self.result_as_string = result
        self.result = ET.fromstring(result)

    def get_result(self):
            """Return the result as an ET Element."""
            return self.result

    def get_status(self):
        """Return the init status as a string."""
        return self.status

    def get_error_msg(self):
        """Return the error message."""
        return str(self.error)
    
# ---------- SRU Scan Result ----------
# Not supported (my instance ?)
# class SRU_Result_Scan(object):
#     """SRU_Result_Scan
#     =======
#     A set of function to handle a scan request response from Sudoc's SRU"""
#     def __init__(self, status: Status, error: Errors, result: str, maximum_terms: int, response_position: int, scan_clause: str, url: str):
#         self.operation = SRU_Operations.SCAN.value
#         self.url = url
#         self.status = status.value
#         if error:
#             self.error = error.value
#             return
#         else:
#             self.error = None
#         self.result_as_string = result

#         # Generate the result property
#         self.result = ET.fromstring(result)

#         # Original query parameters
#         self.maximum_terms = maximum_terms
#         self.response_position = response_position
#         self.scan_clause = scan_clause

#         # Calculated infos
#         self.terms = self.get_terms()

#     def get_result(self):
#             """Return the result as an ET Element."""
#             return self.result

#     def get_status(self):
#         """Return the init status as a string."""
#         return self.status

#     def get_error_msg(self):
#         """Return the error message."""
#         return str(self.error)

#     def get_terms(self):
#         """Returns a list of all terms as SRU_Scanned_Term"""
#         output = []
#         for term_container in self.result.findall(".//srw:terms/srw:term", XML_NS):
#             term = term_container.find("srw:displayTerm", XML_NS).text
#             nb_records = term_container.find("srw:numberOfRecords", XML_NS).text
#             extra_term_data = term_container.find("srw:extraTermData", XML_NS).text
#             value = term_container.find("srw:value", XML_NS).text
#             output.append(SRU_Scanned_Term(term, value, nb_records, extra_term_data))
#         return output
    
# # ----- SRU Explain sub-classes -----
# class SRU_Scanned_Term(object):
#     """SRU_Scanned_Term
#     =======
#     A simple class that extracts data from XML objects"""
#     def __init__(self, term: str, value: str, nb_records: str, extra_term_data: str):
#         self.term = term
#         self.value = value
#         self.nb_records = int(nb_records)
#         self.extra_term_data = extra_term_data
#         self.as_string = self.to_string()
    
#     def to_string(self):
#         """Returns all this instance property as a string"""
#         return f"{self.term} : {self.nb_records}, "\
#                 f"value={self.value}, extra term data={self.extra_term_data}"

# ---------- SRU Search Retrieve Result ----------

class SRU_Result_Search(object):
    """SRU_Result_Search
    =======
    A set of function to handle a search retrieve request response from Sudoc's SRU"""

    closing_tags_fix = "</record></srw:recordData></srw:record>"

    def __init__(self, status: Status, error: Errors, result: str, record_schema: str, version:str, maximum_records: int, start_record: int, query: str, url: str):
        self.operation = SRU_Operations.SEARCH.value
        self.url = url
        self.status = status.value
        if error:
            self.error = error.value
            return
        else:
            self.error = None
        self.result_as_string = result
        self.result_as_parsed_xml = ET.fromstring(result)
        self.result = self.result_as_parsed_xml
        
        # Original query parameters
        self.record_schema = record_schema
        self.version = version
        self.maximum_records = maximum_records
        self.start_record = start_record
        self.query = query
        
        # Calculated infos
        self.nb_results = self.get_nb_results()
        self.records = self.get_records()
        self.records_id = self.get_records_id()

    def get_result(self):
            """Return the result as a string or ET Element depending the chosen recordPacking"""
            return self.result

    def get_status(self):
        """Return the init status as a string."""
        return self.status

    def get_error_msg(self):
        """Return the error message."""
        return str(self.error)

    def get_nb_results(self):
        """Returns the number of results as an int."""
        if self.result_as_parsed_xml.findall(f"zs{self.version}:numberOfRecords", XML_NS):
            # Abes SRU crashed FCR because numberofrecords return None
            try:
                return int(self.result_as_parsed_xml.find(f"zs{self.version}:numberOfRecords", XML_NS).text)
            except:
                return 0
        else: 
            return 0

    def get_records(self):
        """Returns all records as a list"""
        return self.result_as_parsed_xml.findall(f".//zs{self.version}:record", XML_NS)
    
    def get_records_id(self):
        """Returns all records as a list of strings"""
        records = self.get_records()
        output = []
        for record in records:
            # Controlfield 001 search
            output.append(record.find(".//marc:controlfield[@tag='001']", XML_NS).text)
        return output
