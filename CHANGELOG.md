# Changelog

Changelog for eol_scons

## [Unreleased]

Nothing.

## [0.1] - 2022-08-02 - ACCLIP FF02 TEST

This version of the software was flown for ACCIP FF02 leg 2 from Sacramento to
Kona as a first test under flight conditions.
### Added

- Jenkins configuration is saved to a `jenkinsfile`

- Document configuration directory layout and sample YAML `config file`

- Deploy conda runtime environment via `mtpenv.yml` file

- `mtudpd` now has an option to send to RIC

- A suite of scripts to run the MTP manually for testing

- Initialize the IWG section of the MTP dictionary using the variable list
provided in the ascii_parms file.

- This version has a start to unit tests for the control software

### Changed

- Fully refactored and updated `MTPcontrol` program

- Updated deprecated `Oxygen frequencies` to be accuratea

- Fixed pointing calculations

- Code now handles varying numbers of flight levels in the RCF file
programmatically.

### Removed

- Unused files have been removed

## [1ba299d] - 2022-03-15

- first tagged release

<!-- Versions -->
[unreleased]: https://github.com/NCAR/MTP/compare/V0.1-ACCLIPff02...HEAD
[0.1]: https://github.com/NCAR/MTP/compare/pre-tig3er...V0.1-ACCLIPff02
[1ba299d]: https://github.com/NCAR/MTP/releases/tag/pre-tig3er
