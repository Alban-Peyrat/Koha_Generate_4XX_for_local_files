# Generate Koha fields 4XX in local files based on the field content

[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)

This application is used to build UNIMARC `4XX` fields for local MARC records based on Koha database.
This is based on [the value builder `unimarc_field_4XX.pl` (master branch, 2024-04-08)](https://github.com/Koha-Community/Koha/blob/a64383de16c8d79e44c297ad8da860b536d91597/cataloguing/value_builder/unimarc_field_4XX.pl).

__Developped for `pymarc 5.2.0`__  _(previously developped with `pymarc 4.2.2.`, should be up to date)_

This script was created mainly to link articles to their periodical, it might not work the best / correcty for other cases.

## Setting up

Set up the following environment variables :

* `RECORDS_FILE` : full path to the file contining all the records to edit
* `FILE_OUT` : full path to thhe file that will contain all records edited
* `ERRORS_FILE`: full path to the file with errors (will be created / rewrite existing one)
* `MANUAL_CHECKS_FILE` : full path to the [manual checks XML file](#manual-check-file)
* `KOHA_URL` : your Koha OPAC URL for the SRU
* `IGNORE_FIELDS` : list of UNIMARC fields to ignore in the `4XX` range, separated by commas

### Manual check file

[A default manual checks XML is provided with a generic value](./manual_checks.xml), the root must be `fields`, then it should always follow these conditions :

* `checks` root :
  * Does not use any attributes
  * Contains `check` nodes
* `check` nodes :
  * Must have an attribute `bibnb`, which is the biblionumber for the target record
  * Contains `subfield` nodes
* `subfield` nodes :
  * Must have an attribute `code`
  * Can have an attribute `normalised` :
    * If equal to `1`, the value will be normalised in upper case after using `unidecode.unidecode()`
    * If omitted or any other value, the value won't be normalised
    * Must contain some text, which is the value checked
  * __A check can only check for a subfield code once__ (you can't check twice on `$t` for example)

## Processing

The script will check, for each field, with the following order :

1. If the field matches one of the manual checks
2. If the field has a linked biblionumber (`$9`), it will search with Koha SRU for records
2. If the field has an ISSN (`$x`), it will search with Koha SRU for records
3. If the field has an ISBN (`$y`), it will search with Koha SRU for records

If a field matches a linked biblionumber, an ISSN or an ISBN, the script will store for this execution the matching record, to minimze requests to the SRU on known elements.