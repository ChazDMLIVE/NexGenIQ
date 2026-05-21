/*
 * NexGenIQ application shell.
 *
 * Holds the authentication state, the top bar, and routes between the
 * Index Builder, the Herd Simulation wizard, and the Troubleshooting
 * page. The HelpProvider and the shared ContextPanel wrap the whole
 * authenticated app so any InfoTip can drive the one explanation panel
 * (Phase 3.5 Part 3).
 *
 * The simulation -> index hand-off is coordinated here: when the
 * simulation wizard derives economic values, the App routes the user to
 * the Index Builder pre-loaded with those values as a breeding goal.
 */

// NexGenIQ frontend — Milestone 2 (Index Builder + Herd Simulation).
import { useState } from "react";
import { type GoalComponent, type User, setToken } from "./lib/api";
import { HelpProvider } from "./components/Help";
import { AuthScreen } from "./pages/AuthScreen";
import { IndexBuilder } from "./pages/IndexBuilder";
import { SimulationWizard } from "./pages/SimulationWizard";
import { Troubleshooting } from "./pages/Troubleshooting";
import { TechnicalDocs } from "./pages/TechnicalDocs";
import { HowToUse } from "./pages/HowToUse";
import { SavedWork } from "./pages/SavedWork";
import { Logo } from "./components/Logo";

type Route =
  | "builder"
  | "simulation"
  | "saved"
  | "howto"
  | "troubleshooting"
  | "techdocs";

/* Economic weights handed from the simulation to the Index Builder. */
export interface DerivedGoal {
  name: string;
  components: GoalComponent[];
}

/* The top-bar navigation items, in display order. */
const NAV_ITEMS: { route: Route; label: string }[] = [
  { route: "builder", label: "Index Builder" },
  { route: "simulation", label: "Herd Simulation" },
  { route: "saved", label: "My Saved Work" },
  { route: "howto", label: "How to Use" },
  { route: "techdocs", label: "Technical Docs" },
  { route: "troubleshooting", label: "Help" },
];

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [route, setRoute] = useState<Route>("builder");

  /* When the simulation derives a goal, it is stashed here and the
   * Index Builder consumes it on mount. */
  const [derivedGoal, setDerivedGoal] = useState<DerivedGoal | null>(
    null,
  );

  if (!user) {
    return <AuthScreen onAuthenticated={setUser} />;
  }

  function signOut() {
    setToken(null);
    setUser(null);
    setRoute("builder");
    setDerivedGoal(null);
  }

  /* The simulation -> index integration hand-off. */
  function handleUseInIndex(
    components: GoalComponent[],
    name: string,
  ) {
    setDerivedGoal({ name, components });
    setRoute("builder");
  }

  return (
    <HelpProvider>
      <div className="app-shell">
        <header className="topbar">
          <button
            type="button"
            className="topbar-logo-btn"
            onClick={() => setRoute("builder")}
            aria-label="NexGenIQ home"
          >
            <Logo size={26} />
          </button>

          <nav className="topbar-nav">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.route}
                type="button"
                className={
                  route === item.route
                    ? "topbar-link topbar-link-active"
                    : "topbar-link"
                }
                onClick={() => setRoute(item.route)}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="topbar-user-group">
            <span className="topbar-user">
              {user.full_name || user.email}
            </span>
            <button
              type="button"
              className="topbar-signout"
              onClick={signOut}
            >
              Sign out
            </button>
          </div>
        </header>

        {route === "builder" && (
          <IndexBuilder
            derivedGoal={derivedGoal}
            onDerivedGoalConsumed={() => setDerivedGoal(null)}
          />
        )}
        {route === "simulation" && (
          <SimulationWizard onUseInIndex={handleUseInIndex} />
        )}
        {route === "saved" && (
          <SavedWork onUseGoal={handleUseInIndex} />
        )}
        {route === "howto" && <HowToUse />}
        {route === "techdocs" && <TechnicalDocs />}
        {route === "troubleshooting" && <Troubleshooting />}
      </div>
    </HelpProvider>
  );
}
