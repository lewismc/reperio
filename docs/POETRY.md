# Poetry Guide for Reperio

This guide covers using Poetry with Reperio, including changes in Poetry 2.0+.

## Poetry Version Differences

### Poetry 1.x (Legacy)

Used `poetry shell` to activate virtual environments:

```bash
poetry shell
reperio --help
exit
```

### Poetry 2.0+ (Current)

The `shell` command is **not available by default**. Use one of these alternatives:

## Method 1: `poetry run` (Recommended)

Run commands directly without activating the environment:

```bash
poetry run reperio --help
poetry run reperio stats /path/to/crawldb --type crawldb
poetry run reperio serve --port 8000
```

**Advantages:**
- No activation/deactivation needed
- Works consistently across environments
- Recommended by Poetry maintainers

**Create an alias for convenience:**

```bash
# Add to ~/.zshrc or ~/.bashrc
alias reperio="poetry run reperio"

# Then use directly
reperio --help
```

## Method 2: Manual Activation

Activate the virtual environment manually:

```bash
# Get the virtual environment path
poetry env info --path

# Activate it (output will be something like /path/to/.venv)
source $(poetry env info --path)/bin/activate

# Now run commands directly
reperio --help
reperio stats /path/to/crawldb --type crawldb

# Deactivate when done
deactivate
```

## Method 3: Install Shell Plugin (Optional)

If you really want `poetry shell` back:

```bash
# Install the shell plugin
poetry self add poetry-plugin-shell

# Now shell command works
poetry shell
reperio --help
exit
```

## Common Commands

### Installation

```bash
# Install all dependencies
poetry install

# Install with extras (HDFS support)
poetry install --extras hdfs

# Install only production dependencies
poetry install --no-dev
```

### Running Commands

```bash
# Run any reperio command
poetry run reperio [command]

# Examples
poetry run reperio --version
poetry run reperio stats /path/to/data --type crawldb
poetry run reperio serve --port 8000
```

### Environment Management

```bash
# Show environment info
poetry env info

# List all environments
poetry env list

# Remove current environment
poetry env remove python

# Create new environment with specific Python
poetry env use python3.10
```

### Dependency Management

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show installed packages
poetry show

# Export requirements.txt (if needed)
poetry export -f requirements.txt --output requirements.txt
```

### Virtual Environment Location

```bash
# Find where Poetry created the virtual environment
poetry env info --path

# Example output:
# /Users/username/Library/Caches/pypoetry/virtualenvs/reperio-xyz-py3.10
```

## Troubleshooting

### Command Not Found After Installation

**Problem:**
```bash
reperio --help
# zsh: command not found: reperio
```

**Solution:**
Use `poetry run`:
```bash
poetry run reperio --help
```

Or activate the environment first:
```bash
source $(poetry env info --path)/bin/activate
reperio --help
```

### Poetry Shell Not Available

**Problem:**
```bash
poetry shell
# Error: shell command is not available
```

**Solution:**
This is expected in Poetry 2.0+. Use `poetry run` instead, or install the shell plugin:
```bash
poetry self add poetry-plugin-shell
```

### Wrong Python Version

**Problem:**
Poetry uses wrong Python version.

**Solution:**
```bash
# Specify Python version
poetry env use python3.10

# Or use full path
poetry env use /usr/bin/python3.10

# Verify
poetry env info
```

### Dependencies Not Found

**Problem:**
Import errors when running code.

**Solution:**
```bash
# Reinstall dependencies
poetry install

# Or update lock file
poetry update
```

### Slow Installation

**Problem:**
`poetry install` is very slow.

**Solution:**
```bash
# Use parallel installation (Poetry 1.2+)
poetry config installer.parallel true

# Or increase max workers
poetry config installer.max-workers 10
```

### Poetry Environment Issues or Typer/Click Errors

**Problem:**
```bash
reperio --help
# TypeError: Secondary flag is not valid for non-boolean flag.
```

Or encountering `packaging.metadata` errors, or Poetry refusing to work with your Python version.

**Solution (Recommended): Use Python venv Instead**

Poetry can have compatibility issues with certain Python versions or system configurations. For a more reliable setup, use Python's built-in `venv`:

```bash
# Navigate to the project directory
cd /path/to/reperio

# Create a virtual environment with Python 3.10+
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install reperio in development mode
pip install -e .

# Optional: Install with HDFS support
pip install -e ".[hdfs]"

# Upgrade Typer if needed (requires 0.12+)
pip install --upgrade 'typer>=0.12.0'

# Run commands directly
reperio --help
reperio stats path/to/data --type crawldb

# Deactivate when done
deactivate
```

This approach bypasses Poetry entirely and works reliably across different Python versions and platforms.

## Best Practices

### 1. Always Use `poetry run`

For consistency and simplicity, always use `poetry run` in documentation and scripts:

```bash
# Good
poetry run reperio serve

# Works but requires activation
reperio serve
```

### 2. Pin Python Version

Specify Python version in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.10"
```

### 3. Use Extras for Optional Dependencies

```toml
[tool.poetry.extras]
hdfs = ["pyarrow"]
```

Install with:
```bash
poetry install --extras hdfs
```

### 4. Lock Dependencies

Always commit `poetry.lock` to version control:

```bash
git add poetry.lock
git commit -m "Update dependencies"
```

### 5. CI/CD Integration

For GitHub Actions or similar:

```yaml
- name: Install dependencies
  run: |
    pip install poetry
    poetry install

- name: Run tests
  run: poetry run pytest
```

## Migration from Poetry 1.x

If upgrading from Poetry 1.x:

1. **Update Poetry:**
   ```bash
   poetry self update
   ```

2. **Replace `poetry shell` commands:**
   ```bash
   # Old (Poetry 1.x)
   poetry shell
   reperio --help
   
   # New (Poetry 2.0+)
   poetry run reperio --help
   ```

3. **Update documentation** to use `poetry run`

4. **Update scripts:**
   ```bash
   # Old
   #!/bin/bash
   poetry shell
   reperio serve
   
   # New
   #!/bin/bash
   poetry run reperio serve
   ```

## Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry 2.0 Migration Guide](https://python-poetry.org/docs/master/migration/)
- [Managing Environments](https://python-poetry.org/docs/managing-environments/)
- [Poetry Shell Plugin](https://github.com/python-poetry/poetry-plugin-shell)
