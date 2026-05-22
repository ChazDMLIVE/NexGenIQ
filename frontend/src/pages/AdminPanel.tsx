/*
 * Admin panel.
 *
 * Visible only to a site_admin account. Three views:
 *   - Users: every registered account, with role / active management.
 *   - Activity: the audit-event log, filterable by event type.
 *   - A per-user drill-in showing that user's submitted (saved) work.
 *
 * Every call here hits an admin-only endpoint; a non-admin never reaches
 * this page because the nav item is not shown for them, and the backend
 * would reject the request anyway.
 */

import { useEffect, useState } from "react";
import {
  api,
  type AdminUser,
  type AuditEvent,
  type AdminSavedItem,
} from "../lib/api";
import { Button, Card, Field } from "../components/UI";

type Tab = "users" | "activity";

const ROLES = [
  "producer",
  "researcher",
  "breeder",
  "assoc_admin",
  "site_admin",
];

const EVENT_TYPES = [
  "",
  "register",
  "login",
  "login_failed",
  "password_reset",
  "index_build",
  "simulation_run",
  "file_import",
  "admin_action",
];

function formatWhen(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export function AdminPanel() {
  const [tab, setTab] = useState<Tab>("users");

  return (
    <main className="main-area">
      <div className="main-content">
        <h1 className="page-title">Admin</h1>
        <p className="page-intro">
          Site administration — registered users, their submitted work,
          and the activity log. Visible only to administrators.
        </p>

        <div className="admin-tabs">
          <button
            type="button"
            className={
              tab === "users"
                ? "admin-tab admin-tab-active"
                : "admin-tab"
            }
            onClick={() => setTab("users")}
          >
            Users
          </button>
          <button
            type="button"
            className={
              tab === "activity"
                ? "admin-tab admin-tab-active"
                : "admin-tab"
            }
            onClick={() => setTab("activity")}
          >
            Activity log
          </button>
        </div>

        {tab === "users" && <UsersView />}
        {tab === "activity" && <ActivityView />}
      </div>
    </main>
  );
}

/* ---- Users -------------------------------------------------------------- */
function UsersView() {
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState("");
  const [openUser, setOpenUser] = useState<AdminUser | null>(null);

  function load() {
    setError("");
    api
      .adminListUsers()
      .then(setUsers)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Could not load users."),
      );
  }

  useEffect(load, []);

  if (error) return <p className="form-error">{error}</p>;
  if (!users) return <p className="docs-body">Loading users…</p>;

  return (
    <>
      <Card title={`Registered users (${users.length})`}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Role</th>
              <th>Status</th>
              <th>Saved</th>
              <th>Joined</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>{u.full_name || "—"}</td>
                <td>{u.role}</td>
                <td>
                  {u.is_active ? (
                    <span className="admin-status-on">Active</span>
                  ) : (
                    <span className="admin-status-off">Disabled</span>
                  )}
                </td>
                <td>{u.saved_item_count}</td>
                <td>{formatWhen(u.created_at)}</td>
                <td>
                  <button
                    type="button"
                    className="prov-why"
                    onClick={() => setOpenUser(u)}
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {openUser && (
        <ManageUser
          user={openUser}
          onClose={() => setOpenUser(null)}
          onChanged={() => {
            load();
            setOpenUser(null);
          }}
        />
      )}
    </>
  );
}

/* ---- Manage one user ---------------------------------------------------- */
function ManageUser({
  user,
  onClose,
  onChanged,
}: {
  user: AdminUser;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [role, setRole] = useState(user.role);
  const [active, setActive] = useState(user.is_active);
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saved, setSaved] = useState<AdminSavedItem[] | null>(null);

  useEffect(() => {
    api
      .adminUserSavedItems(user.id)
      .then(setSaved)
      .catch(() => setSaved([]));
  }, [user.id]);

  async function saveChanges() {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await api.adminUpdateUser(user.id, {
        role,
        is_active: active,
      });
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save changes.");
    } finally {
      setBusy(false);
    }
  }

  async function resetPassword() {
    setError("");
    setNotice("");
    if (newPassword.length < 8) {
      setError("The new password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      await api.adminResetPassword(user.id, newPassword);
      setNewPassword("");
      setNotice("Password reset. Tell the user their new password.");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not reset the password.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title={`Manage ${user.email}`}>
      {error && <p className="form-error">{error}</p>}
      {notice && <p className="auth-notice">{notice}</p>}

      <Field label="Role">
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Account status">
        <select
          value={active ? "active" : "disabled"}
          onChange={(e) => setActive(e.target.value === "active")}
        >
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
        </select>
      </Field>

      <div className="admin-actions">
        <Button variant="primary" busy={busy} onClick={saveChanges}>
          Save changes
        </Button>
        <Button variant="quiet" onClick={onClose}>
          Close
        </Button>
      </div>

      <hr className="admin-divider" />

      <p className="admin-subhead">Reset this user's password</p>
      <p className="docs-body">
        For a user who cannot reset their own password — for example an
        account with no security question on file.
      </p>
      <Field label="New password" hint="At least 8 characters.">
        <input
          type="text"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="New password for this user"
        />
      </Field>
      <Button variant="secondary" busy={busy} onClick={resetPassword}>
        Set new password
      </Button>

      <hr className="admin-divider" />

      <p className="admin-subhead">Submitted work</p>
      {!saved && <p className="docs-body">Loading…</p>}
      {saved && saved.length === 0 && (
        <p className="docs-body">This user has not saved any work.</p>
      )}
      {saved && saved.length > 0 && (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Kind</th>
              <th>Saved</th>
            </tr>
          </thead>
          <tbody>
            {saved.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{s.kind}</td>
                <td>{formatWhen(s.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}

/* ---- Activity log ------------------------------------------------------- */
function ActivityView() {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    setEvents(null);
    api
      .adminActivity(filter)
      .then(setEvents)
      .catch((e) =>
        setError(
          e instanceof Error ? e.message : "Could not load the log.",
        ),
      );
  }, [filter]);

  return (
    <Card title="Activity log">
      <p className="docs-body">
        Recorded actions, newest first. The log captures events from the
        time it was switched on; it cannot show activity from before then.
      </p>

      <Field label="Filter by event type">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t === "" ? "All events" : t}
            </option>
          ))}
        </select>
      </Field>

      {error && <p className="form-error">{error}</p>}
      {!events && !error && (
        <p className="docs-body">Loading activity…</p>
      )}
      {events && events.length === 0 && (
        <p className="docs-body">No events recorded yet.</p>
      )}
      {events && events.length > 0 && (
        <table className="admin-table">
          <thead>
            <tr>
              <th>When</th>
              <th>Event</th>
              <th>User</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td>{formatWhen(e.created_at)}</td>
                <td>{e.event_type}</td>
                <td>{e.user_email || "—"}</td>
                <td>{e.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
