const USER_ID_KEY = "agent_user_id";
const EXPIRES_DAYS = 365;

function generateUserId(): string {
  return crypto.randomUUID();
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name: string, value: string, days: number): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

export function getUserId(): string {
  let userId = getCookie(USER_ID_KEY);
  if (!userId) {
    userId = generateUserId();
    setCookie(USER_ID_KEY, userId, EXPIRES_DAYS);
  }
  return userId;
}
