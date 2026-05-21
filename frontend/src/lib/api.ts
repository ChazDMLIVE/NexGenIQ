/*
 * NexGenIQ API client.
 *
 * A small typed wrapper around the FastAPI backend (Phase 3 Part 3C
 * Section 3.4). It holds the JWT in memory, attaches it to every request,
 * and surfaces backend errors as plain Error objects the UI can display.
 */

// NexGenIQ API client — covers the Index Builder and Herd Simulation.
//
// In development the Vite dev server proxies "/api" to the local backend,
// so a relative base works. In a deployment the frontend and backend are
// on different hosts, so the backend URL is supplied at build time via
// VITE_API_BASE_URL (e.g. "https://nexgeniq-api.up.railway.app").
const API_ROOT = import.meta.env.VITE_API_BASE_URL ?? "";
const BASE = `${API_ROOT}/api/v1`;

/* In-memory auth token. Not persisted to storage — a page reload requires
 * signing in again. (Token persistence is a later hardening step.) */
let authToken: string | null = null;

export function setToken(token: string | null): void {
  authToken = token;
}

export function getToken(): string | null {
  return authToken;
}

/* ----------------------------------------------------------------------
 * Shared types — mirror the backend Pydantic schemas.
 * -------------------------------------------------------------------- */
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface Trait {
  code: string;
  name: string;
  category: string;
  units: string;
  higher_is_better: boolean;
  is_threshold: boolean;
  /** Breed associations that publish this trait's EPD. Empty = universal;
      a non-empty list (e.g. PAP) means the trait is breed-restricted. */
  breeds: string[];
  description: string;
}

export interface GoalComponent {
  trait_code: string;
  economic_weight: number;
}

export interface BreedingGoal {
  name: string;
  basis: string;
  components: GoalComponent[];
  source?: string;
}

export interface Epd {
  trait_code: string;
  value: number;
  bif_accuracy: number | null;
  scale?: string;
}

export interface Animal {
  animal_id: string;
  breed: string;
  evaluation_id?: string;
  sex?: string;
  epds: Epd[];
}

export interface IndexBuildRequest {
  goal: BreedingGoal;
  animals: Animal[];
  parameter_set_id?: string | null;
  mode: string;
  missing_policy?: string;
  adjustment_table_id?: string | null;
  native_multi_breed?: boolean;
}

export interface ValidationIssue {
  severity: "error" | "warn" | "info";
  code: string;
  message: string;
  fix_hint: string;
  location: string;
}

export interface AnimalScore {
  rank: number;
  animal_id: string;
  breed: string;
  index_value: number;
  std_error: number | null;
  ci_low: number | null;
  ci_high: number | null;
  contributions: Record<string, number>;
  is_partial: boolean;
  explanation: string;
}

export interface IndexBuildResponse {
  ok: boolean;
  mode: string;
  weights: Record<string, number>;
  scores: AnimalScore[];
  excluded: string[];
  validation: ValidationIssue[];
  adjustment_table_version: string;
  ledger_id: string | null;
}

export interface TornadoEntry {
  trait_code: string;
  rank_corr_low: number;
  rank_corr_high: number;
  top_changed: boolean;
}

/* ---- economic-value estimator ---- */
export interface EstimatorQuestion {
  key: string;
  prompt: string;
  help_text: string;
  default: number;
  units: string;
  minimum: number;
  maximum: number;
}

export interface EstimatorRecipe {
  trait_code: string;
  questions: EstimatorQuestion[];
  formula_text: string;
  basis_note: string;
}

export interface EstimateResult {
  trait_code: string;
  economic_value: number;
  formula_text: string;
  basis_note: string;
  inputs_used: Record<string, number>;
}

/* ---- herd simulation (Milestone 2) ---- */
export interface BreedCompositionIn {
  fraction: number;
  breeds: Record<string, number>;
}

export interface PriceBandIn {
  sex: string;
  low: number;
  high: number;
  price_per_cwt: number;
}

export interface GridCellIn {
  quality_grade: string;
  yield_grade: number;
  premium: number;
}

export interface ProductionSystemIn {
  name: string;
  herd_size: number;
  conception_rate: number;
  calving_loss_rate: number;
  replacement_rate: number;
  heifer_retention: boolean;
  cow_breed_composition: BreedCompositionIn[];
  bull_breed_composition: BreedCompositionIn[];
}

