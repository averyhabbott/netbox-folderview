# NetBox FolderView

A NetBox plugin with two independent features:

- **Prefix Tree** — a collapsible folder-tree view of IP prefixes, similar to SolarWinds IPAM or phpIPAM
- **Catalogs** — user-defined hierarchical folder structures for organizing any NetBox object type

---

## Compatible NetBox Versions

| Plugin Version | NetBox Version |
| -------------- | -------------- |
| 0.1.x          | 4.5.x          |
| 0.2.x          | 4.5.x          |
| 0.3.x          | 4.5.x – 4.6.x  |

**Python:** 3.10 – 3.13 (matching the supported NetBox releases).

> **Note:** This plugin relies on internal NetBox APIs. Compatibility with versions below 4.5.0 is not guaranteed.

---

## Features

### Prefix Tree

- **Two-pane tree view** — prefix hierarchy on the left, IP addresses on the right
- **Lazy loading** — child prefixes and IP addresses are fetched on demand
- **Filter-aware tree** — apply any NetBox prefix filter and the tree reorganizes automatically
- **Saved filters** — the saved filter dropdown from the standard Prefixes view is available in the tree header
- **Column configuration** — configurable per-user, persisted via NetBox's native `UserConfig` mechanism
- **Respects NetBox RBAC** — all queries are restricted to the authenticated user's object-level permissions

### Catalogs

- **Any object type** — create catalogs for Devices, Prefixes, VLANs, Circuits, VMs, and any other NetBox type that has a registered filterset
- **Hierarchical folders** — nest folders inside folders to any depth
- **Static folders** — manually curate which objects belong in each folder
- **Dynamic folders** — reference a NetBox Saved Filter; membership is resolved at runtime, always current
- **Duplicate control** — optionally prevent an object from appearing in more than one static folder within a catalog
- **Two-pane catalog view** — folder tree on the left, filtered object table on the right with native NetBox columns, filters, and search
- **Bulk operations** — add, remove, and move objects across folders in bulk
- **Respects NetBox RBAC** — object queries are restricted to the user's existing NetBox permissions; Catalog and Folder access is governed by standard NetBox object-level permissions

---

## Installation

### 1. Install the package

**From PyPI**:

```bash
pip install netbox-folderview
```

**From source** (development):

```bash
git clone https://github.com/averyhabbott/netbox-folderview.git
cd netbox-folderview
pip install -e .
```

### 2. Add to NetBox configuration

In your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_folderview',
]

PLUGINS_CONFIG = {
    'netbox_folderview': {},
}
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Restart NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

---

## Permissions

FolderView uses NetBox's standard object-level permissions system. No special configuration is required for the Prefix Tree — it respects existing prefix permissions automatically.

For **Catalogs**, two object types appear in NetBox's permission picker: **Catalog** and **Folder**. Users need view permission on both to see a catalog and its contents. Granting only one is not sufficient.

### Recommended setup

Create a single permission entry covering both object types:

1. In NetBox, go to **Admin → Permissions → Add Permission**
2. Set a name (e.g. "View all catalogs")
3. Under **Object Types**, select both **netbox\_folderview | catalog** and **netbox\_folderview | folder**
4. Set **Actions** to `view` (add `add`, `change`, `delete` as needed)
5. Leave **Constraints** empty to grant access to all catalogs, or scope them (see below)
6. Assign the permission to the appropriate users or groups

### Scoping access to specific catalogs

To give a user access to only certain catalogs, use constraints on **separate** permission entries:

**Catalog permission** — constrains which catalogs the user can see:

```json
{"name": "My Devices Catalog"}
```

**Folder permission** — must be scoped to match:

```json
{"catalog__name": "My Devices Catalog"}
```

Without the matching Folder constraint, the user can see the catalog in the nav but none of its folders will load.

### Object permissions in the right pane

Objects displayed inside a folder are always filtered by the user's **existing NetBox permissions** for that object type. FolderView does not grant access to objects — it only organizes them. A user without `view` permission on Devices will see an empty folder even if devices are in it.

