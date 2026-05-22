"use client";

import api from "./api";
import type {
  User,
  LoginCredentials,
  LoginResponse,
  ApiResponse,
} from "./types";

const TOKEN_KEYS = {
  ACCESS: "access_token",
  REFRESH: "refresh_token",
  USER: "user",
} as const;

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await api.post<ApiResponse<LoginResponse>>(
      "/api/auth/login/",
      credentials
    );
    const data = response.data.data!;

    localStorage.setItem(TOKEN_KEYS.ACCESS, data.access);
    localStorage.setItem(TOKEN_KEYS.REFRESH, data.refresh);
    localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(data.user));

    return data;
  },

  async logout(): Promise<void> {
    const refresh = localStorage.getItem(TOKEN_KEYS.REFRESH);
    try {
      await api.post("/api/auth/logout/", { refresh });
    } catch {
      // proceed with local logout even if server call fails
    } finally {
      this.clearSession();
    }
  },

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEYS.ACCESS);
    localStorage.removeItem(TOKEN_KEYS.REFRESH);
    localStorage.removeItem(TOKEN_KEYS.USER);
  },

  async refreshToken(): Promise<string | null> {
    const refresh = localStorage.getItem(TOKEN_KEYS.REFRESH);
    if (!refresh) return null;

    try {
      const response = await api.post<ApiResponse<{ access: string }>>(
        "/api/auth/refresh/",
        { refresh }
      );
      const newAccess = response.data.data!.access;
      localStorage.setItem(TOKEN_KEYS.ACCESS, newAccess);
      return newAccess;
    } catch {
      this.clearSession();
      return null;
    }
  },

  getStoredUser(): User | null {
    if (typeof window === "undefined") return null;
    const stored = localStorage.getItem(TOKEN_KEYS.USER);
    return stored ? JSON.parse(stored) : null;
  },

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEYS.ACCESS);
  },

  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !!this.getStoredUser();
  },

  hasRole(allowedRoles: string[]): boolean {
    const user = this.getStoredUser();
    if (!user) return false;
    return allowedRoles.includes(user.role);
  },
};

export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}
