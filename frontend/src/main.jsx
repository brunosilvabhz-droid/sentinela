import React from "react";
import { createRoot } from "react-dom/client";
import LandingAdminPage from "./pages/LandingAdminPage.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import SentinelaApp from "./SentinelaApp.jsx";
import "./styles.css";

function Root() {
  const path = window.location.pathname;
  const hostname = window.location.hostname;
  if (path.startsWith("/landing-admin")) {
    return <LandingAdminPage />;
  }
  if (hostname === "app.impactocg.com" || path.startsWith("/app") || path.startsWith("/ack")) {
    return <SentinelaApp />;
  }
  return <LandingPage />;
}

createRoot(document.getElementById("root")).render(<Root />);
