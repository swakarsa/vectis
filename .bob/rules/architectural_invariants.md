# Architectural Invariants & Monorepo SemVer Rules

1. **SemVer Contract Integrity:**
   - Any modification to exported types/interfaces in `src/models/` or `src/auth/` that renames or deletes a field is classified as a BREAKING MUTATION.
   - Renaming `id` to `sub` violates downstream caller invariants unless an adapter proxy is provided.

2. **PCI-DSS Compliance Invariant:**
   - Req 10.2.1 requires unbroken audit log identity continuity.
   - Any change dropping `user.id` from transaction contexts triggers an immediate regulatory violation flag.

3. **Deterministic Fail-Closed Policy:**
   - If blast radius encompasses critical domains (`payments/`, `auth/`, `workers/`), merging is hard-blocked until backward compatibility is certified.
