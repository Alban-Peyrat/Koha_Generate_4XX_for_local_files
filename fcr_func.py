# -*- coding: utf-8 -*- 

# External imports
import re
from unidecode import unidecode

# ---------- Start of old prep_data ----------

def prep_string(_str:str, _noise = True, _multiplespaces = True) -> str:
    """Returns a string without punctuation and/or multispaces stripped and in lower case.

    Takes as arguments :
        - _str : the string to edit
        - _noise [optional] {bool} : remove punctuation ?
        - _multispaces [optional] {bool} : remove multispaces ?
    """
    # remove noise (punctuation) if asked (by default yes)
    if _noise:
        _str = re.sub(r"[\x21-\x2F]|[\x3A-\x40]|[\x5B-\x60]|[\x7B-\x7F]|[\u2010-\u2015]|\.|\,|\?|\!|\;|\/|\:|\=|\[|\]|\'|\-|\(|\)|\||\"|\<|\>|\+|\°", " ", _str, flags=re.IGNORECASE)
    # replace multiple spaces by ine in string if requested (default yes)
    if _multiplespaces:
        _str = re.sub("\s+", " ", _str).strip()
    return _str.strip().lower()

def nettoie_titre(titre:str) -> str:
    """Supprime les espaces, la ponctuation et les diacritiques transforme "&" en "et" et renvoie le résultat en minuscule.

    Args:
        titre (string): une chaîne de caractères
    """
    if titre is not None :
        titre_norm = prep_string(titre)
        titre_norm = titre_norm.replace('&', 'et')
        titre_norm = titre_norm.replace('œ', 'oe')
        # out = re.sub(r'[^\w]','',unidecode(titre_norm))
        out = unidecode(titre_norm)
        return out.lower()
    else :
        return titre

def clean_publisher(pub:str) -> str:
    """Deletes from the publisher name a list of words and returns the result as a string.

    Takes as an argument the publisher name as a string."""
    if pub is not None :
        pub_noise_list = ["les editions", "les ed.", "les ed", "editions", "edition", "ed."] # this WILL probably delete too much things but we take the risk
        # pas "ed" parce que c'est vraiment trop commun
        pub_norm = prep_string(pub, _noise=False) # We keep punctuation for the time being
        pub_norm = pub_norm.lower()
        pub_norm = pub_norm.replace('&', 'et')
        pub_norm = pub_norm.replace('œ', 'oe')
        pub_norm = unidecode(pub_norm)
        
        for car in pub_noise_list:
            pub_norm = pub_norm.replace(car, " ")
        
        return prep_string(pub_norm) # we don't need punctuation anymore
    else :
        return pub

def get_year(txt:str) -> str:
    """Returns all 4 consecutive digits included in the string as a list of strings.
    
    Takes as an argument a string."""
    return re.findall("\d{4}", txt)

# ---------- End of old prep_data ----------

def delete_control_char(txt: str) -> str:
    """Returns the string without control characters"""
    # https://pythonguides.com/remove-unicode-characters-in-python/
    # https://stackoverflow.com/questions/5028717/matching-unicode-characters-in-python-regular-expressions
    # This hits to wide .encode("ascii", "ignore").decode()
    # Delete backslashes in case some of them are escaped
    # Control characters : (https://www.compart.com/en/unicode/category/Cc)
    # \x00-\x1F : ASCII control characters
    # \x7F-\x9F : other control characters
    # Format characters : (https://www.compart.com/en/unicode/category/Cf)
    # Single characters : \xAD \u061C \u06DD \u070F \u08E2 \u180E \uFEFF \u110BD \u110CD \uE0001
    # Ranges : \u0600-\u0605 \u200B-\u200F \u202A-\u202E \u2060-\u206F \uFFF9-\uFFFB ~~\u13430-\u13438~~
    # ~~\u1BCA0-\u1BCA3 \u1D173-\u1D17A \uE0020-\uE007F~~
    return re.sub(r"[\x00-\x1F|\x7F-\x9F|\xAD|\u0600-\u0605|\u061C|\u06DD|\u070F|\u08E2|\u180E|\u200B-\u200F|\u202A-\u202E|\u2060-\u206F|\uFEFF|\uFFF9-\uFFFB|\\]", " ", str(txt), re.UNICODE)

