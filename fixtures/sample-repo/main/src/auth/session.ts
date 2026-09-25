/**
 * Auth Session Interface - Base main branch
 */
export interface User {
  id: string;
  email: string;
  tier: 'free' | 'pro' | 'enterprise';
  roles: string[];
}

export async function getCurrentUser(): Promise<User> {
  return {
    id: "usr_9921_legacy",
    email: "enterprise-admin@corp.com",
    tier: "enterprise",
    roles: ["admin", "billing"]
  };
}
