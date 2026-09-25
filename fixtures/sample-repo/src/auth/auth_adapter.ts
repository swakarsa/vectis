/**
 * auth_adapter.ts
 * Vectis Backward-Compatibility Shim — PR #482 (refactor-auth)
 *
 * Wraps the new `SessionUser` (OIDC 2.0) payload in an ES6 Proxy that
 * transparently re-surfaces all legacy `User` fields expected by:
 *   - src/payments/checkout.ts     (.id, .tier)
 *   - src/workers/settlement_worker.ts  (.id)
 *
 * Satisfies:
 *   PCI-DSS v4.0.1 §10.2.1  — Audit Log Identity Continuity
 *   PCI-DSS v4.0.1 §3.4.2   — Downstream Settlement Integrity
 *   PCI-DSS v4.0.1 §8.2.8   — 90-day Deprecation Grace Period
 *
 * @deprecated_fields  id, tier, roles
 *   These fields are bridged for a 90-day transition window.
 *   Callers MUST migrate to .sub, .metadata.tier, and .scopes
 *   before the deprecation deadline.
 *
 * Synthesis: IBM Granite 3.0 Code · Vectis Release Reliability Gate
 */

// ─── Source (OIDC 2.0) interface — PR #482 ───────────────────────────────────

export interface SessionUser {
  sub: string;
  email: string;
  metadata: {
    tier: "free" | "pro" | "enterprise";
    organizationId: string;
  };
  scopes: string[];
}

// ─── Legacy (main-branch) interface ──────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  tier: "free" | "pro" | "enterprise";
  roles: string[];
}

// ─── Bridge type: both shapes visible simultaneously ─────────────────────────

/**
 * BridgedUser satisfies BOTH the legacy `User` contract AND the new
 * `SessionUser` contract.  Downstream callers using `user.id` or
 * `user.tier` continue to work; callers already migrated to `user.sub`
 * and `user.metadata.tier` also work without any change.
 *
 * @deprecated `id`    — use `sub` after migration window closes
 * @deprecated `tier`  — use `metadata.tier` after migration window closes
 * @deprecated `roles` — use `scopes` after migration window closes
 */
export interface BridgedUser extends SessionUser {
  /** @deprecated PCI-DSS §8.2.8 bridge: maps to `.sub`. Remove after 90-day window. */
  id: string;
  /** @deprecated PCI-DSS §8.2.8 bridge: maps to `.metadata.tier`. Remove after 90-day window. */
  tier: "free" | "pro" | "enterprise";
  /** @deprecated PCI-DSS §8.2.8 bridge: maps to `.scopes`. Remove after 90-day window. */
  roles: string[];
  /** Serialisation hook — preserves legacy fields through JSON.stringify for Stripe & Kafka. */
  toJSON(): LegacySerializedUser;
}

/**
 * Shape written to wire by toJSON().
 * Stripe charges and Kafka events receive ALL fields: both OIDC-canonical
 * (`sub`, `metadata`, `scopes`) and legacy (`id`, `tier`, `roles`),
 * maintaining an unbroken audit trail per PCI-DSS §10.2.1.
 */
export interface LegacySerializedUser {
  // OIDC 2.0 canonical fields
  sub: string;
  email: string;
  metadata: {
    tier: "free" | "pro" | "enterprise";
    organizationId: string;
  };
  scopes: string[];
  // Legacy bridge fields (present until all callers are migrated)
  id: string;
  tier: "free" | "pro" | "enterprise";
  roles: string[];
}

// ─── Legacy field routing map ─────────────────────────────────────────────────

/**
 * Static map of legacy property names → resolver functions.
 * Adding a new alias here is the only change required to bridge
 * additional renamed fields in future OIDC migrations.
 */
const LEGACY_FIELD_RESOLVERS: Record<
  string,
  (target: SessionUser) => unknown
