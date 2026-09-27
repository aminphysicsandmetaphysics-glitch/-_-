import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { api, setAuthToken } from "../api/client";
import { User } from "../types/audit";

const TOKEN_KEY = "energy_audit_token";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    setAuthToken(token);
    api
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setAuthToken(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      localStorage.setItem(TOKEN_KEY, access_token);
      setAuthToken(access_token);
      setUser(await api.me());
    } catch {
      setError("ایمیل یا رمز عبور نادرست است.");
      throw new Error("login_failed");
    }
  }

  async function register(email: string, password: string, fullName: string) {
    setError(null);
    try {
      await api.register(email, password, fullName);
      await login(email, password);
    } catch {
      setError("ثبت‌نام ناموفق بود. شاید این ایمیل قبلاً ثبت شده است.");
      throw new Error("register_failed");
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, error, login, register, logout }), [user, loading, error]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
