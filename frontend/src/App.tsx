import { useEffect, useState } from "react";
import { ApiError, api, formatMoney, type PlanRequest } from "./api";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { BathroomPlanSVG } from "./components/BathroomPlanSVG";
import { BriefForm } from "./components/BriefForm";
import { CandidateCard } from "./components/CandidateCard";
import { ConflictPanel } from "./components/ConflictPanel";
import { ModifyPanel } from "./components/ModifyPanel";
import { WaterPanel } from "./components/WaterPanel";
import type { ModifyResponse, PlanResponse, VisionEvidence } from "./types";

export default function App() {
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<{
    catalog_size: number;
    vision_available: boolean;
    llm_available: boolean;
  } | null>(null);

  const [pendingImage, setPendingImage] = useState<File | null>(null);
  const [vision, setVision] = useState<VisionEvidence | null>(null);
  const [visionError, setVisionError] = useState<string | null>(null);
  const [history, setHistory] = useState<ModifyResponse[]>([]);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() =>
        setError(
          "The planning service is not reachable. Start the backend with: uvicorn backend.main:app --reload",
        ),
      );
  }, []);

  const run = async <T,>(work: () => Promise<T>): Promise<T | null> => {
    setBusy(true);
    setError(null);
    try {
      return await work();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Something went wrong.");
      return null;
    } finally {
      setBusy(false);
    }
  };

  const handlePlan = async (request: PlanRequest) => {
    const result = await run(() => api.createPlan(request));
    if (!result) return;
    setPlan(result);
    setSelected(0);
    setHistory([]);
    if (pendingImage && result.meta.vision_available) {
      analyseImage(result.project_id, pendingImage);
    }
  };

  const analyseImage = async (projectId: string, file: File) => {
    setVisionError(null);
    try {
      setVision(await api.analyseImage(projectId, file));
    } catch (caught) {
      setVision(null);
      setVisionError(
        caught instanceof ApiError ? caught.message : "Image analysis failed.",
      );
    }
  };

  const handleResolve = async (body: Record<string, unknown>) => {
    if (!plan) return;
    const result = await run(() => api.resolve(plan.project_id, body));
    if (result) {
      setPlan(result);
      setSelected(0);
    }
  };

  const handleModify = async (message: string) => {
    if (!plan) return;
    const result = await run(() => api.modify(plan.project_id, message));
    if (result) {
      setPlan(result.plan);
      setSelected(0);
      setHistory((prev) => [...prev, result]);
    }
  };

  const candidate = plan?.candidates[selected] ?? null;

  return (
    <div className="app">
      <header className="masthead">
        <div>
          <h1>KOHLER AI BathPlan</h1>
          <p className="tagline">
            The AI can imagine a bathroom. The constraint engine decides whether it
            survives reality.
          </p>
        </div>
        {health && (
          <div className="status-strip">
            <span className="status-ok">Planner ready · {health.catalog_size} products</span>
            <span className={health.vision_available ? "status-ok" : "status-off"}>
              Vision {health.vision_available ? "on" : "off"}
            </span>
            <span className={health.llm_available ? "status-ok" : "status-off"}>
              AI language layer {health.llm_available ? "on" : "off"}
            </span>
          </div>
        )}
      </header>

      {error && (
        <div className="banner banner-error" role="alert">
          {error}
        </div>
      )}

      <main className="layout">
        <div className="column column-input">
          <BriefForm
            onSubmit={handlePlan}
            onImageSelected={(file) => {
              setPendingImage(file);
              if (plan) analyseImage(plan.project_id, file);
            }}
            busy={busy}
            visionAvailable={health?.vision_available ?? false}
            imageName={pendingImage?.name ?? null}
          />
        </div>

        <div className="column column-output">
          {!plan && !busy && (
            <section className="panel placeholder">
              <h2>No plan yet</h2>
              <p>
                Enter your room dimensions and budget, then generate a plan. Every result
                is checked against physical clearances, your budget, product compatibility
                and installation requirements before it is shown to you.
              </p>
            </section>
          )}

          {plan && <AnalysisPanel meta={plan.meta} vision={vision} visionError={visionError} />}

          {plan?.status === "no_fully_compliant_configuration" && plan.conflict && (
            <ConflictPanel
              conflict={plan.conflict}
              brief={plan.brief}
              onResolve={handleResolve}
              busy={busy}
            />
          )}

          {plan && plan.candidates.length > 0 && (
            <section className="panel">
              <h2>3 · Options that work</h2>
              <p className="hint">
                {plan.candidates.length} configuration(s) passed every hard constraint.
                {plan.brief.budget !== null && (
                  <> Budget: {formatMoney(plan.brief.budget, plan.brief.currency)}.</>
                )}
              </p>
              <div className="cards">
                {plan.candidates.map((item, index) => (
                  <CandidateCard
                    key={index}
                    candidate={item}
                    selected={index === selected}
                    onSelect={() => setSelected(index)}
                  />
                ))}
              </div>
            </section>
          )}

          {candidate && (
            <section className="panel">
              <h2>4 · Bathroom plan</h2>
              <BathroomPlanSVG layout={candidate.layout} />
            </section>
          )}

          {candidate && <WaterPanel water={candidate.water_impact} />}

          {plan && (
            <ModifyPanel
              onSend={handleModify}
              busy={busy}
              history={history}
              llmAvailable={health?.llm_available ?? false}
            />
          )}
        </div>
      </main>

      <footer className="footer">
        <p>
          Prototype for the KOHLER–MIT-WPU AI Research Lab. Product data is illustrative
          and is not KOHLER pricing or verified specification. Concepts shown are
          preliminary planning guidance — final dimensions, plumbing, electrical,
          structural and local-code requirements must be verified by a qualified
          professional before installation.
        </p>
      </footer>
    </div>
  );
}
