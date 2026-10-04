export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface CreateAccountInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export type FieldErrors = Partial<Record<keyof CreateAccountInput, string>>;

/** Thrown when the backend rejects a request; carries per-field messages when it sends them. */
export class AuthError extends Error {
  constructor(
    message: string,
    public fieldErrors: FieldErrors = {},
  ) {
    super(message);
  }
}

export const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const MIN_PASSWORD_LENGTH = 8;

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    if (detail && typeof detail === "object" && "errors" in detail) {
      throw new AuthError("Please fix the errors below.", detail.errors as FieldErrors);
    }
    throw new AuthError(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
  }
  return data as T;
}

export function createAccount(input: CreateAccountInput): Promise<User> {
  return postJson<User>("/api/auth/register", input);
}

export function logIn(email: string, password: string): Promise<User> {
  return postJson<User>("/api/auth/login", { email, password });
}

export function logOut(): Promise<unknown> {
  return postJson("/api/auth/logout");
}

export async function fetchCurrentUser(): Promise<User | null> {
  const response = await fetch("/api/auth/me");
  return response.ok ? ((await response.json()) as User | null) : null;
}