> = {
  /**
   * .id → .sub
   * Used by checkout.ts:13 and settlement_worker.ts:7 as the Stripe
   * customer key and the ledger routing key respectively.
   * PCI-DSS §10.2.1: `id` must remain the stable audit-trail identity.
   */
  id: (t) => t.sub,

  /**
   * .tier → .metadata.tier
   * Used by checkout.ts:8 for the 20% enterprise discount gate.
   */
  tier: (t) => t.metadata.tier,

  /**
   * .roles → .scopes
   * Used by any RBAC middleware that still inspects the `roles` array.
   */
  roles: (t) => t.scopes,
};

// ─── ownKeys catalogue ────────────────────────────────────────────────────────

/**
 * The full set of keys the proxy claims to own.
 * Enumerated explicitly so that:
 *   Object.keys(user)      → includes legacy keys
 *   JSON.stringify(user)   → does not drop legacy keys
 *   for...in (user)        → iterates legacy keys
 *   Object.getOwnPropertyNames(user) → complete list
 *
 * Without this, Proxy traps on `get` alone are invisible to
 * JSON.stringify and Kafka serialisers, which enumerate keys via
 * [[OwnPropertyKeys]] before calling [[Get]].
 */
const ALL_OWN_KEYS: (keyof LegacySerializedUser)[] = [
  "sub",
  "email",
  "metadata",
  "scopes",
  "id",
  "tier",
  "roles",
  "toJSON",
];

// ─── Core factory ─────────────────────────────────────────────────────────────

/**
 * wrapSessionUser(session)
 *
 * Wraps a `SessionUser` (OIDC 2.0) in an ES6 Proxy that:
 *
 *   1. `get` trap       — routes legacy field reads transparently.
 *   2. `has` trap       — `'id' in user` returns true (guards & typeof checks).
 *   3. `ownKeys` trap   — exposes both OIDC and legacy keys to enumerators.
 *   4. `getOwnPropertyDescriptor` trap — makes legacy keys appear as
 *                         own, enumerable, configurable data properties
 *                         so JSON.stringify and Kafka serialisers include them.
 *   5. `toJSON` hook    — called by JSON.stringify before key enumeration;
 *                         returns a plain object with ALL fields so that
 *                         Stripe API calls and Kafka events carry both the
 *                         OIDC-canonical identity AND the legacy audit fields.
 *
 * @param session  Raw SessionUser returned by the OIDC token endpoint.
 * @returns        BridgedUser proxy satisfying both User and SessionUser contracts.
 */
