"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { authService, isTokenExpired } from "./auth";
import type { User, LoginCredentials } from "./types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const checkAuth = useCallback((): boolean => {
    const token = authService.getAccessToken();
    const storedUser = authService.getStoredUser();

    if (!token || !storedUser) {
      setUser(null);
      return false;
    }

    if (isTokenExpired(token)) {
      authService.clearSession();
      setUser(null);
      return false;
    }

    setUser(storedUser);
    return true;
  }, []);

  useEffect(() => {
    checkAuth();
    setIsLoading(false);
  }, [checkAuth]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const response = await authService.login(credentials);
      setUser(response.user);
    },
    []
  );

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
