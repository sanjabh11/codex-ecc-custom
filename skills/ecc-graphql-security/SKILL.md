---
name: ecc-graphql-security
description: >-
  Security-focused GraphQL patterns covering introspection attacks, query
  depth/complexity limits, batching abuse, aliasing DoS, field suggestions,
  authorization at resolver level, persisted queries, and N+1 prevention.
  Use for GraphQL API security audits, DoS protection, authz review, or when
  building production GraphQL servers. Triggers: "graphql security",
  "graphql vulnerability", "query depth limit", "introspection attack",
  "graphql dos", "graphql authorization", "batching abuse", "persisted
  queries".
---

# ecc-graphql-security

## When to Use

- Auditing a GraphQL API for security vulnerabilities
- Implementing query depth/complexity limits to prevent DoS
- Reviewing resolver-level authorization (field-level security)
- Preventing introspection attacks in production
- Designing persisted query patterns for client-server security
- Reviewing batching/aliasing abuse vectors

## Vulnerability Catalog

### 1. Introspection Enabled in Production

**Risk:** Attackers can map your entire schema — types, fields, mutations.

**Detection:**
```graphql
# If this returns your schema, introspection is enabled
{
  __schema {
    types {
      name
      fields { name }
    }
  }
}
```

**Mitigation:**
```javascript
// Apollo Server — disable introspection in production
import { ApolloServer } from '@apollo/server';
import { ApolloServerPluginInlineTrace } from '@apollo/server/plugin/inlineTrace';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
  plugins: [
    process.env.NODE_ENV === 'production' && ApolloServerPluginInlineTrace()
  ].filter(Boolean),
});
```

```python
# Strawberry (Python) — disable introspection
import strawberry
from strawberry.extensions import DisableIntrospection

schema = strawberry.Schema(
    query=Query,
    extensions=[DisableIntrospection] if not DEBUG else []
)
```

### 2. Query Depth Attacks (DoS)

**Risk:** Deeply nested queries cause exponential resolver calls.

**Detection:**
```graphql
# Malicious nested query
{
  user(id: 1) {
    friends { friends { friends { friends { friends { name } } } } }
  }
}
```

**Mitigation:**
```javascript
import { createDepthLimitValidator } from 'graphql-depth-limit';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [createDepthLimitValidator(10)],
});
```

```python
# Strawberry — depth limit
from strawberry.extensions import MaxQueryDepthValidator

schema = strawberry.Schema(
    query=Query,
    extensions=[lambda: MaxQueryDepthValidator(max_depth=10)]
)
```

### 3. Query Complexity Attacks (DoS)

**Risk:** Wide queries with many fields cause resource exhaustion.

**Detection:**
```graphql
# 1000 aliases in one query
{
  a1: user(id: 1) { name email }
  a2: user(id: 2) { name email }
  # ... 998 more
}
```

**Mitigation:**
```javascript
import { createComplexityRule } from 'graphql-query-complexity';

const server = new ApolloServer({
  validationRules: [
    createComplexityRule({
      maximumComplexity: 1000,
      variables: {},
      estimators: [fieldExtensionsEstimator(), simpleEstimator({ defaultComplexity: 1 })]
    })
  ],
});
```

### 4. Batching Abuse (DoS)

**Risk:** Clients send hundreds of queries in a single batch request.

**Mitigation:**
```javascript
// Apollo Server — limit batch size
const server = new ApolloServer({
  typeDefs,
  resolvers,
  // Allow max 5 queries per batch
  allowBatchedHttpRequests: true,
  maxQueryBatchSize: 5,
});
```

### 5. Missing Resolver-Level Authorization

**Risk:** Auth checked at query level but not at field/resolver level —
users can access other users' data through nested fields.

**Vulnerable:**
```javascript
const resolvers = {
  Query: {
    user: (_, { id }, context) => context.db.user.findById(id)
    // No authz check — any user can query any user
  },
  User: {
    // No field-level authz — sensitive fields exposed
    email: (parent) => parent.email,
    ssn: (parent) => parent.ssn,
  }
};
```

**Secure:**
```javascript
const resolvers = {
  Query: {
    user: async (_, { id }, context) => {
      if (!context.user) throw new AuthenticationError('Not authenticated');
      const user = await context.db.user.findById(id);
      if (context.user.id !== id && context.user.role !== 'admin') {
        throw new ForbiddenError('Not authorized');
      }
      return user;
    },
  },
  User: {
    email: (parent, _, context) => {
      if (context.user?.id !== parent.id) return null; // field-level redaction
      return parent.email;
    },
    ssn: (parent, _, context) => {
      if (context.user?.role !== 'admin') return null;
      return parent.ssn;
    },
  }
};
```