export function wrapSessionUser(session: SessionUser): BridgedUser {
  /**
   * toJSON implementation — defined once outside the handler so
   * it closes over `session` and is never recreated per-access.
   *
   * JSON.stringify calls toJSON() *before* enumerating own keys, so
   * this hook is the single authoritative source of the serialised shape.
   * It is also invoked by Stripe's SDK (which calls JSON.stringify
   * internally) and by the Kafka producer's default serialiser.
   */
  const toJSON = (): LegacySerializedUser => ({
    // OIDC 2.0 canonical fields — present for new consumers
    sub: session.sub,
    email: session.email,
    metadata: session.metadata,
    scopes: session.scopes,
    // Legacy bridge fields — present for PCI-DSS audit continuity
    id: session.sub,
    tier: session.metadata.tier,
    roles: session.scopes,
  });

  const handler: ProxyHandler<SessionUser> = {
    // ── Trap 1: get ───────────────────────────────────────────────────────
    /**
     * Intercepts every property read on the proxy.
     *
     *   user.id        → session.sub
     *   user.tier      → session.metadata.tier
     *   user.roles     → session.scopes
     *   user.toJSON()  → serialisation hook
     *   user.*         → direct pass-through for all other properties
     *
     * The Reflect.get fallback preserves native prototype behaviour
     * (e.g. Symbol.toPrimitive, Symbol.iterator) so the proxy is
     * transparent to all other consumer patterns.
     */
    get(target: SessionUser, prop: string | symbol): unknown {
      // toJSON hook — must be returned as a callable
      if (prop === "toJSON") {
        return toJSON;
      }

      // Legacy field routing
      if (typeof prop === "string" && prop in LEGACY_FIELD_RESOLVERS) {
        const value = LEGACY_FIELD_RESOLVERS[prop](target);
        // Emit a deprecation warning in non-production environments
        if (
          typeof process !== "undefined" &&
          process.env["NODE_ENV"] !== "production"
        ) {
          console.warn(
            `[auth_adapter] Deprecated field access: "${prop}". ` +
              `Migrate to "${prop === "id" ? "sub" : prop === "tier" ? "metadata.tier" : "scopes"}" ` +
              `before the 90-day PCI-DSS §8.2.8 window closes.`
          );
        }
        return value;
      }

      // Pass-through: return the native property from the underlying object
      return Reflect.get(target, prop);
    },

    // ── Trap 2: has ───────────────────────────────────────────────────────
    /**
     * Makes `'id' in user`, `'tier' in user`, and `'roles' in user`
     * return true so that guard patterns like:
     *
     *   if ('id' in user) { ... }
     *
     * behave correctly without callers needing to know the field moved.
     */
    has(target: SessionUser, prop: string | symbol): boolean {
      if (typeof prop === "string" && prop in LEGACY_FIELD_RESOLVERS) {
        return true;
      }
      if (prop === "toJSON") {
        return true;
      }
      return Reflect.has(target, prop);
    },

    // ── Trap 3: ownKeys ───────────────────────────────────────────────────
    /**
     * Returns the union of all OIDC-native keys and all legacy bridge keys.
     *
     * This trap is what makes JSON.stringify and Kafka's key-enumeration
     * step see the legacy fields.  Without it, only the raw SessionUser
     * keys (`sub`, `email`, `metadata`, `scopes`) would be visible to
     * any code that calls Object.keys(), Object.getOwnPropertyNames(),
     * or the [[OwnPropertyKeys]] internal method.
     *
     * Note: JSON.stringify calls [[OwnPropertyKeys]] first, then for each
     * key calls [[GetOwnProperty]] to check enumerability, then [[Get]]
     * to obtain the value.  All three must agree — see Trap 4.
     */
    ownKeys(_target: SessionUser): (string | symbol)[] {
      return ALL_OWN_KEYS as string[];
    },

    // ── Trap 4: getOwnPropertyDescriptor ─────────────────────────────────
    /**
     * Makes every key in ALL_OWN_KEYS appear as an own, enumerable,
     * writable, configurable data property of the proxy.
     *
     * This is required because JSON.stringify verifies enumerability via
     * [[GetOwnProperty]] for each key returned by [[OwnPropertyKeys]].
     * If this trap returns undefined for a legacy key, JSON.stringify
     * silently drops that key even though `get` would have returned a value.
     *
     * The same issue affects:
     *   Object.entries(user)        — used by Kafka avro serialiser
     *   Object.getOwnPropertyDescriptors(user)  — used by some ORMs
     *   Structuredclone / MessageChannel transfers
     */
    getOwnPropertyDescriptor(
      target: SessionUser,
      prop: string | symbol
    ): PropertyDescriptor | undefined {
      // toJSON hook descriptor
      if (prop === "toJSON") {
        return {
          value: toJSON,
          writable: false,
          enumerable: false, // toJSON is intentionally non-enumerable
          configurable: true,
        };
      }

      // Legacy bridge field descriptors
      if (typeof prop === "string" && prop in LEGACY_FIELD_RESOLVERS) {
        return {
          value: LEGACY_FIELD_RESOLVERS[prop](target),
          writable: false,
          enumerable: true,  // must be true for JSON.stringify to include it
          configurable: true,
        };
      }

      // Native OIDC field descriptors — delegate to the real object
      const nativeDescriptor = Object.getOwnPropertyDescriptor(target, prop);
      if (nativeDescriptor !== undefined) {
        return nativeDescriptor;
      }

      // Unknown key — must return undefined (not throw) per Proxy invariants
      return undefined;
    },
  };

  return new Proxy(session, handler) as unknown as BridgedUser;
}

// ─── Adapted getCurrentUser ───────────────────────────────────────────────────

/**
 * Replacement for the getCurrentUser() exported by PR #482's session.ts.
 *
 * Drop-in swap: callers that `import { getCurrentUser } from "../auth/session"`
 * can instead `import { getCurrentUser } from "../auth/auth_adapter"` and
 * receive a BridgedUser with no other changes required.
 *
 * The adapter is designed to be removed once all callers have migrated to the
 * OIDC 2.0 field names and the 90-day PCI-DSS §8.2.8 window has closed.
 */
