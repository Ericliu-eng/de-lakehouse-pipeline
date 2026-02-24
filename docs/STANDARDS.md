```markdown
# Standards

## Branch naming
- Use lowercase + hyphen, e.g. `w01/d1-repo-skeleton-ci-makefile`

## Commits
- Conventional style, e.g. `feat: ...`

## Local commands (must stay reproducible)
- `make setup`
- `make lint`
- `make test`

## PR checklist
- CI green (or explain why not)
- Include how to validate
- Include proof under `docs/proof/`

## Commit Message Convention
We follow Conventional Commits:

| Type      | Meaning              |
|-----------|---------------------|
| feat      | New feature         |
| fix       | Bug fix             |
| docs      | Documentation       |
| refactor  | Code refactoring    |
| test      | Add/update tests    |
| chore     | Maintenance/config  |

### Examples

feat: add postgres migration pipeline  
fix: handle missing values in transform  
test: add db smoke test  