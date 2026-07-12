import AuthLayout from "../components/AuthLayout";
import LoginForm from "../components/LoginForm";

function Login() {
  return (
    <AuthLayout
      title="Welcome Back"
      subtitle="Login to continue using Atlas."
    >
      <LoginForm />
    </AuthLayout>
  );
}

export default Login;