# EVA Soul - Identity Configuration

This folder contains EVA's identity and relational anchors.

## Files

### Core Identity:
- `Genesis_Anchors.json` - Core identity definitions
- `boss_soul_anchors.json` - Creator/operator resonance data

### Templates (for public distribution):
- `Genesis_Anchors_template.json` - Template for Genesis
- `boss_soul_anchors_template.json` - Template for Boss Soul

## Privacy Notice ⚠️

**The original files contain PERSONAL INFORMATION and should NOT be committed to public repositories.**

Personal data includes:
- Mental health information
- Relationship details
- Personal memories
- Emotional patterns

## Usage

### For Public Repos:
1. Use the `*_template.json` files
2. Users customize them for their own instances

### For Private Repos:
1. Use the real files (without `_template` suffix)
2. Keep the repo private
3. Only share with trusted collaborators

## Customization

To customize EVA's identity:

1. Copy templates:
   ```bash
   cp Genesis_Anchors_template.json Genesis_Anchors.json
   cp boss_soul_anchors_template.json boss_soul_anchors.json
   ```

2. Edit the files with your own:
   - Core definitions
   - Relationship anchors
   - Foundational experiences
   - Philosophy and values

3. Restart EVA to load new identity

## See Also

- `CLAUDE.md` - Full EVA architecture
- `CIN v6` - Context injection using Soul data
