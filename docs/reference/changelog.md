# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CONTRIBUTING.md with development guidelines and PR process
- SECURITY.md with vulnerability reporting policy
- CODE_OF_CONDUCT.md for community standards
- This CHANGELOG.md following Keep a Changelog format

### Changed
- Documentation improvements to remove condescending language and improve clarity

## [1.0.0] - 2025-11-28

### Added
- mDNS-based peer discovery via Zeroconf
- Direct TCP connections between peers
- Gossip protocol for message routing and propagation
- Multi-channel chat system with public and private channels
- End-to-end encryption for private channels using AES-256-GCM
- X25519 key exchange for secure channel key distribution
- Ed25519 digital signatures for message authentication
- SQLite database for message persistence
- Advanced terminal UI built with Textual framework
- Export/import functionality for message backup and migration
- `/create`, `/join`, `/leave`, `/switch` channel management commands
- `/invite` command for private channel member management
- `/export` and `/import` commands for data portability
- `/peers` command to show connected nodes
- Comprehensive test suite with 97 tests and 100% coverage
- Complete documentation including User Guide, Deployment Guide, and Architecture reference
- Automatic installation script (`install.sh`)
- Uninstallation script (`uninstall.sh`)
- systemd service file for Linux deployments
- Docker deployment support

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- AES-256-GCM authenticated encryption for private channels
- Ed25519 cryptographic signatures on all messages
- X25519 elliptic curve key exchange
- Secure random key generation using NaCl

## Version History

[Unreleased]: https://github.com/fabriziosalmi/tad/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/fabriziosalmi/tad/releases/tag/v1.0.0
