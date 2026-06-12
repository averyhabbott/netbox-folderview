# Changelog

## [0.3.0] — 2026-06-12

### Added

- **REST API** for Catalog and Folder (`/api/plugins/folderview/catalogs/`, `/api/plugins/folderview/folders/`): list / retrieve / create / update / delete with token authentication, pagination, and filtering (`name`, `object_type`, `catalog`, `folder_type`).
- **Comprehensive test suite** — models, views, REST API, filtersets, dynamic object-type resolution, and plugin config. Validated on NetBox 4.6.2.

### Fixed

- Deleting a Catalog or Folder raised HTTP 500 (`SerializerNotFound`) on NetBox 4.6. NetBox 4.6's event pipeline serializes change-logged objects through their REST API serializer; the new serializers satisfy that path.

### Changed

- Validated against NetBox 4.6.x; `max_version` is `4.6.999`.
- License changed from MIT to **GPL-3.0-or-later** (full text now shipped in `LICENSE`).

---

## [0.2.1] — 2026-05-19

### Fixed

- Resolved "Your models in app(s): 'netbox_folderview' have changes that are not yet reflected in a migration" warning emitted by `manage.py migrate` after installing 0.2.0. Adds `0002_field_metadata` migration to align field `verbose_name` / `help_text` and switches `FolderMembership` to a `UniqueConstraint` (matches the shipped initial migration). No schema changes.

---

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
