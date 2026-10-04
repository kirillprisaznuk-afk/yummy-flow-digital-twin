"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspace } from "@/features/scenarios/workspace";

const navigation = [
  ["/", "Overview", "01"],
  ["/scenarios", "Scenario Lab", "02"],
  ["/operations", "Operations", "03"],
  ["/economics", "Unit Economics", "04"],
  ["/risk", "Risk & Simulation", "05"],
  ["/methodology", "Methodology", "06"],
];
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const workspace = useWorkspace();
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link href="/" className="brand">
          <span className="brand-mark">
            yf<span>.</span>
          </span>
          <span>
            Yummy Flow<small>DIGITAL TWIN</small>
          </span>
        </Link>
        <div className="nav-heading">WORKSPACE</div>
        <nav aria-label="Primary navigation">
          {navigation.map(([href, label, number]) => (
            <Link
              key={href}
              href={href}
              aria-current={pathname === href ? "page" : undefined}
            >
              <span className="nav-number">{number}</span>
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="status-dot" /> Illustrative model
          <p>
            Madrid · Single dark store
            <br />
            EUR · VAT excluded
          </p>
          <span className="small-muted">Portfolio research project</span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Operations intelligence <span className="crumb">/</span>{" "}
            {navigation.find(([href]) => href === pathname)?.[1] ?? "Workspace"}
          </span>
          <span className="synthetic-tag">SYNTHETIC DATA</span>
        </header>
        <main id="main" tabIndex={-1}>
          {workspace.error && (
            <div role="alert" className="alert error">
              <strong>Action couldn’t be completed.</strong>
              <p>{workspace.error}</p>
              {!workspace.drafts && (
                <button
                  onClick={() => void workspace.initialise()}
                  disabled={workspace.busy}
                >
                  Retry connection
                </button>
              )}
            </div>
          )}
          {workspace.notice && (
            <div role="status" className="alert notice">
              {workspace.notice}
            </div>
          )}
          {children}
        </main>
        <footer>
          Yummy Flow Digital Twin{" "}
          <span>
            Illustrative assumptions. Decision support, not a forecast.
          </span>
        </footer>
      </div>
    </div>
  );
}
