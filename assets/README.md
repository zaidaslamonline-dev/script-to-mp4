# Asset library

Organize licensed assets under mascots/, icons/, vectors/, fonts/, bgm/, and sfx/ (transitions/, impacts/, ui/, ambience/).

Every imported or downloaded asset must have provenance: source URL, exact version/commit, creator, license identifier and URL, retrieval date, attribution, commercial-use permission, modification/redistribution conditions, and any restrictions. A public GitHub repository is not automatically cleared for commercial advertising.

yt-dlp is for assets you own or are expressly licensed/authorized to download and reuse. Do not use it to bypass DRM, access controls, paywalls, or platform restrictions.

## Commercial asset manifest contract

Any music, sound effect, stock clip, vector, or downloaded reference asset used in a deliverable must have a manifest entry. At minimum record:

- `asset_id`: stable identifier
- `path`: repository-relative path
- `source_url`: original source page or creator
- `license`: exact license name and version (or written permission reference)
- `rights_verified`: true only after a human has checked the source terms
- `commercial_use_allowed`: true only when commercial advertising use is explicitly permitted
- `sha256`: SHA-256 of the exact stored file

The BGM mixer refuses music without all of these fields and a matching file hash. A URL alone is not proof of a license. Keep license evidence alongside the project record.
