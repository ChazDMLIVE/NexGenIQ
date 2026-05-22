/*
 * Authentication screen — sign in, create an account, or reset a password.
 *
 * The first screen an unauthenticated user sees. Calm and minimal, in the
 * Graphite + Sage system (Phase 3.5).
 *
 * Password reset is self-service via a security question (no email is
 * sent): the user enters their email, answers the question they set at
 * registration, and chooses a new password.
 */

import { useState, type FormEvent } from "react";
import { api, type User } from "../lib/api";
import { Button, Card, Field } from "../components/UI";

/* A small curated list of security questions, chosen to favour answers
   that are personal and not easily researched online. Users can also
   write their own. */
const SECURITY_QUESTIONS = [
  "What was the name of the first ranch or farm you worked on?",
  "What is the name of the town where your first cattle were sold?",
  "What was the name of your first horse?",
  "What is your oldest cousin's first name?",
  "What was the make and model of your first truck?",
  "What was the name of your first school?",
];

const CUSTOM_QUESTION = "__custom__";

type Mode = "login" | "register" | "reset";

export function AuthScreen({
  onAuthenticated,
}: {
  onAuthenticated: (user: User) => void;
}) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("producer");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  /* Registration: security question + answer. */
  const [questionChoice, setQuestionChoice] = useState(
    SECURITY_QUESTIONS[0],
  );
  const [customQuestion, setCustomQuestion] = useState("");
  const [securityAnswer, setSecurityAnswer] = useState("");

  /* Password reset is a small two-step flow within the "reset" mode. */
  const [resetStep, setResetStep] = useState<"email" | "answer">("email");
  const [resetQuestion, setResetQuestion] = useState("");
  const [resetAnswer, setResetAnswer] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetNotice, setResetNotice] = useState("");

  /* The actual question text for registration — either the picked one or
     the user's custom wording. */
  const effectiveQuestion =
    questionChoice === CUSTOM_QUESTION
      ? customQuestion.trim()
      : questionChoice;

  function resetAllMessages() {
    setError("");
    setResetNotice("");
  }

  function switchMode(next: Mode) {
    setMode(next);
    resetAllMessages();
    setResetStep("email");
    setResetQuestion("");
    setResetAnswer("");
    setResetNewPassword("");
  }

  /* Sign in / create account. */
  async function submit(e: FormEvent) {
    e.preventDefault();
    resetAllMessages();

    if (mode === "register") {
      if (!effectiveQuestion) {
        setError("Please choose or write a security question.");
        return;
      }
      if (!securityAnswer.trim()) {
        setError("Please answer your security question.");
        return;
      }
    }

    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(
          email,
          password,
          fullName,
          role,
          effectiveQuestion,
          securityAnswer,
        );
      }
      const user = await api.login(email, password);
      onAuthenticated(user);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong.",
      );
    } finally {
      setBusy(false);
    }
  }

  /* Reset step 1: look up the account's security question. */
  async function lookupQuestion(e: FormEvent) {
    e.preventDefault();
    resetAllMessages();
    setBusy(true);
    try {
      const res = await api.passwordResetQuestion(email);
      if (res.has_question) {
        setResetQuestion(res.question);
        setResetStep("answer");
      } else {
        setResetNotice(res.message);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong.",
      );
    } finally {
      setBusy(false);
    }
  }

  /* Reset step 2: verify the answer and set the new password, then sign
     the user straight in. */
  async function confirmReset(e: FormEvent) {
    e.preventDefault();
    resetAllMessages();
    setBusy(true);
    try {
      await api.passwordResetConfirm(email, resetAnswer, resetNewPassword);
      const user = await api.login(email, resetNewPassword);
      onAuthenticated(user);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "That security answer did not match.",
      );
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
          {/* ---- Sign in / Register ---- */}
          {mode !== "reset" && (
            <>
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
                    placeholder="********"
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

                {mode === "register" && (
                  <>
                    <Field
                      label="Security question"
                      hint="Used to reset your password if you forget it.
                            Pick one whose answer only you would know."
                    >
                      <select
                        value={questionChoice}
                        onChange={(e) =>
                          setQuestionChoice(e.target.value)
                        }
                      >
                        {SECURITY_QUESTIONS.map((q) => (
                          <option key={q} value={q}>
                            {q}
                          </option>
                        ))}
                        <option value={CUSTOM_QUESTION}>
                          Write my own question…
                        </option>
                      </select>
                    </Field>

                    {questionChoice === CUSTOM_QUESTION && (
                      <Field label="Your security question">
                        <input
                          type="text"
                          value={customQuestion}
                          onChange={(e) =>
                            setCustomQuestion(e.target.value)
                          }
                          placeholder="A question only you can answer"
                          maxLength={255}
                        />
                      </Field>
                    )}

                    <Field
                      label="Security answer"
                      hint="Capitalisation and spacing are ignored."
                    >
                      <input
                        type="text"
                        value={securityAnswer}
                        onChange={(e) =>
                          setSecurityAnswer(e.target.value)
                        }
                        placeholder="Your answer"
                      />
                    </Field>
                  </>
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

              {mode === "login" && (
                <p className="auth-toggle">
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      switchMode("reset");
                    }}
                  >
                    Forgot your password?
                  </a>
                </p>
              )}

              <p className="auth-toggle">
                {mode === "login" ? (
                  <>
                    New to NexGenIQ?{" "}
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        switchMode("register");
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
                        switchMode("login");
                      }}
                    >
                      Sign in
                    </a>
                  </>
                )}
              </p>
            </>
          )}

          {/* ---- Password reset ---- */}
          {mode === "reset" && (
            <>
              <p className="auth-reset-title">Reset your password</p>

              {resetStep === "email" && (
                <form onSubmit={lookupQuestion}>
                  {error && <p className="auth-error">{error}</p>}
                  {resetNotice && (
                    <p className="auth-notice">{resetNotice}</p>
                  )}
                  <p className="auth-reset-help">
                    Enter your email and we will show the security
                    question you chose when you created your account.
                  </p>
                  <Field label="Email">
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                    />
                  </Field>
                  <Button
                    type="submit"
                    variant="primary"
                    busy={busy}
                    style={{ width: "100%", justifyContent: "center" }}
                  >
                    Continue
                  </Button>
                </form>
              )}

              {resetStep === "answer" && (
                <form onSubmit={confirmReset}>
                  {error && <p className="auth-error">{error}</p>}
                  <Field label="Security question">
                    <input
                      type="text"
                      value={resetQuestion}
                      readOnly
                      className="auth-readonly"
                    />
                  </Field>
                  <Field
                    label="Your answer"
                    hint="Capitalisation and spacing are ignored."
                  >
                    <input
                      type="text"
                      required
                      value={resetAnswer}
                      onChange={(e) => setResetAnswer(e.target.value)}
                      placeholder="Your answer"
                    />
                  </Field>
                  <Field label="New password" hint="At least 8 characters.">
                    <input
                      type="password"
                      required
                      value={resetNewPassword}
                      onChange={(e) =>
                        setResetNewPassword(e.target.value)
                      }
                      placeholder="********"
                    />
                  </Field>
                  <Button
                    type="submit"
                    variant="primary"
                    busy={busy}
                    style={{ width: "100%", justifyContent: "center" }}
                  >
                    Set new password and sign in
                  </Button>
                </form>
              )}

              <p className="auth-toggle">
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    switchMode("login");
                  }}
                >
                  Back to sign in
                </a>
              </p>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