def list_as_string(this_list: list) -> str:
    """Returns the list as a string :
        - "" if the lsit is empty
        - the first element as a string if there's only one element
        - if after removing empty elements there is only one element, thsi element as a string
        - the lsit a string if there are multiple elements.
    Takes as argument a list"""
    if len(this_list) == 0:
        return ""
    elif len(this_list) == 1:
        return delete_control_char(str(this_list[0]))
    else:
        if type(this_list) != list:
            return delete_control_char(str(this_list))
        non_empty_elements = []
        for elem in this_list:
            if elem:
                non_empty_elements.append(elem)
        if len(non_empty_elements) == 0:
            return ""
        elif len(non_empty_elements) == 1:
            return delete_control_char(str(non_empty_elements[0]))
        else:
            return delete_control_char(str(", ".join([str(elem) for elem in non_empty_elements])))

def delete_CBS_boolean_operators(txt:str) -> str:
    """Deletes all CBS boolean operators (AND, OR, NOT) in eevry language and return the resukt as a string
    Based on "All CBS Command" Version 6 (2014-02-11)"""
    txt = re.sub(r"\b(AND|EN|UND|ET|VE|NOT|NIET|NICHT|NON|DEGIL|SAUF|OR|OF|ORDER|OU|VEYA)\b", "", txt, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", txt)

def delete_Sudoc_empty_words(txt:str) -> str:
    """Deletes all Sudoc empty keywords (index TOUT) to simplify the query"""
    txt = re.sub(r"\b(A|BIS|DI|IL|OF|THE|AB|BY|DIE|IM|ON|THEIR|ABOUT|C|DONT|IMPR|OU|THIS|ACCORDING|CE|DR|IN|OVER|TO|ACROSS|CETTE|DU|INTO|P|UEBER|AD|CEUX|DURANT|E|PAR|UM|AGAINST|CHEZ|DURANTE|ITS|PER|UND|AINSI|CO|DURCH|J|PLUS|UNDER|AL|COMME|DURING|L|POR|UNE|ALL|COMO|E|LA|POUR|UNLESS|ALLA|CUM|ED|LAS|QU|UNTER|ALLE|D|EIN|LE|QUAE|UPON|ALS|DAL|EINE|LES|QUE|VOM|ALSO|DALL|EINEM|LEUR|R|VON|ALTRE|DALLA|EINER|LEURS|S|VOR|AM|DANS|EINES|LO|SANS|VOS|AMONG|DAS|EL|LOS|SE|VOTRE|AN|DE|EN|M|SELON|VOUS|AND|DEGLI|ES|MES|SES|W|ASI|DEL|ET|MIT|SIC|WAS|AT|DELL|F|N|SINCE|WE|ATQUE|DELLA|FOR|NACH|SIVE|WHITCH|AU|DELLE|FROM|NE|SN|WITH|AUF|DELLO|FUER|NEAR|SO|Y|AUPRES|DEM|G|NEL|SOME|ZU|AUS|DEN|GLI|NO|SOUS|ZUR|AUSSI|DEPUIS|H|NOS|ST|AUX|DER|HIS|NOTRE|SUL|AVEC|DEREN|I|NOUS|SUR|B|DES|IHRE|O|TE|BEI|DESDE|IHRER|ODER|THAT|UN|COLLECTIF|COLLECTIFS)\b", "", txt, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", txt)

def delete_for_sudoc(txt:str) -> str:
    """Merges deletion func specifics for CBs and Sudoc"""
    return delete_suspicious_looking_words(delete_duplicate_words(delete_Sudoc_empty_words(delete_CBS_boolean_operators(txt))))

def delete_duplicate_words(txt:str) -> str:
    """Returns the strig withotu duplicates BUT DOES NOT KEEP  THE WORD ORDER"""
    unique_words = set()
    for word in txt.split():
        if word not in unique_words:
            unique_words.add(word)
    return " ".join(unique_words)

def delete_suspicious_looking_words(txt:str) -> str:
    """Returns the string without words not starting with a letter or a number"""
    output = []
    for word in txt.split():
        if re.match(r"^[a-zA-Z\d]", word):
            output.append(word)
    return " ".join(output)