import { useState } from "react";
import { useAuth } from "../lib/auth";

export function AuthScreen() {
  const { login, register, error } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
    } catch {
      /* error already surfaced via context */
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="sidebar-brand" style={{ borderBottom: "none", marginBottom: 8, padding: 0 }}>
          <div className="sidebar-brand-mark" />
          <div>
            <strong>ممیزی هوشمند انرژی</strong>
            <span>Residential Energy Audit Platform</span>
          </div>
        </div>
        <h1>{mode === "login" ? "ورود به حساب کاربری" : "ساخت حساب کاربری"}</h1>
        <p style={{ marginBottom: 20 }}>
          {mode === "login" ? "برای دسترسی به پروژه‌های ممیزی خود وارد شوید." : "برای شروع ممیزی خانه‌های خود ثبت‌نام کنید."}
        </p>
        <div className="auth-toggle">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
            ورود
          </button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">
            ثبت‌نام
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-grid" style={{ gridTemplateColumns: "1fr", gap: 12 }}>
            {mode === "register" && (
              <div className="field">
                <label>نام کامل</label>
                <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="امین" />
              </div>
            )}
            <div className="field">
              <label>ایمیل</label>
              <input className="input ltr-num" type="email" required dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div className="field">
              <label>رمز عبور</label>
              <input className="input ltr-num" type="password" required dir="ltr" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="حداقل ۸ کاراکتر" />
            </div>
          </div>
          {error && <p className="alert error" style={{ marginTop: 14 }}>{error}</p>}
          <button className="btn btn-primary btn-block" style={{ marginTop: 18 }} disabled={busy} type="submit">
            {busy ? "..." : mode === "login" ? "ورود" : "ایجاد حساب"}
          </button>
        </form>
      </div>
    </div>
  );
}
