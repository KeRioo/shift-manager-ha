#!/bin/bash
# bump-version.sh – updates version in all project files at once
# Usage: ./bump-version.sh 1.2.0

set -euo pipefail

NEW_VERSION="${1:?Usage: $0 <new-version>  (e.g. 1.2.0)}"

# Validate semver format
if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "❌ Invalid version format. Use semver: X.Y.Z"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR"

echo "🔄 Bumping version to $NEW_VERSION ..."

# 1. addon/config.yaml
sed -i "s/^version: .*/version: $NEW_VERSION/" "$ROOT/addon/config.yaml"
echo "  ✅ addon/config.yaml"

# 2. custom_components/work_schedule/manifest.json
sed -i "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" "$ROOT/custom_components/work_schedule/manifest.json"
echo "  ✅ custom_components/work_schedule/manifest.json"

echo ""
echo "✅ All files updated to v$NEW_VERSION"
echo ""
echo "Next steps:"
echo "  1. Update CHANGELOG.md with new entry"
echo "  2. git add -A && git commit -m \"release: v$NEW_VERSION\""
echo "  3. git tag v$NEW_VERSION"
echo "  4. git push && git push --tags"
