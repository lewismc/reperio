# Multi-Dataset Support

## Overview

Reperio now supports loading and visualizing multiple Nutch datasets (CrawlDB, LinkDB, HostDB) simultaneously from a single CLI command. This significantly improves the user experience by:

1. **Eliminating redundant data entry**: Data paths are specified once via CLI arguments
2. **Enabling dataset comparison**: Switch between loaded datasets interactively in the frontend
3. **Providing complete context**: Load both CrawlDB and LinkDB together to see the full picture

## Architecture Changes

### Backend (Python/FastAPI)

#### 1. Multi-Dataset Storage (`reperio/api/main.py`)

**Before:**
```python
current_graph: Optional[nx.DiGraph] = None
current_graph_builder: Optional[GraphBuilder] = None
current_metadata: Dict[str, Any] = {}
```

**After:**
```python
loaded_datasets: Dict[str, Dict[str, Any]] = {}
active_dataset: Optional[str] = None
```

Each dataset is stored with its graph, builder, and metadata:
```python
{
    "crawldb": {
        "graph": nx.DiGraph(),
        "builder": GraphBuilder(),
        "metadata": {...}
    },
    "linkdb": {
        "graph": nx.DiGraph(),
        "builder": GraphBuilder(),
        "metadata": {...}
    }
}
```

#### 2. New API Endpoints

**GET /api/datasets**
- Returns list of all loaded datasets with metadata
- Indicates which dataset is currently active

**POST /api/datasets/{dataset_name}/activate**
- Switches the active dataset
- Returns metadata about the newly activated dataset

**Enhanced GET /api/status**
- Now includes `loaded_datasets` array
- Shows `active_dataset` name

#### 3. Helper Functions

```python
def add_dataset(dataset_name, graph, builder, metadata)
def get_active_graph()
def get_active_builder()
def get_active_metadata()
```

All existing endpoints now use these helpers instead of accessing globals directly.

### CLI (`reperio/__main__.py`)

#### Before (Single Dataset):
```bash
reperio web /path/to/crawldb --type crawldb
reperio serve /path/to/crawldb --type crawldb
```

#### After (Multi-Dataset):
```bash
reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb
reperio serve --crawldb /path/to/crawldb --linkdb /path/to/linkdb --hostdb /path/to/hostdb
```

#### Changes:

1. **Replaced positional argument + `--type` flag** with optional keyword arguments:
   - `--crawldb PATH`
   - `--linkdb PATH`
   - `--hostdb PATH`

2. **Loading loop**: Each specified dataset is loaded sequentially with progress reporting

3. **Error handling**: If one dataset fails to load, others continue

4. **Validation**: At least one dataset must be specified

### Frontend (React)

#### 1. Pre-loaded Data Detection (`App.jsx`)

On mount, the app now:
1. Calls `/api/status` to check if data is already loaded by CLI
2. If data exists:
   - Skips the `DataLoader` form
   - Fetches graph data for the active dataset
   - Displays loaded datasets in header
3. If no data exists:
   - Shows the `DataLoader` form as before

```javascript
useEffect(() => {
  const checkPreloadedData = async () => {
    const status = await api.getStatus()
    if (status.graph_loaded && status.loaded_datasets.length > 0) {
      // Load active dataset's graph
      const graphData = await api.getGraphData()
      setGraphData(graphData)
    } else {
      setShowLoader(true)
    }
  }
  checkPreloadedData()
}, [])
```

#### 2. Dataset Switcher (`ControlPanel.jsx`)

New UI component added to control panel:
- Dropdown select showing all loaded datasets
- Displays node count for each dataset
- Clicking a dataset activates it on backend and reloads graph

```javascript
<select value={activeDataset} onChange={(e) => handleDatasetSwitch(e.target.value)}>
  {availableDatasets.map(dataset => (
    <option key={dataset} value={dataset}>
      {dataset.toUpperCase()} ({datasetsInfo[dataset].num_nodes} nodes)
    </option>
  ))}
</select>
```

#### 3. Header Badge

When datasets are pre-loaded, the header displays:
```
Loaded: CRAWLDB, LINKDB
```

