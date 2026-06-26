import React from "react";
import { createRoot } from "react-dom/client";
import LandingPage from "./pages/LandingPage.jsx";
import SentinelaApp from "./SentinelaApp.jsx";
import "./styles.css";

function Root() {
  const path = window.location.pathname;
  if (path.startsWith("/app") || path.startsWith("/ack")) {
    return <SentinelaApp />;
  }
  return <LandingPage />;
}

createRoot(document.getElementById("root")).render(<Root />);
