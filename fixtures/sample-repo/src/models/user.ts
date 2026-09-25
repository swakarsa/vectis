/**
 * Core User Contract (Base version)
 */
export interface User {
  id: string;
  email: string;
  name: string;
  tier: 'free' | 'pro' | 'enterprise';
  createdAt: string;
}

export interface UserPreferences {
  currency: string;
  locale: string;
  notificationsEnabled: boolean;
}
