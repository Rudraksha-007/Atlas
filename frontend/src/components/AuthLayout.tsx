import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

function AuthLayout({
  title,
  subtitle,
  children,
}: AuthLayoutProps) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* Left Section */}
      <div
        style={{
          background: "#111827",
          color: "white",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "4rem",
        }}
      >
        <h1
          style={{
            fontSize: "3rem",
            marginBottom: "1rem",
          }}
        >
          Atlas
        </h1>

        <p
          style={{
            fontSize: "1.2rem",
            color: "#D1D5DB",
            lineHeight: "1.8",
          }}
        >
          Securely manage your digital capsules and access them from
          anywhere.
        </p>
      </div>

      {/* Right Section */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          background: "#F9FAFB",
        }}
      >
        <div
          style={{
            width: "420px",
            background: "white",
            padding: "2.5rem",
            borderRadius: "16px",
            boxShadow: "0 10px 30px rgba(0,0,0,.08)",
          }}
        >
          <h2>{title}</h2>

          <p
            style={{
              color: "#6B7280",
              marginBottom: "2rem",
            }}
          >
            {subtitle}
          </p>

          {children}
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;