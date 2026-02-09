# Nutch Tool Integration

Reperio integrates with Apache Nutch's built-in tools for robust data reading and visualization.

## Philosophy

**Reperio focuses on visualization, not reimplementing Nutch's functionality.**

Nutch already provides excellent tools for reading its data structures:
- `readdb` for CrawlDB
- `readlinkdb` for LinkDB  
- `readhostdb` for HostDB

These tools:
- ✅ Handle all compression formats natively
- ✅ Support all SequenceFile formats
- ✅ Are well-tested and maintained
- ✅ Can export to various formats

**Reperio adds:** Interactive graph visualization, analysis, and exploration.

## Recommended Workflow

### Step 1: Export Data with Nutch Tools

Use Nutch's tools to export your data to a format Reperio can read:

```bash
# Export CrawlDB
nutch readdb /path/to/crawldb -dump crawldb-export.txt

# Export LinkDB
nutch readlinkdb /path/to/linkdb -dump linkdb-export.txt

# Export HostDB
nutch readhostdb /path/to/hostdb -dump hostdb-export.txt -csv
```

### Step 2: Visualize with Reperio

```bash
# Load and analyze
poetry run reperio stats crawldb-export.txt --type crawldb

# Export as graph
poetry run reperio export crawldb-export.txt graph.json \
  --type crawldb --format json

# Start web interface
poetry run reperio serve
# Then load the export file through the web UI
```

## Nutch Tool Export Formats

### CrawlDB Export (readdb)

Text format example:
```
http://example.com
    Status: 2 (db_fetched)
    Fetch time: Mon Jan 01 00:00:00 UTC 2024
    Modified time: Mon Jan 01 00:00:00 UTC 2024
    Retries since fetch: 0
    Retry interval: 2592000 seconds (30 days)
    Score: 1.0
    Signature: null

http://another.com
    Status: 1 (db_unfetched)
    Fetch time: Thu Jan 01 00:00:00 UTC 1970
    Modified time: Thu Jan 01 00:00:00 UTC 1970
    Retries since fetch: 0
    Retry interval: 2592000 seconds (30 days)
    Score: 1.0
    Signature: null
```

**Export command:**
```bash
nutch readdb /path/to/crawldb -dump output.txt
```

**Load in Reperio:**
```bash
poetry run reperio stats output.txt --type crawldb --input-format nutch-export
```

### LinkDB Export (readlinkdb)

Text format example:
```
http://target.com
    Inlinks:
    http://source1.com
        Anchor: Click here
    http://source2.com
        Anchor: Visit site
```

**Export command:**
```bash
nutch readlinkdb /path/to/linkdb -dump output.txt
```

**Load in Reperio:**
```bash
poetry run reperio stats output.txt --type linkdb --input-format nutch-export
```

### HostDB Export (readhostdb)

CSV or text format with host statistics.

**Export command:**
```bash
nutch readhostdb /path/to/hostdb -dump output.txt
```

## Working with Compressed Data

### Problem: Compressed SequenceFiles

If you encounter this error:
```
Error: Compressed SequenceFiles are not yet supported. 
Codec: org.apache.hadoop.io.compress.DefaultCodec
```

### Solution: Use Nutch Tools

Nutch tools handle compression automatically:

```bash
# Step 1: Export with Nutch (handles compression)
nutch readdb /path/to/compressed/crawldb -dump crawldb.txt

# Step 2: Visualize with Reperio
poetry run reperio stats crawldb.txt --type crawldb
```

## Auto-Detection

Reperio can auto-detect the input format:

```bash
# Auto-detects SequenceFile
poetry run reperio stats /path/to/crawldb/part-r-00000/data --type crawldb

# Auto-detects Nutch export (text file)
poetry run reperio stats crawldb-export.txt --type crawldb

# Explicit format (recommended for clarity)
poetry run reperio stats crawldb-export.txt --type crawldb --input-format nutch-export
```

Auto-detection looks for:
1. File extension (`.txt`, `.json`)
2. File size (small files are likely exports)
3. Content format (tries to read as text)

## Complete Examples

### Example 1: Visualize Complete Crawl

```bash
# 1. Export CrawlDB and LinkDB
nutch readdb /nutch/crawldb -dump crawldb.txt
nutch readlinkdb /nutch/linkdb -dump linkdb.txt

# 2. View statistics
poetry run reperio stats crawldb.txt --type crawldb
poetry run reperio stats linkdb.txt --type linkdb

# 3. Export combined graph
poetry run reperio export crawldb.txt crawldb-graph.json \
  --type crawldb --format sigma

# 4. Start web interface for interactive exploration
poetry run reperio serve &
cd frontend && npm run dev
```

### Example 2: Analyze Specific Domain

