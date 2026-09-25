/**
 * Auth Session Interface - PR #482 (Refactor to OIDC 2.0 Specs)
 * WARNING: Silent Breaking Change for downstream callers!
 */
export interface SessionUser {
  sub: string;
  email: string;
  metadata: {
    tier: 'free' | 'pro' | 'enterprise';
    organizationId: string;
  };
  scopes: string[];
}

export async function getCurrentUser(): Promise<SessionUser> {
  return {
    sub: "usr_9921_oidc",
    email: "enterprise-admin@corp.com",
    metadata: {
      tier: "enterprise",
      organizationId: "org_alpha_01"
    },
    scopes: ["openid", "profile"]
  };
}