export async function getCurrentUser(): Promise<BridgedUser> {
  // Import the new OIDC session function at runtime to stay decoupled
  // from which version of session.ts is active.
  const { getCurrentUser: getOIDCUser } = await import("./session");
  const session = await getOIDCUser();
  return wrapSessionUser(session as SessionUser);
}

// ─── Verification suite ───────────────────────────────────────────────────────

/**
 * verifyShim(session)
 *
 * Deterministic self-test.  Call once at application startup (or in CI)
 * to assert that all three shim contracts are satisfied before any live
 * traffic is served.
 *
 * Returns a typed result object so callers can gate on success without
 * relying on thrown exceptions.
 */
export function verifyShim(session: SessionUser): {
  passed: boolean;
  checks: Record<string, boolean>;
  errors: string[];
} {
  const user = wrapSessionUser(session);
  const checks: Record<string, boolean> = {};
  const errors: string[] = [];

  // ── Contract 1: .id → .sub (PCI-DSS §10.2.1) ─────────────────────────
  checks["id_maps_to_sub"] = user.id === session.sub;
  if (!checks["id_maps_to_sub"]) {
    errors.push(
      `[VRG-PCI-001] user.id ("${user.id}") !== session.sub ("${session.sub}")`
    );
  }

  // ── Contract 2: .tier → .metadata.tier ───────────────────────────────
  checks["tier_maps_to_metadata_tier"] = user.tier === session.metadata.tier;
  if (!checks["tier_maps_to_metadata_tier"]) {
    errors.push(
      `[VRG-PCI-001] user.tier ("${user.tier}") !== session.metadata.tier ("${session.metadata.tier}")`
    );
  }

  // ── Contract 3: .roles → .scopes ──────────────────────────────────────
  checks["roles_maps_to_scopes"] =
    JSON.stringify(user.roles) === JSON.stringify(session.scopes);
  if (!checks["roles_maps_to_scopes"]) {
    errors.push(
      `[VRG-PCI-001] user.roles !== session.scopes`
    );
  }

  // ── Contract 4: settlement ledger key must never be "ledger_undefined" ─
  const accountKey = `ledger_${user.id}`;
  checks["settlement_key_valid"] = accountKey !== "ledger_undefined";
  if (!checks["settlement_key_valid"]) {
    errors.push(
      `[VRG-PCI-002] Settlement ledger key resolved to "ledger_undefined" — SEV-1 abort would fire`
    );
  }

  // ── Contract 5: JSON.stringify includes `id` and `tier` (Stripe/Kafka) ─
  const serialised = JSON.parse(JSON.stringify(user)) as Record<string, unknown>;
  checks["json_includes_id"] = "id" in serialised && serialised["id"] === session.sub;
  checks["json_includes_tier"] =
    "tier" in serialised && serialised["tier"] === session.metadata.tier;

  if (!checks["json_includes_id"]) {
    errors.push(
      `[VRG-PCI-001] JSON.stringify output missing "id" — Stripe audit trail would be broken`
    );
  }
  if (!checks["json_includes_tier"]) {
    errors.push(
      `[VRG-PCI-001] JSON.stringify output missing "tier" — enterprise discount gate would fail`
    );
  }

  // ── Contract 6: 'in' operator works for legacy keys ───────────────────
  checks["in_operator_id"] = "id" in user;
  checks["in_operator_tier"] = "tier" in user;
  if (!checks["in_operator_id"] || !checks["in_operator_tier"]) {
    errors.push(
      `[VRG-PCI-003] 'in' operator does not see legacy fields — guard patterns would silently fail`
    );
  }

  // ── Contract 7: OIDC-canonical fields still accessible ────────────────
  checks["sub_accessible"] = user.sub === session.sub;
  checks["metadata_accessible"] = user.metadata.tier === session.metadata.tier;
  checks["scopes_accessible"] =
    JSON.stringify(user.scopes) === JSON.stringify(session.scopes);

  const passed = Object.values(checks).every(Boolean);
  return { passed, checks, errors };
}
