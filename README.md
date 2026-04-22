# NetBox FolderView

A NetBox plugin that provides a folder-tree view of IP prefixes, similar to the experience offered by SolarWinds IPAM or phpIPAM. Browse your prefix hierarchy visually, drill into assigned IP addresses, and filter the tree using NetBox's native filter and saved-filter system — all without leaving the familiar NetBox UI.

---

## Compatible NetBox Versions

| Plugin Version | NetBox Version |
|---------------|----------------|
| 0.1.x         | 4.5.x+         |

> **Note:** This plugin relies on internal NetBox APIs (`restrict()`, `UserConfig`, `PrefixFilterSet`, `SavedFilter`). Compatibility with versions below 4.5.0 is not guaranteed.

---

## Features

- **Two-pane tree view** — prefix hierarchy on the left, IP addresses on the right
- **Lazy loading** — child prefixes and IP addresses are fetched on demand; no performance penalty on large datasets
- **Filter-aware tree** — apply any NetBox prefix filter and the tree reorganizes to show only matching prefixes; filtered-out parent prefixes are skipped and their children become root nodes automatically
- **Saved filters** — the saved filter dropdown from the standard Prefixes view is available directly in the tree header
- **Column configuration** — right-pane IP table columns are configurable per-user, persisted via NetBox's native `UserConfig` mechanism
- **Respects NetBox RBAC** — all queries are restricted to the authenticated user's object-level permissions
- **Read-only** — no create, edit, or delete actions; purely a visualization layer over existing data

---

## Installation

### 1. Install the package

Install into the same Python environment as NetBox.

**From PyPI** *(once published)*:
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

### 3. Restart NetBox

No database migrations are required — the plugin is stateless.

```bash
# Example for a systemd-managed installation
sudo systemctl restart netbox netbox-rq
```

---

## How to Use

### Navigating to the Prefix Tree

After installation, a **FolderView** section appears in the NetBox left-hand navigation menu. Click **Prefix Tree** to open the view.

### The Tree Tab

The main view is split into two panes:

**Left pane — Prefix Tree**
- Displays your prefix hierarchy as a collapsible folder tree
- Top-level prefixes (those with no parent prefix) appear as root nodes; aggregates are excluded
- Click the **chevron** (▶) beside a prefix to expand it and reveal child prefixes
- **Single-click** a prefix to load its assigned IP addresses in the right pane
- **Double-click** a prefix to navigate to its full NetBox detail page

**Right pane — IP Addresses**
- Displays the IP addresses assigned within the selected prefix
- Paginated using NetBox's standard pagination controls
- **Double-click** any IP address to navigate to its NetBox detail page
- Click **Configure** to choose which columns are shown; your preferences are saved per-user

### Filtering the Tree

Use the controls at the top of the Tree tab to narrow what appears:

- **Quick search** — type to filter the visible tree by prefix or description
- **Saved filter dropdown** — apply any saved filter you've created on the standard Prefixes page
- **Filters tab** — switch to the Filters tab for the full NetBox prefix filter panel (VRF, tenant, site, role, status, and more); click **Search** to apply; the tree reorganizes to show only matching results

When filters are active, a summary of applied filters appears above the tree. Click the **Reset** button on the Filters tab to clear all filters.

---

## Development

To run against a local NetBox instance:

```bash
# Clone and install in editable mode
git clone https://github.com/averyhabbott/netbox-folderview.git
pip install -e ./netbox-folderview

# Add to your NetBox configuration.py (see Installation above)

# Start the NetBox dev server (no migrations needed)
cd netbox
python manage.py runserver
```

---

## License

MIT
