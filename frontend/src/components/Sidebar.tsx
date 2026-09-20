import React from "react";

export type NavRoute =
  | "new_project"
  | "my_designs"
  | "inspiration"
  | "catalog"
  | "designpulse"
  | "sustainability"
  | "export";

export type UserRole = "homeowner" | "designer";

interface SidebarProps {
  activeRoute: NavRoute;
  onNavigate: (route: NavRoute) => void;
  userRole: UserRole;
  onToggleUserRole: (role: UserRole) => void;
  savedDesignsCount: number;
  catalogCount: number;
  hasActivePlan: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeRoute,
  onNavigate,
  userRole,
  onToggleUserRole,
  savedDesignsCount,
  catalogCount,
  hasActivePlan,
}) => {
  const navItems: {
    id: NavRoute;
    label: string;
    icon: string;
    badge?: string | number;
    description: string;
    requiresPlan?: boolean;
  }[] = [
    {
      id: "new_project",
      label: hasActivePlan ? "Active Project" : "New Project",
      icon: "📐",
      description: "Room brief & spatial geometry",
    },
    {
      id: "my_designs",
      label: "My Designs",
      icon: "🗂",
      badge: savedDesignsCount > 0 ? savedDesignsCount : undefined,
      description: "Saved bathroom concepts",
    },
    {
      id: "inspiration",
      label: "Inspiration",
      icon: "✨",
      description: "KOHLER style directions",
    },
    {
      id: "catalog",
      label: "Product Catalog",
      icon: "📦",
      badge: catalogCount > 0 ? `${catalogCount}` : undefined,
      description: "Fixtures & fittings",
    },
    {
      id: "designpulse",
      label: "DesignPulse™",
      icon: "⚡",
      badge: "AI",
      description: "Change consequence engine",
      requiresPlan: true,
    },
    {
      id: "sustainability",
      label: "Sustainability",
      icon: "💧",
      description: "Water & energy intelligence",
      requiresPlan: true,
    },
    {
      id: "export",
      label: "Export & Share",
      icon: "📄",
      description: "Client & Dealer BOM packages",
      requiresPlan: true,
    },
  ];

  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      {/* Brand Header */}
      <div className="sidebar-brand-header">
        <div className="brand-badge-sidebar">
          <div className="brand-logo-text">KOHLER</div>
          <div className="brand-sub-text">AI BATHPLAN</div>
        </div>
        <p className="sidebar-tagline">Imagine. Plan. Live Better.</p>
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">WORKSPACE</div>
        <ul className="sidebar-menu">
          {navItems.map((item) => {
            const isActive = activeRoute === item.id;
            const isDisabled = item.requiresPlan && !hasActivePlan;

            return (
              <li key={item.id} className="sidebar-menu-item">
                <button
                  type="button"
                  className={`sidebar-nav-btn ${isActive ? "active" : ""} ${
                    isDisabled ? "disabled" : ""
                  }`}
                  onClick={() => !isDisabled && onNavigate(item.id)}
                  disabled={isDisabled}
                  title={isDisabled ? "Generate a plan to unlock this tool" : item.description}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span className="sidebar-nav-icon">{item.icon}</span>
                  <div className="sidebar-nav-text">
                    <span className="sidebar-nav-label">{item.label}</span>
                    <span className="sidebar-nav-sub">{item.description}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`sidebar-badge ${
                        item.badge === "AI" ? "badge-ai" : "badge-counter"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom User Mode & System Context */}
      <div className="sidebar-footer">
        {/* Role Toggle Switcher */}
        <div className="role-switch-container">
          <div className="role-switch-header">
            <span className="role-label-title">PLANNING EXPERIENCE</span>
            <span className="role-current-badge">
              {userRole === "homeowner" ? "Homeowner" : "Architect / Designer"}
            </span>
          </div>
          <div className="role-toggle-pills" role="radiogroup" aria-label="Experience Mode">
            <button
              type="button"
              className={`role-pill-btn ${userRole === "homeowner" ? "selected" : ""}`}
              onClick={() => onToggleUserRole("homeowner")}
              title="Friendly, clear language with progressive technical disclosure"
              aria-checked={userRole === "homeowner"}
              role="radio"
            >
              Homeowner
            </button>
            <button
              type="button"
              className={`role-pill-btn ${userRole === "designer" ? "selected" : ""}`}
              onClick={() => onToggleUserRole("designer")}
              title="Full architectural clearances, millimeter tolerances, and code specs"
              aria-checked={userRole === "designer"}
              role="radio"
            >
              Designer
            </button>
          </div>
          <p className="role-helper-text">
            {userRole === "homeowner"
              ? "Plain-language explanations & guided decisions."
              : "Advanced dimensional tolerances & engineering rules."}
          </p>
        </div>

        {/* System Meta */}
        <div className="sidebar-system-meta">
          <div className="system-status-indicator">
            <span className="system-dot" />
            <span className="system-text">Verified Deterministic Solver</span>
          </div>
          <div className="system-version">KOHLER Studio · v1.0 Production</div>
        </div>
      </div>
    </aside>
  );
};
