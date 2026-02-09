# Troubleshooting Guide

This guide covers common issues and their solutions when using Reperio.

## Installation Issues

### TypeError: Secondary flag is not valid for non-boolean flag

**Problem:**
When running `reperio --help` or any other command, you get:
```bash
TypeError: Secondary flag is not valid for non-boolean flag.
```

**Cause:**
This error occurs when Typer 0.4.x is installed with Click 8.x. These versions are incompatible.

**Solution:**
Upgrade Typer to version 0.12 or higher:

```bash
# If using venv
source venv/bin/activate
pip install --upgrade 'typer>=0.12.0'

# If using Poetry
poetry add 'typer>=0.12.0'
```

### Command Not Found: reperio

**Problem:**
```bash
reperio --help
# zsh: command not found: reperio
```

**Cause:**
The virtual environment is not activated or the package is not installed.

**Solutions:**

**If using venv:**
```bash
# Navigate to project directory
cd /path/to/reperio

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Now run commands
reperio --help
```

**If using Poetry:**
```bash
# Option 1: Use poetry run (recommended)
poetry run reperio --help

# Option 2: Activate manually
source $(poetry env info --path)/bin/activate
reperio --help
```

### No module named 'packaging.metadata'

**Problem:**
When running Poetry commands:
```bash
poetry run reperio web
# No module named 'packaging.metadata'
```

**Cause:**
Poetry environment corruption or Python version incompatibility (often with Homebrew Python installations).

**Solution: Use venv Instead of Poetry**

The most reliable solution is to bypass Poetry and use Python's built-in venv:

```bash
# Navigate to project directory
cd /path/to/reperio

# Remove any existing Poetry environments
rm -rf .venv

# Create a fresh venv with Python 3.10+
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install in development mode
pip install -e .

# Test
reperio --help
```

### Poetry Shell Command Not Available

**Problem:**
```bash
poetry shell
# Looks like you're trying to use a Poetry command that is not available.
# Since Poetry (2.0.0), the shell command is not installed by default.
```

**Cause:**
Poetry 2.0+ removed the `shell` command by default.

**Solutions:**

**Option 1: Use `poetry run` (Recommended)**
```bash
poetry run reperio --help
poetry run reperio serve
```

**Option 2: Manual Activation**
```bash
source $(poetry env info --path)/bin/activate
reperio --help
```

**Option 3: Install Shell Plugin**
```bash
poetry self add poetry-plugin-shell
poetry shell
```

## Runtime Issues

### Compressed SequenceFiles Not Supported

**Problem:**
```bash
reperio stats /path/to/linkdb --type linkdb
# Error: Compressed SequenceFiles are not yet supported. Codec: org.apache.hadoop.io.compress.DefaultCodec
```

**Cause:**
Reperio doesn't support compressed SequenceFiles directly (implementing all Hadoop codecs is complex and error-prone).

**Solution: Use Nutch Export Tools**

This is the recommended approach - leverage Nutch's robust data reading tools:

```bash
# For CrawlDB
nutch readdb /path/to/crawldb -dump crawldb-export.txt
reperio stats crawldb-export.txt --type crawldb --input-format nutch-export

# For LinkDB
nutch readlinkdb /path/to/linkdb -dump linkdb-export.txt
reperio stats linkdb-export.txt --type linkdb --input-format nutch-export

# For HostDB
nutch readhostdb /path/to/hostdb -dump hostdb-export.txt
reperio stats hostdb-export.txt --type hostdb --input-format nutch-export
```

### SSL Certificate Verification Errors

**Problem:**
```bash
pip install -e .
# SSLError(SSLCertVerificationError('OSStatus -26276'))
```

**Cause:**
SSL certificate issues, often on macOS.

**Solutions:**

**Option 1: Update SSL certificates**
```bash
# On macOS with Python from python.org
/Applications/Python\ 3.x/Install\ Certificates.command

# Or reinstall certificates
pip install --upgrade certifi
```

**Option 2: Use system Python**
```bash
# Use Homebrew Python instead
brew install python@3.10
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

**Option 3: Temporarily bypass SSL (NOT recommended for production)**
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -e .
```

### Frontend Build Warnings

