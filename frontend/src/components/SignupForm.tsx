import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { signup } from "../services/auth";
import { useState } from "react";

interface SignupFormData {
  user_name: string;
  email: string;
  password: string;
}

function SignupForm() {
  const navigate = useNavigate();

  const [serverError, setServerError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormData>();

  const onSubmit = async (data: SignupFormData) => {
    try {
      setServerError("");

      await signup(data);

      alert("Account created successfully!");

      navigate("/login");
    } catch (err: any) {
      setServerError(
        err.response?.data?.detail || "Something went wrong."
      );
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>

      <div style={{ marginBottom: "1rem" }}>
        <label>Username</label>

        <input
          {...register("user_name", {
            required: "Username is required",
          })}
          placeholder="Enter username"
          style={inputStyle}
        />

        {errors.user_name && (
          <p style={errorStyle}>{errors.user_name.message}</p>
        )}
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Email</label>

        <input
          type="email"
          {...register("email", {
            required: "Email is required",
          })}
          placeholder="Enter email"
          style={inputStyle}
        />

        {errors.email && (
          <p style={errorStyle}>{errors.email.message}</p>
        )}
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Password</label>

        <input
          type="password"
          {...register("password", {
            required: "Password is required",
            minLength: {
              value: 6,
              message: "Password must be at least 6 characters",
            },
          })}
          placeholder="Enter password"
          style={inputStyle}
        />

        {errors.password && (
          <p style={errorStyle}>{errors.password.message}</p>
        )}
      </div>

      {serverError && (
        <p style={errorStyle}>{serverError}</p>
      )}

      <button
        type="submit"
        style={buttonStyle}
        disabled={isSubmitting}
      >
        {isSubmitting ? "Creating..." : "Create Account"}
      </button>

      <p
        style={{
          textAlign: "center",
          marginTop: "1rem",
        }}
      >
        Already have an account?{" "}
        <Link to="/login">Login</Link>
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
  background: "#2563EB",
  color: "white",
  border: "none",
  borderRadius: "8px",
  cursor: "pointer",
  fontSize: "16px",
};

const errorStyle = {
  color: "red",
  marginTop: "5px",
  fontSize: "14px",
};

export default SignupForm;