export interface EconomicScenarioIn {
  name: string;
  sale_endpoint: string;
  price_bands: PriceBandIn[];
  carcass_base_price?: number;
  grid?: GridCellIn[];
  cull_cow_price_per_cwt: number;
  aum_cost: number;
  feed_cost_per_lb_dm?: number;
  background_days?: number;
  days_on_feed?: number;
  fixed_cost_per_cow: number;
  discount_rate: number;
  /** Ranch elevation, ft above sea level. Drives PAP's economic weight. */
  elevation_ft?: number;
  /** Cost to rear an own heifer to first calving. */
  replacement_development_cost?: number;
  /** Cost to buy a bred replacement female. */
  purchased_replacement_cost?: number;
  /** Economic loss when a productive cow dies. */
  value_of_lost_animal?: number;
}

export interface SimulationControlsIn {
  burn_in_years: number;
  planning_horizon_years: number;
  replicates: number;
  seed: number;
}

export interface SimulationRequest {
  production_system: ProductionSystemIn;
  economic_scenario: EconomicScenarioIn;
  controls: SimulationControlsIn;
  traits: string[];
}

export interface DerivedMev {
  trait_code: string;
  units: string;
  mev: number;
  mc_std_error: number;
  is_precise: boolean;
}

export interface SimulationResponse {
  baseline_profit: number;
  replicates: number;
  mevs: DerivedMev[];
  warnings: string[];
}

export interface SensitivityResponse {
  baseline_top: string;
  summary: string;
  entries: TornadoEntry[];
}

/* ----------------------------------------------------------------------
 * Core request helper.
 * -------------------------------------------------------------------- */
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    /* Surface the backend's plain-language detail where available. */
    let detail = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* non-JSON error body — keep the generic message */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/* ----------------------------------------------------------------------
 * Endpoint methods.
 * -------------------------------------------------------------------- */
export const api = {
  /** Register a new account. */
  async register(
    email: string,
    password: string,
    fullName: string,
    role: string,
  ): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        role,
      }),
    });
  },

  /** Exchange credentials for a JWT; stores the token on success. */
  async login(email: string, password: string): Promise<User> {
    /* The OAuth2 password flow expects form-encoded fields. */
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${BASE}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) {
      throw new Error("Incorrect email or password.");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data.user as User;
  },

  /** List the trait registry. */
  async traits(): Promise<Trait[]> {
    return request<Trait[]>("/library/traits");
  },

  /** Build a selection index and rank animals. */
  async buildIndex(
    req: IndexBuildRequest,
  ): Promise<IndexBuildResponse> {
    return request<IndexBuildResponse>("/index/build", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /** Run tornado sensitivity analysis on an index. */
  async sensitivity(
    req: IndexBuildRequest & { variation: number },
  ): Promise<SensitivityResponse> {
    return request<SensitivityResponse>("/index/sensitivity", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /** Run a herd simulation and derive marginal economic values. */
  async deriveMevs(
    req: SimulationRequest,
  ): Promise<SimulationResponse> {
    return request<SimulationResponse>("/simulation/derive-mevs", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /** Fetch the economic-value estimator recipes (questions + formulas). */
  async econEstimatorRecipes(): Promise<EstimatorRecipe[]> {
    return request<EstimatorRecipe[]>("/library/econ-estimator/recipes");
  },

  /** Estimate the economic value of one trait from plain-language answers. */
  async estimateEconValue(
    traitCode: string,
    answers: Record<string, number>,
  ): Promise<EstimateResult> {
    return request<EstimateResult>("/library/econ-estimator/estimate", {
      method: "POST",
      body: JSON.stringify({ trait_code: traitCode, answers }),
    });
  },

  /** Inspect an uploaded CSV and get a proposed column mapping. */
  async inspectCsv(file: File): Promise<{
    filename: string;
    row_count: number;
    columns: {
      source_column: string;
      target_field: string;
      confidence: string;
    }[];
    preview_rows: Record<string, string>[];
  }> {
    const form = new FormData();
    form.append("file", file);
    return request("/import/inspect", { method: "POST", body: form });
  },

  /** Parse a CSV with a confirmed column mapping into animal records. */
  async parseCsv(
    file: File,
    mapping: Record<string, string>,
  ): Promise<{
    animal_count: number;
    animals: Animal[];
    problems: string[];
  }> {
    const form = new FormData();
    form.append("file", file);
    form.append("mapping_json", JSON.stringify(mapping));
    return request("/import/parse", { method: "POST", body: form });
  },
};
