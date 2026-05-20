/*
 * Authentication screen — sign in or create an account.
 *
 * The first screen an unauthenticated user sees. Calm and minimal, in the
 * Graphite + Sage system (Phase 3.5).
 */

import { useState, type FormEvent } from "react";
import { api, type User } from "../lib/api";
import { Button, Card, Field } from "../components/UI";

export function AuthScreen({
  onAuthenticated,
}: {
  onAuthenticated: (user: User) => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("producer");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(email, password, fullName, role);
      }
      const user = await api.login(email, password);
      onAuthenticated(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="auth-brand">NexGenIQ</p>
        <p className="auth-tagline">
          Selection-index platform for beef cattle
        </p>

        <Card>
          <form onSubmit={submit}>
            {error && <p className="auth-error">{error}</p>}

            {mode === "register" && (
              <Field label="Your name">
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Rancher"
                />
              </Field>
            )}

            <Field label="Email">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </Field>

            <Field
              label="Password"
              hint={
                mode === "register"
                  ? "At least 8 characters."
                  : undefined
              }
            >
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>

            {mode === "register" && (
              <Field
                label="Your role"
                hint="This sets your starting view — you can change it
                      anytime, and it never limits what you can do."
              >
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="producer">Cattle producer</option>
                  <option value="researcher">Researcher</option>
                  <option value="breeder">Seedstock breeder</option>
                  <option value="assoc_admin">
                    Breed-association admin
                  </option>
                </select>
              </Field>
            )}

            <Button
              type="submit"
              variant="primary"
              busy={busy}
              style={{ width: "100%", justifyContent: "center" }}
            >
              {mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <p className="auth-toggle">
            {mode === "login" ? (
              <>
                New to NexGenIQ?{" "}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setMode("register");
                    setError("");
                  }}
                >
                  Create an account
                </a>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setMode("login");
                    setError("");
                  }}
                >
                  Sign in
                </a>
              </>
            )}
          </p>
        </Card>
      </div>
    </div>
  );
}
