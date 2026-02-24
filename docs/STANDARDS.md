# Standards

## Branch Naming
- Use lowercase + hyphen  
- Example: `w01/d1-repo-skeleton-ci-makefile`

---

## Commit Convention
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

---

## PR Checklist
- CI is green (or explain why not)
- Include how to validate
- Include proof under `docs/proof/`

---

## Reproducible Commands
All commands must be runnable from a fresh environment:

- `make setup`
- `make lint`
- `make test`