```bash
# Export filtered CrawlDB
nutch readdb /nutch/crawldb -dump full.txt

# Filter for specific domain
grep "example.com" full.txt > example-com.txt

# Visualize domain-specific data
poetry run reperio stats example-com.txt --type crawldb
```

### Example 3: Pipeline with Nutch

```bash
# Create a pipeline script
#!/bin/bash

# Run Nutch crawl
nutch inject crawldb urls
nutch generate crawldb segments -topN 100
# ... more Nutch commands ...

# Export for visualization
nutch readdb crawldb -dump export/crawldb.txt
nutch readlinkdb linkdb -dump export/linkdb.txt

# Visualize results
poetry run reperio export export/crawldb.txt results/crawl-$(date +%Y%m%d).json \
  --type crawldb --format json

echo "Visualization ready: results/crawl-$(date +%Y%m%d).json"
```

### Example 4: HDFS to Local Visualization

```bash
# Export from HDFS
nutch readdb hdfs://namenode:9000/nutch/crawldb -dump crawldb.txt

# Visualize locally
poetry run reperio stats crawldb.txt --type crawldb
```

## Direct SequenceFile Support

Reperio still supports direct SequenceFile reading for **uncompressed files**:

```bash
# Works if file is uncompressed
poetry run reperio stats /path/to/crawldb/part-r-00000/data \
  --type crawldb --input-format sequencefile
```

**Use cases for direct SequenceFile reading:**
- Quick testing with small, uncompressed files
- Development and debugging
- When you know files are uncompressed

**Limitations:**
- ❌ No compression support
- ❌ Limited error handling
- ❌ May not handle all Nutch versions

**For production, always use Nutch tools first.**

## Best Practices

### 1. Always Use Nutch Tools for Export

```bash
# ✅ Recommended
nutch readdb crawldb -dump export.txt
poetry run reperio stats export.txt --type crawldb

# ⚠️ Only for uncompressed files
poetry run reperio stats crawldb/part-r-00000/data --type crawldb
```

### 2. Export to Dedicated Directory

```bash
# Create export directory
mkdir -p nutch-exports

# Export all data structures
nutch readdb crawldb -dump nutch-exports/crawldb.txt
nutch readlinkdb linkdb -dump nutch-exports/linkdb.txt
nutch readhostdb hostdb -dump nutch-exports/hostdb.txt

# Keep organized
ls nutch-exports/
# crawldb.txt  linkdb.txt  hostdb.txt
```

### 3. Use Descriptive Filenames

```bash
# Include date and crawl ID
nutch readdb crawldb -dump export-20240101-crawl01.txt
poetry run reperio stats export-20240101-crawl01.txt --type crawldb
```

### 4. Combine with Version Control

```bash
# Export and version
nutch readdb crawldb -dump exports/crawldb-$(git rev-parse --short HEAD).txt

# Track exports in git
git add exports/
git commit -m "Add crawl export for commit $(git rev-parse --short HEAD)"
```

## Troubleshooting

### "Compressed SequenceFiles not supported"

**Problem:**
```bash
poetry run reperio stats /path/to/crawldb --type crawldb
Error: Compressed SequenceFiles are not yet supported
```

**Solution:**
Use Nutch readdb:
```bash
nutch readdb /path/to/crawldb -dump crawldb.txt
poetry run reperio stats crawldb.txt --type crawldb
```

### Auto-detection Issues

**Problem:**
Reperio doesn't correctly detect file format.

**Solution:**
Explicitly specify format:
```bash
poetry run reperio stats file.txt --type crawldb --input-format nutch-export
```

### Empty Results

**Problem:**
No records parsed from export file.

**Solution:**
Check export format:
```bash
# Verify export file
head -20 crawldb.txt

# Try different Nutch options
nutch readdb crawldb -dump output.txt -format normal
```

## Performance Comparison

| Method | Pros | Cons | Use Case |
|--------|------|------|----------|
| **Nutch Tools** | Handles compression, robust, well-tested | Extra step | Production, compressed files |
| **Direct SequenceFile** | Faster for small files, no export | No compression | Development, small datasets |

**Recommendation:** Use Nutch tools for all production work.

## Future Enhancements

Potential improvements for Reperio:

1. **Compression Support**: Add native compression handling
2. **Streaming Pipeline**: Read Nutch tool output via pipe
3. **Nutch Integration**: Call Nutch tools directly from Reperio
4. **Format Converter**: GUI tool to convert between formats

## References

- [Nutch readdb documentation](https://cwiki.apache.org/confluence/display/NUTCH/bin%2Fnutch+readdb)
- [Nutch readlinkdb documentation](https://cwiki.apache.org/confluence/display/NUTCH/bin%2Fnutch+readlinkdb)
- [Nutch readhostdb documentation](https://cwiki.apache.org/confluence/display/NUTCH/bin%2Fnutch+readhostdb)
