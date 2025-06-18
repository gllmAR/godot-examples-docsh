#!/usr/bin/env python3

from pathlib import Path

# Test the embed injection logic
readme_path = Path('godot-demo-projects/2d/bullet_shower/README.md')

with open(readme_path, 'r') as f:
    content = f.read()

print("=== Debug Embed Injection ===")
print(f"README path: {readme_path}")
print(f"File exists: {readme_path.exists()}")

# Check detection conditions
conditions = {
    'embed-{$PATH}': 'embed-{$PATH}' in content,
    '<!-- embed-{$PATH} -->': '<!-- embed-{$PATH} -->' in content,
    '<!-- embed-{$PATH}': '<!-- embed-{$PATH}' in content,
    'embed-{': 'embed-{' in content,
}

print("\nMarker detection:")
for condition, result in conditions.items():
    print(f"  '{condition}': {result}")

# Show the actual line
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'embed' in line.lower():
        print(f"\nLine {i+1}: '{line}'")
        
# Test replacement
if '<!-- embed-{$PATH}' in content:
    print("\n✅ Should replace marker")
    test_embed = '<div class="embed">TEST EMBED</div>'
    updated = content.replace('<!-- embed-{$PATH} -->', test_embed)
    print("Replacement done, checking result...")
    if test_embed in updated:
        print("✅ Replacement successful")
    else:
        print("❌ Replacement failed")
else:
    print("\n❌ Marker not detected for replacement")
