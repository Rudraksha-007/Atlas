import AuthLayout from "../components/AuthLayout";
import SignupForm from "../components/SignupForm";

function Signup() {
  return (
    <AuthLayout
      title="Create Account"
      subtitle="Join Atlas and start managing your digital capsules."
    >
      <SignupForm />
    </AuthLayout>
  );
}

export default Signup;