**Problem:**
When running `npm install` in the frontend directory:
```bash
npm warn deprecated eslint@8.57.1: This version is no longer supported.
npm warn deprecated glob@7.2.3: Old versions of glob contain security vulnerabilities.
```

**Cause:**
These are warnings about outdated transitive dependencies. They're not breaking errors.

**Solution:**
These warnings can generally be ignored as they come from sub-dependencies. However, to fix them:

```bash
cd frontend

# Update all dependencies
npm update

# Or audit and fix
npm audit fix

# For major breaking changes
npm audit fix --force
```

The Reperio frontend uses ESLint 9 with the new flat config, so the core linting setup is modern and secure.

### HDFS Connection Issues

**Problem:**
Can't connect to HDFS cluster or read files from HDFS.

**Solution:**

1. **Verify HDFS access:**
   ```bash
   hdfs dfs -ls /path/to/data
   ```

2. **Install HDFS extras:**
   ```bash
   pip install -e ".[hdfs]"
   # or
   poetry install --extras hdfs
   ```

3. **Provide namenode info:**
   ```bash
   reperio stats hdfs:///path/to/crawldb \
     --type crawldb \
     --namenode namenode.example.com \
     --port 9000
   ```

4. **Check Hadoop configuration:**
   ```bash
   # Ensure HADOOP_CONF_DIR is set
   export HADOOP_CONF_DIR=/etc/hadoop/conf
   
   reperio stats hdfs:///path/to/data --type crawldb
   ```

## Web Interface Issues

### Frontend Not Built Warning

**Problem:**
```bash
reperio web
# Warning: Frontend not built. Run 'npm run build' in the frontend directory.
```

**Cause:**
The React frontend hasn't been compiled to static files.

**Solution:**
```bash
# Build the frontend
cd frontend
npm install
npm run build

# Now start the web interface
cd ..
reperio web
```

### API Server Not Starting

**Problem:**
```bash
reperio serve
# Error: FastAPI and uvicorn are required.
```

**Cause:**
FastAPI dependencies not installed.

**Solution:**
```bash
# Reinstall with all dependencies
pip install -e .

# Or install FastAPI manually
pip install fastapi 'uvicorn[standard]'
```

### Port Already in Use

**Problem:**
```bash
reperio web
# Error: [Errno 48] Address already in use
```

**Solution:**
```bash
# Use a different port
reperio web --port 8080

# Or find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

## Graph Visualization Issues

### Graph Too Large to Display

**Problem:**
Browser freezes or crashes when loading large graphs.

**Solution:**

1. **Limit the number of records:**
   ```bash
   reperio export /path/to/linkdb graph.json \
     --type linkdb \
     --max-records 10000 \
     --format sigma
   ```

2. **Filter before visualization:**
   ```python
   # Use the API to filter
   import requests
   
   # Apply filters via API
   response = requests.post('http://localhost:8000/api/graph/filter', json={
       'min_score': 0.5,
       'status': 'db_fetched',
       'max_nodes': 5000
   })
   ```

3. **Sample the graph:**
   Use Reperio's built-in graph sampling to get a representative subset.

### Frontend Not Built Warning

**Problem:**
When running `reperio web`, you see:
```
Warning: Frontend not built. Run 'npm run build' in the frontend directory.
API will be available at: http://localhost:{port}/docs
```

And when you open `http://localhost:8000` in your browser, you only see the API documentation page instead of the interactive graph visualization.

**Cause:**
The React + Sigma.js frontend hasn't been built. Reperio's visualization requires a compiled frontend application to render the interactive graph.

**What You'll See Without Frontend:**
- ✅ Backend API works correctly (loads data, processes partitions)
- ✅ REST API endpoints accessible at `/api/graph/*`
- ✅ API documentation visible at `/docs`
- ❌ No interactive graph visualization
- ❌ No web UI for exploring nodes/edges

**Solution:**

Build the frontend (one-time setup):

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Build the frontend for production
npm run build

# Return to project root
cd ..

# Now restart reperio web
reperio web /path/to/your/data --type crawldb
```

The build process creates a `frontend/dist/` directory with the compiled React application. After building, `reperio web` will serve this at `http://localhost:8000` and you'll see the interactive graph visualization.

