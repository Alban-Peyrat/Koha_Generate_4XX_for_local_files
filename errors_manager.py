# -*- coding: utf-8 -*- 

# external imports
from enum import Enum
import csv

class Error_File_Headers(Enum):
        INDEX = "index"
        ID = "id"
        ERROR = "error"
        TXT = "error_message"
        DATA = "data"

class Errors(Enum):
    CHUNK_ERROR = 0
    NO_RECORD_ID = 1
    MANUAL_CHECK_SRU = 2
    
    # Analysis errors
    SRU_ERROR = 100
    SRU_MULTIPLE_MATCHES = 101


class Errors_Manager(object):
    def __init__(self, file_path:str) -> None:
        self.file = open(file_path, "w", newline="", encoding='utf-8')
        self.headers = []
        for member in Error_File_Headers:
            self.headers.append(member.value)
        self.writer = csv.DictWriter(self.file, extrasaction="ignore", fieldnames=self.headers, delimiter=";")
        self.writer.writeheader()

    def close(self):
        self.file.close()

    def trigger_error(self, index:int, id:str, error:Errors, txt:str, data:str):
        """Trigger an error.
        Takes as argument :
            - index {int} : record index, negative value means skipped
            - id {str} : record ID
            - error {Errors} : Error type
            - txt {str} : Error message
            - data {str} : additionnal information (ex : data that trigger the error)"""
        if index < 0:
            index = "Ø"
        self.writer.writerow(
            {
                Error_File_Headers.INDEX.value:index,
                Error_File_Headers.ID.value:id,
                Error_File_Headers.ERROR.value:error.name,
                Error_File_Headers.TXT.value:txt,
                Error_File_Headers.DATA.value:data
            }
        )