---

## How to Use

### Using the Prefix Tree

Navigate to **FolderView → Prefix Tree** in the left-hand nav.

- **Left pane** — collapsible prefix hierarchy. Click the chevron to expand/collapse. Single-click a prefix to load its IPs on the right. Double-click to navigate to the NetBox detail page.
- **Right pane** — IP addresses within the selected prefix. Double-click any row to navigate to its detail page.
- **Filtering** — use the quick search, saved filter dropdown, or the Filters tab for the full NetBox prefix filter panel.
- **Column configuration** — click **Configure** in either pane to choose which columns are shown; preferences are saved per-user.

### Using Catalogs

Navigate to **FolderView → Manage Catalogs** to create and manage catalogs, or click directly on a catalog name in the nav to open it.

#### Creating a catalog

1. Click **+ Add** on the Manage Catalogs page
2. Choose a name and **Object Type** (the type of objects this catalog will organize)
3. Set **Allow Duplicates** — when disabled, each object may only appear in one static folder within this catalog
4. Set **Default: Show Nested Objects** — controls whether new folders in this catalog show objects from all descendant folders by default

#### Creating folders

Within a catalog, click **+ Add Folder** to create a folder:

- **Parent Folder** — leave blank for a root-level folder, or select a parent to nest it
- **Folder Type** — *Static* (manual) or *Dynamic* (filter-driven)
- **Show Nested Objects** — when enabled, the folder displays objects from all descendant folders recursively
- **Saved Filter** — required for dynamic folders; only shared filters matching the catalog's object type are shown

> Dynamic folders cannot be parents of static folders.

#### Adding objects (static folders)

Click **Add Objects** in the right pane when a static folder is selected. This opens a full NetBox-native list view for the catalog's object type, with all standard filters and search. Select objects and click **Add to Folder**.

#### Moving and removing objects

Per-row and bulk actions are available in the right pane when a static folder is selected:

- **Remove** / **Remove Selected** — deletes the folder membership; the object itself is unaffected
- **Move** / **Move Selected** — moves objects to another static folder within the same catalog atomically

#### Finding duplicate objects

If a catalog has **Allow Duplicates** disabled, use the **Find Duplicate Objects** action (available in the action dropdown on the Manage Catalogs page) to see any objects that appear in more than one static folder.

---

## REST API

FolderView exposes Catalog and Folder through NetBox's standard REST API, under
the plugin's API namespace:

- `GET|POST /api/plugins/folderview/catalogs/` — list / create
- `GET|PATCH|PUT|DELETE /api/plugins/folderview/catalogs/{id}/` — retrieve / update / delete
- `GET|POST /api/plugins/folderview/folders/` — list / create
- `GET|PATCH|PUT|DELETE /api/plugins/folderview/folders/{id}/` — retrieve / update / delete

These follow the usual NetBox conventions: Bearer-token authentication, paginated
list responses, and filtering. Catalogs can be filtered by `name` and
`object_type`; folders by `name`, `catalog`, and `folder_type`.

```bash
curl -s -H "Authorization: Token $NETBOX_TOKEN" \
  "https://netbox.example.com/api/plugins/folderview/catalogs/?object_type=ipam.prefix"
```

---

## Development

```bash
git clone https://github.com/averyhabbott/netbox-folderview.git
cd netbox-folderview
pip install -e .
# Add to configuration.py, run migrate, restart NetBox
```

### Running the tests

```bash
python manage.py test netbox_folderview
```

The suite must run under a configuration that lists `netbox_folderview` in
`PLUGINS` — i.e. your normal `configuration.py`, **not**
`netbox.configuration_testing` (which resets `PLUGINS` to only the bundled dummy
plugin, so none of these tests would load). Django's test runner creates and
tears down its own throwaway `test_*` database, so it is safe to run against a
live development install.

---

## License

This project is licensed under the **GNU General Public License v3.0 or later
(GPLv3)**. See [LICENSE](LICENSE) for the full text.
