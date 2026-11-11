#!/usr/bin/env bash
# Builds apidocs.lightburnsoftware.com into site/. Cloudflare Pages runs this
# on every push (build command "bash build.sh", output directory "site"); a
# failure fails the deployment and the previous one stays live.
#
#   bash build.sh          build site/
#   bash build.sh serve    build, then serve site/ on http://localhost:8000
#                          (no live reload: rerun after editing)
#
# Needs Python 3 and Node. Run it from a virtualenv locally.
set -euo pipefail
cd "$(dirname "$0")"

REDOCLY_CLI_VERSION=2.71.2

pip install --quiet -r requirements.txt

# Assemble the MkDocs source tree. The guides go one level down so that their
# links to the root documents (../SAFETY.md, ../CHANGELOG.md) resolve here
# exactly as they do on GitHub.
rm -rf .build site
mkdir -p .build/src/guide
cp -R website/. .build/src/
cp docs/*.md docs/openapi.yaml .build/src/guide/
cp API-EULA.md CERTIFICATION.md CHANGELOG.md DISCLOSURE.md NOTICE.md \
   POLICY.md SAFETY.md SECURITY.md .build/src/

# --strict turns broken links and missing nav entries into errors.
mkdocs build --strict

# The full reference: Redoc pre-renders the spec into one HTML page. Its
# script still loads from cdn.redocly.com, pinned to the Redoc version this
# CLI release ships and checked with an integrity hash.
npx --yes "@redocly/cli@${REDOCLY_CLI_VERSION}" build-docs docs/openapi.yaml \
    --output site/reference/index.html \
    --title "LightBurn / MillMage REST API reference"

if [[ "${1:-}" == "serve" ]]; then
    python3 -m http.server --directory site 8000
fi