#### 4. API Client Updates (`client.js`)

New methods:
```javascript
getStatus: async () => await apiClient.get('/api/status')
getDatasets: async () => await apiClient.get('/api/datasets')
activateDataset: async (datasetName) => await apiClient.post(`/api/datasets/${datasetName}/activate`)
```

## Usage Examples

### Load Single Dataset
```bash
reperio web --crawldb /path/to/crawldb
```

### Load Multiple Datasets (Recommended)
```bash
reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb
```

### Load All Three
```bash
reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb --hostdb /path/to/hostdb
```

### From HDFS
```bash
reperio web --crawldb hdfs://namenode:9000/nutch/crawldb --linkdb hdfs://namenode:9000/nutch/linkdb
```

### With Limits
```bash
reperio web --crawldb /path/to/crawldb --max-records 10000
```

## User Experience Improvements

### Before
1. Run: `reperio web`
2. Browser opens showing a form
3. Manually enter: database type, storage type, path
4. Click "Load Data"
5. Wait for loading
6. **To visualize another dataset**: Repeat steps 2-5

### After
1. Run: `reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb`
2. Browser opens showing the visualization immediately
3. **To switch datasets**: Use dropdown in control panel (instant)

## API Workflow

### Check Loaded Datasets
```bash
curl http://localhost:8000/api/status
```

Response:
```json
{
  "message": "Reperio API",
  "version": "0.1.0",
  "graph_loaded": true,
  "loaded_datasets": ["crawldb", "linkdb"],
  "active_dataset": "crawldb"
}
```

### List Datasets with Details
```bash
curl http://localhost:8000/api/datasets
```

Response:
```json
{
  "datasets": {
    "crawldb": {
      "name": "crawldb",
      "active": true,
      "num_nodes": 6605,
      "num_edges": 0,
      "metadata": {...}
    },
    "linkdb": {
      "name": "linkdb",
      "active": false,
      "num_nodes": 1234,
      "num_edges": 5678,
      "metadata": {...}
    }
  },
  "active_dataset": "crawldb",
  "total_loaded": 2
}
```

### Switch Active Dataset
```bash
curl -X POST http://localhost:8000/api/datasets/linkdb/activate
```

Response:
```json
{
  "status": "success",
  "active_dataset": "linkdb",
  "num_nodes": 1234,
  "num_edges": 5678,
  "metadata": {...}
}
```

## Backward Compatibility

The old workflow of loading data through the frontend form still works:
1. Run `reperio web` without dataset arguments
2. Frontend shows the `DataLoader` form
3. Fill in details and load data as before

This ensures users who prefer the form-based approach can still use it.

## Benefits

1. **Faster workflow**: No need to re-enter paths for each dataset
2. **Better visualization**: Load CrawlDB + LinkDB together for complete picture
3. **Easier comparison**: Switch between datasets instantly
4. **Cleaner UX**: Frontend UI is simpler and less redundant
5. **More powerful CLI**: Single command loads everything needed

## Testing

To test the multi-dataset support:

1. **Test single dataset loading**:
   ```bash
   reperio web --crawldb /path/to/crawldb
   ```

2. **Test multiple datasets**:
   ```bash
   reperio web --crawldb /path/to/crawldb --linkdb /path/to/linkdb
   ```

3. **Verify dataset switching**:
   - Open browser
   - Check that header shows "Loaded: CRAWLDB, LINKDB"
   - Open control panel
   - Find "Dataset" dropdown
   - Switch between datasets
   - Verify graph updates

4. **Test API endpoints**:
   ```bash
   curl http://localhost:8000/api/datasets
   curl -X POST http://localhost:8000/api/datasets/linkdb/activate
   ```

## Future Enhancements

Potential improvements for future versions:

1. **Side-by-side comparison**: View multiple datasets simultaneously
2. **Dataset merging**: Combine CrawlDB and LinkDB into a unified graph
3. **Dataset filtering**: Filter nodes/edges by dataset source
4. **Persistent storage**: Save loaded datasets to disk for faster reloading
5. **Background loading**: Load datasets asynchronously without blocking
6. **Progress indicators**: Real-time loading progress for each dataset
