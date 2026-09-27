import React from "react";
import ReactDOM from "react-dom/client";
import "vazirmatn/Vazirmatn-Variable-font-face.css";
import App from "./App";
import { AuthProvider } from "./lib/auth";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>,
);
