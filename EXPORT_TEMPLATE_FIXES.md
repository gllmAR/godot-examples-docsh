# Godot Export Template Installation Fixes

## Issues Identified
1. **Template Installation**: Export templates were not being extracted correctly to the expected directory structure
2. **Version Format**: Pre-release versions (e.g., `4.5-beta1`) needed to be converted to the correct template format (`4.5.beta1`)
3. **Template Validation**: No verification that templates were properly installed and accessible to Godot
4. **Directory Structure**: Templates were being extracted to wrong locations

## Fixes Implemented

### 1. Improved Template Installation Process
```bash
# Extract templates to temporary location first
unzip -q export_templates.tpz -d temp_templates/

# Move templates to correct location with proper handling
if [ -d "temp_templates/templates" ]; then
    mv temp_templates/templates ~/.local/share/godot/export_templates/${GODOT_TEMPLATE_VERSION}
else
    mv temp_templates ~/.local/share/godot/export_templates/${GODOT_TEMPLATE_VERSION}
fi
```

### 2. Template Version Format Conversion
```bash
# Convert version format for pre-release versions
if [[ "${GODOT_VERSION}" == *"-beta"* ]]; then
    GODOT_TEMPLATE_VERSION="${GODOT_VERSION/-beta/.beta}"
elif [[ "${GODOT_VERSION}" == *"-alpha"* ]]; then
    GODOT_TEMPLATE_VERSION="${GODOT_VERSION/-alpha/.alpha}"
elif [[ "${GODOT_VERSION}" == *"-rc"* ]]; then
    GODOT_TEMPLATE_VERSION="${GODOT_VERSION/-rc/.rc}"
else
    GODOT_TEMPLATE_VERSION="${GODOT_VERSION}"
fi
```

### 3. Template Validation Step
```bash
# Test export template functionality
godot --headless --quit --list-export-templates
godot --headless --export-debug "Web" test.html --quit
```

### 4. Enhanced Build System Validation
Added template validation to the build system:
```python
def validate_export_templates(godot_binary='godot', verbose=False):
    """Validate that Godot can find export templates"""
    result = subprocess.run(
        [godot_binary, '--headless', '--quit', '--list-export-templates'],
        capture_output=True, text=True, timeout=30
    )
    return 'Web' in result.stdout if result.stdout else False
```

### 5. Comprehensive Debugging
- Added detailed logging of template extraction process
- Verification of directory structures
- Search for web-specific template files
- Version.txt validation
- Export capability testing

## Expected Results
With these fixes:
1. Export templates should be properly installed to `~/.local/share/godot/export_templates/4.5.beta1/`
2. Godot should detect web export templates correctly
3. Web exports should be successfully generated for all projects
4. The final documentation site should include all interactive web demos

## Verification Steps
The workflow now includes these validation steps:
1. **Template Installation Verification**: Check directory structure and file presence
2. **Template Detection Test**: Use `--list-export-templates` to verify Godot can see templates
3. **Export Capability Test**: Try a minimal export to verify functionality
4. **Build Result Verification**: Count and verify all web exports were created

## Monitoring
Monitor the next workflow run to ensure:
- ✅ Export templates are properly installed
- ✅ Godot detects web export templates
- ✅ All projects export successfully
- ✅ Web exports are present in final documentation site
