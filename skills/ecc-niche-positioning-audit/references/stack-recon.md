# Stack Reconnaissance — Per-Stack Enumeration

Stack-specific route/endpoint enumeration commands, coverage accounting, unknown states, and fail-closed inventory gates.

## Stack Detection Signals

| Signal File | Detects | Stack ID |
|-------------|---------|----------|
| `package.json` | Node.js ecosystem | `node` |
| `requirements.txt` / `pyproject.toml` | Python | `python` |
| `go.mod` | Go | `go` |
| `Cargo.toml` | Rust | `rust` |
| `Gemfile` | Ruby | `ruby` |
| `pom.xml` / `build.gradle` | Java | `java` |

If stack cannot be auto-detected, ask the user. If multi-stack (monorepo), detect all and inventory each separately.

## Per-Stack Route Enumeration

### Next.js (`next`)

```bash
# App router pages
find app -name "page.tsx" -o -name "page.ts" -o -name "page.jsx" -o -name "page.js" 2>/dev/null

# App router API routes
find app -name "route.ts" -o -name "route.ts" -o -name "route.jsx" -o -name "route.js" 2>/dev/null

# Pages router (legacy)
find pages -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" 2>/dev/null | grep -v '_app\|_document\|_error\|api'

# Pages router API
find pages/api -name "*.ts" -o -name "*.js" 2>/dev/null
```

Coverage: count of `page.*` files + `route.*` files. If directory structure is non-standard, flag as "unknown coverage."

### React — Vite/CRA (`react`)

```bash
# Route definitions (react-router)
grep -rn "Route\|path:" src/ --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" | grep -v node_modules

# Or find router config files
find src -name "router*" -o -name "routes*" -o -name "App.*" 2>/dev/null
```

Coverage: count of `<Route>` elements or route config entries. If no router found, flag as "no router detected — coverage unknown."

### Vue (`vue`)

```bash
# Vue Router route definitions
find src/router -name "*.ts" -o -name "*.js" 2>/dev/null

# View components
find src/views -name "*.vue" 2>/dev/null

# Or grep for route definitions
grep -rn "path:" src/router/ --include="*.ts" --include="*.js" 2>/dev/null
```

Coverage: count of route definitions in router config. If no router directory, flag as "unknown coverage."

### Python — Django (`django`)

```bash
# URL patterns
find . -name "urls.py" -not -path "*/venv/*" -not -path "*/.venv/*" 2>/dev/null

# Extract URL patterns
grep -rn "path(\|re_path(\|url(" */urls.py --include="*.py" 2>/dev/null

# Views
find . -name "views.py" -not -path "*/venv/*" 2>/dev/null
```

Coverage: count of `path()` / `url()` entries in all `urls.py` files. If no `urls.py` found, flag as "unknown coverage."

### Python — FastAPI (`fastapi`)

```bash
# API route decorators
grep -rn "@app\.\(get\|post\|put\|delete\|patch\)\|@router\.\(get\|post\|put\|delete\|patch\)" . --include="*.py" | grep -v venv

# APIRouter includes
grep -rn "include_router" . --include="*.py" | grep -v venv
```

Coverage: count of route decorators + included routers. If no decorators found, flag as "unknown coverage."

### Go (`go`)

```bash
# HTTP handler registrations
grep -rn "HandleFunc\|Handle(\|http\.Handle\|r\.GET\|r\.POST\|r\.PUT\|r\.DELETE\|r\.PATCH\|Group(" . --include="*.go" | grep -v vendor

# Generated route files (swagger, openapi)
find . -name "*routes*.go" -o -name "*handlers*.go" 2>/dev/null | grep -v vendor
```

Coverage: count of handler registrations. If using generated routes, also count generated files. If no handlers found, flag as "unknown coverage."

### Rust (`rust`)

```bash
# Axum/Actix route macros
grep -rn "#\[axum::routing\|#\[actix_web::\|#\[get(\|#\[post(\|#\[put(\|#\[delete(" src/ --include="*.rs"

# Rocket routes
grep -rn "#\[get(\|#\[post(\|#\[put(\|#\[delete(" src/ --include="*.rs"
```

Coverage: count of route macro invocations. If no macros found, flag as "unknown coverage."

### Ruby — Rails (`rails`)

```bash
# Routes file
cat config/routes.rb 2>/dev/null

# Extract route definitions
grep -n "get\|post\|put\|delete\|patch\|resources\|resource " config/routes.rb 2>/dev/null

# Controllers
find app/controllers -name "*.rb" 2>/dev/null
```

Coverage: count of route definitions in `routes.rb`. If no `routes.rb`, flag as "unknown coverage."

### Java — Spring Boot (`spring`)

```bash
# Controller mappings
grep -rn "@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@PatchMapping" src/ --include="*.java"

# RestController classes
grep -rn "@RestController\|@Controller" src/ --include="*.java"
```

Coverage: count of mapping annotations. If no controllers found, flag as "unknown coverage."

## Coverage Accounting

```
coverage = enumerated_routes / total_possible_routes

If total_possible_routes cannot be determined:
  coverage = "unknown"
  flag = "FAIL-CLOSED: cannot verify 100% coverage"
```

### Coverage States

| State | Meaning | Gate Impact |
|-------|---------|-------------|
| **complete** | All routes enumerated, count verified | Gate can pass on coverage criterion |
| **partial** | Some routes enumerated, count estimated | Gate passes with CONDITIONAL — document gap |
| **unknown** | Route enumeration failed or non-standard structure | Gate FAILS on coverage — must document gap and request manual review |
| **not_applicable** | No routes (e.g., library, CLI tool) | Skip coverage criterion |

## Fail-Closed Inventory Gate

If route enumeration returns "unknown" coverage:

1. Do NOT claim "100% of user-facing routes" in the artifact
2. Document: "Route enumeration returned unknown coverage for [stack]. Manual review required."
3. Gate 1 outcome: CONDITIONAL GO (not GO) — coverage gap is tracked as action item
4. If user can provide route list manually, use that and upgrade to "complete"

## Monorepo Handling

1. Detect all stacks in the monorepo (check each package/workspace)
2. Enumerate routes for each stack separately
3. Aggregate counts: `total_routes = sum(per_stack_routes)`
4. Report per-stack and total coverage
5. If any sub-package has "unknown" coverage, total coverage is "partial"
