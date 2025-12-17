# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.2.0] - 2025-12-17

### Added

* Environment variable `KEEP_V` can now be set to `1` to keep currently defined `$v` and remove new `$v` (only if a `$v` was already defined)

### Changed

* Known elements now also includes elements returning no results from the SRU to avoid useless SRU queries
* Rewrote the parts querying the SRU to reduce redundancy

### Fixed

* Now has better detection if a known element has a link
* SRU requests triggering an error no longer prevents next steps to properly execute
* Manual check known elements now have the correct step assigned
* Fixed test plan incorrectly testing erroneous ISBN

## [1.1.0] - 2025-03-14

### Added

* If a `$9` exists in the field, queries the SRU for this biblionumber before querying ISSN & ISBN

### Changed

* Now uses pymarc 5 instead of 4

### Fixed

* Updated Koha SRU connector to fix generic errors not working as intended

## [1.0.0] - 2024-07-25

Original release
