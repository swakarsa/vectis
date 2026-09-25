import { getCurrentUser } from "../auth/session";

export async function processPayment(amount: number) {
  const user = await getCurrentUser();

  // BUG 1: user.tier is undefined in PR #482! 20% discount never applied!
  let finalAmount = amount;
  if ((user as any).tier === "enterprise") {
    finalAmount = amount * 0.8;
  }

  // BUG 2: user.id is undefined in PR #482! Crash with Stripe 400 Bad Request
  const customerId = (user as any).id;
  if (!customerId) {
    throw new Error("[CRITICAL OUTAGE] Customer ID is undefined! Cannot charge Stripe token.");
  }

  return {
    status: "charged",
    customerId,
    finalAmount
  };
}
