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

type Route = "builder" | "simulation" | "troubleshooting" | "techdocs";

/* Economic weights handed from the simulation to the Index Builder. */
export interface DerivedGoal {
  name: string;
  components: GoalComponent[];
}

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
          <span className="topbar-brand">NexGenIQ</span>
          <span className="topbar-sub">
            {route === "builder"
              ? "Index Builder"
              : route === "simulation"
                ? "Herd Simulation"
                : route === "techdocs"
                  ? "Technical Documentation"
                  : "Troubleshooting"}
          </span>
          <span className="topbar-spacer" />
          <a
            href="#"
            className="topbar-link"
            onClick={(e) => {
              e.preventDefault();
              setRoute("builder");
            }}
          >
            Index Builder
          </a>
          <a
            href="#"
            className="topbar-link"
            onClick={(e) => {
              e.preventDefault();
              setRoute("simulation");
            }}
          >
            Herd Simulation
          </a>
          <a
            href="#"
            className="topbar-link"
            onClick={(e) => {
              e.preventDefault();
              setRoute("techdocs");
            }}
          >
            Technical Docs
          </a>
          <a
            href="#"
            className="topbar-link"
            onClick={(e) => {
              e.preventDefault();
              setRoute("troubleshooting");
            }}
          >
            Help
          </a>
          <span className="topbar-user">
            {user.full_name || user.email}
          </span>
          <a
            href="#"
            className="topbar-link"
            onClick={(e) => {
              e.preventDefault();
              signOut();
            }}
          >
            Sign out
          </a>
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
        {route === "techdocs" && <TechnicalDocs />}
        {route === "troubleshooting" && <Troubleshooting />}
      </div>
    </HelpProvider>
  );
}
