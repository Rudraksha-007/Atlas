import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../services/auth";
import { useState } from "react";

interface LoginFormData {
  email: string;
  password: string;
}

function LoginForm() {
  const navigate = useNavigate();

  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>();

  const onSubmit = async (data: LoginFormData) => {
    try {
      setServerError("");

      const response = await login(data);

      localStorage.setItem(
        "accessToken",
        response.access_token
      );

      localStorage.setItem(
        "refreshToken",
        response.refresh_token
      );

      navigate("/dashboard");
    } catch (err: any) {
      setServerError(
        err.response?.data?.detail ||
          "Invalid credentials"
      );
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>

      <div style={{ marginBottom: "1rem" }}>
        <label>Email</label>

        <input
          type="email"
          {...register("email", {
            required: "Email is required",
          })}
          style={inputStyle}
        />

        {errors.email && (
          <p style={errorStyle}>
            {errors.email.message}
          </p>
        )}
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Password</label>

        <input
          type="password"
          {...register("password", {
            required: "Password is required",
          })}
          style={inputStyle}
        />

        {errors.password && (
          <p style={errorStyle}>
            {errors.password.message}
          </p>
        )}
      </div>

      {serverError && (
        <p style={errorStyle}>{serverError}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        style={buttonStyle}
      >
        {isSubmitting ? "Logging in..." : "Login"}
      </button>

      <p
        style={{
          marginTop: "1rem",
          textAlign: "center",
        }}
      >
        Don't have an account?{" "}
        <Link to="/signup">
          Sign Up
        </Link>
      </p>

    </form>
  );
}

const inputStyle = {
  width: "100%",
  padding: "12px",
  marginTop: "6px",
  borderRadius: "8px",
  border: "1px solid #D1D5DB",
  boxSizing: "border-box" as const,
};

const buttonStyle = {
  width: "100%",
  padding: "12px",
  borderRadius: "8px",
  border: "none",
  background: "#2563EB",
  color: "white",
  cursor: "pointer",
};

const errorStyle = {
  color: "red",
  fontSize: "14px",
};

export default LoginForm;