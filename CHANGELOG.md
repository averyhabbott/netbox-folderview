# Changelog

## [0.2.0] — 2026-05-06

### Added

- **Catalogs** — user-defined hierarchical folder structures for organizing any NetBox object type
  - Static folders (manual membership) and dynamic folders (resolved at runtime via a Saved Filter)
  - Supports all NetBox object types with a registered filterset — Devices, Prefixes, VLANs, Circuits, VMs, and more; automatically picks up new types without configuration changes
  - Two-pane catalog view: folder tree on the left, native NetBox object table on the right
  - Full filter and search support in the Add Objects flow
  - Bulk add, remove, and move operations
  - Duplicate detection and optional enforcement per catalog
  - Per-catalog default for "show nested objects" on new folders
  - Dynamic nav entries — each catalog appears individually in the FolderView nav section
  - Standard NetBox object-level permissions for Catalog and Folder models

### Changed

- Plugin now requires running `python manage.py migrate` after installation (models added for Catalogs)

---

## [0.1.x] — 2025

### Added

- **Prefix Tree** — collapsible two-pane hierarchy view of IP prefixes
- Lazy-loaded child prefixes and IP addresses
- Filter-aware tree that reorganizes when filters are applied
- Saved filter dropdown integration
- Per-user column configuration via NetBox `UserConfig`
