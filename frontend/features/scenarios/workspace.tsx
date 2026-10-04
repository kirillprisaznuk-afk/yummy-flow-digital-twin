"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api } from "@/api/client";
import type {
  Assumptions,
  Comparison,
  Draft,
  Scenario,
  Slot,
} from "@/types/model";

function useWorkspaceState() {
  const [drafts, setDrafts] = useState<Record<Slot, Draft> | null>(null);
  const [defaults, setDefaults] = useState<Assumptions | null>(null);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [selected, setSelected] = useState<Slot>("baseline");
  const [saved, setSaved] = useState<Scenario[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [storageError, setStorageError] = useState("");
  const [libraryBusy, setLibraryBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const refreshSaved = useCallback(async (offset = 0) => {
    setLibraryBusy(true);
    try {
      const records = await api.list(offset);
      setSaved((previous) => (offset ? [...previous, ...records] : records));
      setHasMore(records.length === 50);
      setStorageError("");
    } catch {
      setStorageError(
        "Saved scenarios could not be loaded. Calculations are still available. Retry the library when storage is restored.",
      );
    } finally {
      setLibraryBusy(false);
    }
  }, []);
  const initialise = useCallback(async () => {
    try {
      const assumptions = await api.defaults();
      const restored: Record<Slot, Draft> = {
        baseline: {
          name: "Madrid · Baseline",
          description: "",
          assumptions: { ...assumptions },
          dirty: false,
        },
        alternative: {
          name: "Madrid · Alternative",
          description: "",
          assumptions: { ...assumptions },
          dirty: false,
        },
      };
      let unavailable = false;
      try {
        const selection = JSON.parse(
          localStorage.getItem("yummy-flow.selection.v1") || "{}",
        );
        for (const slot of ["baseline", "alternative"] as const) {
          if (
            typeof selection[slot] === "string" &&
            /^[0-9a-f-]{36}$/.test(selection[slot])
          ) {
            try {
              const { scenario } = await api.load(selection[slot]);
              restored[slot] = { ...scenario, dirty: false };
            } catch {
              unavailable = true;
            }
          }
        }
        if (
          selection.selected === "baseline" ||
          selection.selected === "alternative"
        )
          setSelected(selection.selected);
      } catch {
        /* Browser storage is optional; persisted scenarios remain in the library. */
      }
      setDefaults(assumptions);
      setDrafts(restored);
      setComparison(
        await api.compare(
          restored.baseline.assumptions,
          restored.alternative.assumptions,
        ),
      );
      if (unavailable)
        setNotice(
          "A previously selected scenario could not be restored. That slot uses synthetic defaults; reload it from the library when available.",
        );
      await refreshSaved();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Unable to load the model. Please retry.",
      );
    } finally {
      setBusy(false);
    }
  }, [refreshSaved]);
  useEffect(() => {
    // Bootstrap synchronizes with HTTP; initialise only sets state after awaited requests.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void initialise();
  }, [initialise]);
  useEffect(() => {
    if (!drafts) return;
    try {
      localStorage.setItem(
        "yummy-flow.selection.v1",
        JSON.stringify({
          baseline: drafts.baseline.id,
          alternative: drafts.alternative.id,
          selected,
        }),
      );
    } catch {
      /* Local browser preferences are optional. */
    }
  }, [drafts, selected]);
  const unsaved = drafts && Object.values(drafts).some((draft) => draft.dirty);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (unsaved) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [unsaved]);
  function edit(slot: Slot, patch: Partial<Draft>) {
    setDrafts(
      (previous) =>
        previous && {
          ...previous,
          [slot]: { ...previous[slot], ...patch, dirty: true },
        },
    );
    if (patch.assumptions) setComparison(null);
    setNotice("");
    setError("");
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Unable to complete this action. Your edits are preserved.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function calculate() {
    if (!drafts) return;
    await run(async () => {
      setComparison(
        await api.compare(
          drafts.baseline.assumptions,
          drafts.alternative.assumptions,
        ),
      );
      setNotice("Both scenarios calculated from the current assumptions.");
    });
  }
  async function save(slot: Slot, replace: boolean) {
    if (!drafts) return;
    const draft = drafts[slot];
    if (
      replace &&
      (!draft.id ||
        !window.confirm(
          `Replace the saved scenario with “${draft.name}” and these assumptions? This updates the stored record.`,
        ))
    )
      return;
    await run(async () => {
      const record = await api.save(
        {
          name: draft.name,
          description: draft.description,
          assumptions: draft.assumptions,
        },
        replace ? draft.id : undefined,
      );
      const other: Slot = slot === "baseline" ? "alternative" : "baseline";
      setDrafts(
        (previous) =>
          previous && {
            ...previous,
            [other]:
              previous[other].id === record.id
                ? {
                    ...previous[other],
                    dirty: true,
                  }
                : previous[other],
            [slot]: { ...record, dirty: false },
          },
      );
      setNotice(replace ? "Saved scenario updated." : "New scenario saved.");
      await refreshSaved();
    });
  }
  async function load(slot: Slot, id: string) {
    if (
      drafts?.[slot].dirty &&
      !window.confirm("Replace the unsaved edits in this scenario?")
    )
      return;
    await run(async () => {
      const { scenario } = await api.load(id);
      setDrafts(
        (previous) =>
          previous && { ...previous, [slot]: { ...scenario, dirty: false } },
      );
      setComparison(null);
      setNotice("Scenario loaded. Calculate to refresh the comparison.");
    });
  }
  function reset(slot: Slot, copyBaseline = false) {
    if (!drafts || !defaults) return;
    if (
      drafts[slot].dirty &&
      !window.confirm("Replace the unsaved edits in this scenario?")
    )
      return;
    setDrafts({
      ...drafts,
      [slot]: {
        name: copyBaseline ? "Baseline copy" : "New scenario",
        description: "",
        assumptions: {
          ...(copyBaseline ? drafts.baseline.assumptions : defaults),
        },
        dirty: true,
      },
    });
    setComparison(null);
    setNotice("");
    setError("");
  }
  async function remove(scenario: Scenario) {
    if (
      !window.confirm(
        `Delete “${scenario.name}” permanently? Any open draft will be retained as unsaved.`,
      )
    )
      return;
    await run(async () => {
      await api.remove(scenario.id);
      setDrafts((previous) => {
        if (!previous) return previous;
        const next = { ...previous };
        for (const slot of ["baseline", "alternative"] as const) {
          if (next[slot].id === scenario.id)
            next[slot] = { ...next[slot], id: undefined, dirty: true };
        }
        return next;
      });
      await refreshSaved();
      setNotice(
        "Scenario deleted. Open assumptions are retained as an unsaved draft.",
      );
    });
  }
  async function importAssumptions(assumptions: Assumptions) {
    if (
      drafts?.[selected].dirty &&
      !window.confirm(
        "Replace the unsaved edits with the validated CSV assumptions?",
      )
    )
      return;
    await run(async () => {
      await api.evaluate(assumptions);
      setDrafts(
        (previous) =>
          previous && {
            ...previous,
            [selected]: {
              name: "Imported synthetic scenario",
              description: "Imported assumptions; illustrative synthetic data.",
              assumptions: { ...assumptions },
              dirty: true,
            },
          },
      );
      setComparison(null);
      setNotice(
        "CSV validated and loaded as an unsaved draft. Calculate to compare; save explicitly to persist it.",
      );
    });
  }
  function retry() {
    setBusy(true);
    setError("");
    void initialise();
  }
  return {
    drafts,
    comparison,
    selected,
    setSelected,
    saved,
    hasMore,
    busy,
    error,
    notice,
    storageError,
    libraryBusy,
    initialise: retry,
    edit,
    calculate,
    save,
    load,
    reset,
    refreshSaved,
    remove,
    importAssumptions,
    reportError: setError,
  };
}
const WorkspaceContext = createContext<ReturnType<
  typeof useWorkspaceState
> | null>(null);
export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const workspace = useWorkspaceState();
  return (
    <WorkspaceContext.Provider value={workspace}>
      {children}
    </WorkspaceContext.Provider>
  );
}
export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("Workspace provider missing");
  return value;
}