**What You'll See After Building:**
- Interactive WebGL graph visualization with Sigma.js
- Nodes representing URLs, colored by status
- Edges showing link relationships (for LinkDB)
- Pan, zoom, and click interactions
- Control panel for filtering and layout adjustment
- Node detail panel showing metadata

**Development Mode** (optional, for frontend developers):
```bash
cd frontend
npm run dev  # Runs dev server with hot reload at http://localhost:5173
```

### Visualization Not Interactive

**Problem:**
Graph displays but can't interact with it (zoom, pan, select nodes).

**Solution:**

1. **Check browser console** (F12) for JavaScript errors
2. **Clear browser cache**
3. **Try a different browser** (Chrome/Firefox recommended)
4. **Ensure WebGL is enabled:**
   - Chrome: `chrome://gpu`
   - Firefox: `about:support` → Graphics section

## Python Version Issues

### Python Version Mismatch

**Problem:**
```bash
poetry install
# Error: The current Python version (3.9.x) is not supported by the project
```

**Solution:**

**Option 1: Install Python 3.10+**
```bash
# Using Homebrew (macOS)
brew install python@3.10

# Using apt (Ubuntu/Debian)
sudo apt install python3.10

# Using pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

**Option 2: Update pyproject.toml** (if you must use older Python)
```toml
[tool.poetry.dependencies]
python = "^3.9"  # Changed from ^3.10
```

### Multiple Python Versions

**Problem:**
System has multiple Python versions and Poetry/pip uses the wrong one.

**Solution:**

```bash
# Explicitly specify Python version
python3.10 -m venv venv
source venv/bin/activate

# Verify
python --version
# Should show Python 3.10.x

# With Poetry
poetry env use python3.10
poetry env info  # Verify
```

## Data Format Issues

### Auto-Detection Not Working

**Problem:**
Reperio can't automatically detect the input format.

**Solution:**
Explicitly specify the format:

```bash
# For SequenceFiles
reperio stats /path/to/data --type crawldb --input-format sequencefile

# For Nutch exports
reperio stats crawldb-export.txt --type crawldb --input-format nutch-export
```

### Invalid Data Format

**Problem:**
```bash
reperio stats data.txt --type crawldb
# Error: Invalid format or corrupted data
```

**Solutions:**

1. **Verify file format:**
   ```bash
   # For SequenceFiles
   file /path/to/sequencefile
   # Should show: Hadoop SequenceFile
   
   # For text exports
   head -n 5 data.txt
   # Should show readable URL/data pairs
   ```

2. **Re-export with Nutch:**
   ```bash
   nutch readdb /path/to/crawldb -dump new-export.txt
   reperio stats new-export.txt --type crawldb
   ```

3. **Check file permissions:**
   ```bash
   ls -la /path/to/data
   chmod 644 /path/to/data
   ```

## Getting Help

If you continue to experience issues:

1. **Check the logs:**
   ```bash
   # Run with verbose output
   reperio serve --reload  # Shows detailed uvicorn logs
   ```

2. **Search existing issues:**
   [GitHub Issues](https://github.com/lewismc/reperio/issues)

3. **Open a new issue:**
   Include:
   - Reperio version: `reperio --version`
   - Python version: `python --version`
   - OS and version
   - Full error message and stack trace
   - Steps to reproduce

4. **Enable debug mode** (if available in future versions):
   ```bash
   export REPERIO_DEBUG=1
   reperio stats /path/to/data --type crawldb
   ```

## Quick Reference: Common Solutions

| Issue | Quick Fix |
|-------|-----------|
| `command not found: reperio` | `source venv/bin/activate` or `poetry run reperio` |
| `TypeError: Secondary flag` | `pip install --upgrade 'typer>=0.12.0'` |
| `packaging.metadata` error | Use `venv` instead of Poetry |
| Compressed SequenceFile | Use `nutch readdb -dump` first |
| `poetry shell` not found | Use `poetry run` or install shell plugin |
| Port in use | `reperio web --port 8080` |
| Frontend not built | `cd frontend && npm run build` |
| SSL errors | Update certificates or use system Python |

## Related Documentation

- [Poetry Guide](POETRY.md) - Detailed Poetry usage
- [Usage Guide](USAGE.md) - General usage examples
- [API Documentation](API.md) - REST API reference
- [Nutch Integration](NUTCH_INTEGRATION.md) - Working with Nutch data