### 6. Alias-Based DoS

**Risk:** Aliases multiply server-side work in a single request.

**Detection:**
```graphql
{ a: expensiveQuery b: expensiveQuery c: expensiveQuery }
```

**Mitigation:** Use query complexity analysis (see #3) or rate limiting per
field with `graphql-cost-analysis`.

### 7. Field Suggestion Information Leak

**Risk:** GraphQL servers suggest close matches, leaking field names.

**Detection:**
```graphql
# Query a non-existent field
{ user(id: 1) { passwrd } }
# Server responds: "Did you mean 'password'?"
```

**Mitigation:**
```javascript
// Apollo Server — disable suggestions in production
import { ApolloServerErrorCode } from '@apollo/server';

const server = new ApolloServer({
  formatError: (formattedError, error) => {
    if (process.env.NODE_ENV === 'production') {
      // Remove suggestion text in production
      delete formattedError.extensions.suggestion;
    }
    return formattedError;
  },
});
```

### 8. N+1 Query Vulnerability

**Risk:** List queries trigger one DB call per item — performance DoS vector.

**Detection:**
```javascript
// N+1 — each user triggers a separate DB call for posts
const resolvers = {
  User: {
    posts: (parent, _, context) => context.db.posts.find({ userId: parent.id })
    // 100 users = 100 DB calls
  }
};
```

**Mitigation:** Use DataLoader to batch all IDs into a single DB call. See
`graphql-patterns` skill for detailed DataLoader implementation patterns,
batching strategies, and caching configuration. This skill focuses on the
**security implication**: N+1 is a DoS vector that can be exploited by
requesting nested lists with many items.

### 9. Missing Rate Limiting

**Risk:** No rate limiting on GraphQL endpoints allows query flooding.

**Mitigation:**
```javascript
import rateLimit from 'express-rate-limit';

const graphqlLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 queries per minute per IP
  message: 'Too many GraphQL requests',
});

app.use('/graphql', graphqlLimiter);
```

### 10. Persisted Queries Not Enforced

**Risk:** Clients can send arbitrary queries, increasing attack surface.

**Mitigation:**
```javascript
// Apollo Server — persisted queries in production
import { ApolloServerPluginCacheControl } from '@apollo/server/plugin/cacheControl';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  // Only allow persisted query hashes in production
  allowOnlyPersistedQueries: process.env.NODE_ENV === 'production',
});
```

## Security Audit Checklist

- [ ] Introspection disabled in production
- [ ] Query depth limit enforced (recommended: ≤10)
- [ ] Query complexity limit enforced (recommended: ≤1000)
- [ ] Batch size limited (recommended: ≤5)
- [ ] Resolver-level authorization on every field with sensitive data
- [ ] Field-level authz for PII fields (email, SSN, phone)
- [ ] Field suggestions disabled in production
- [ ] DataLoader or equivalent for N+1 prevention
- [ ] Rate limiting on GraphQL endpoint
- [ ] Persisted queries enforced in production
- [ ] Error messages don't leak internal state in production
- [ ] CORS configured to allow only trusted origins
- [ ] Query allowlist for internal/partner APIs

## Integration

- **Router**: `security-skills` and `backend-skills` domain routers
- **Related**: `graphql-patterns` (schema design), `api-design` (REST patterns), `ecc-owasp-security` (API1-API10)
- **Testing**: Use with `e2e-testing` for GraphQL security test automation

## Auto-Revocation

This skill has **no external tool dependencies**. All patterns are markdown
guidance for code review.

- **Core tools** (never gate): `grep`, `cat`, `head` — used for resolver/schema review
- **Advisory tools**: `graphql`, `apollo`, `strawberry` CLIs — if available, use for
  schema introspection checks; if absent, fall back to manual review
- Wrap automated tool calls with `2>/dev/null` and `|| true`

## Cross-IDE Compatibility

Pure markdown skill — no runtime dependencies:
- **Windsurf**: SKILL.md auto-discovered
- **Devin**: SKILL.md injected as context
- **Autogravity**: SKILL.md read as agent capability
- **Codex**: `agents/openai.yaml` provides agent definition

## Upstream Source

Adapted from [aitmpl.com](https://www.aitmpl.com/) GraphQL security agent component and OWASP GraphQL security guidance.
