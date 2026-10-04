import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import {
  AuthError,
  createAccount,
  EMAIL_PATTERN,
  MIN_PASSWORD_LENGTH,
  type CreateAccountInput,
  type FieldErrors,
} from "../api/auth";
import { useAuth } from "../auth/AuthContext";

const emptyForm: CreateAccountInput = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  confirm_password: "",
};

function validate(form: CreateAccountInput): FieldErrors {
  const errors: FieldErrors = {};
  if (!form.first_name.trim()) errors.first_name = "First name is required.";
  if (!form.last_name.trim()) errors.last_name = "Last name is required.";
  if (!form.email.trim()) errors.email = "Email is required.";
  else if (!EMAIL_PATTERN.test(form.email.trim())) errors.email = "Enter a valid email address.";
  if (!form.password) errors.password = "Password is required.";
  else if (form.password.length < MIN_PASSWORD_LENGTH)
    errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  if (!form.confirm_password) errors.confirm_password = "Please confirm your password.";
  else if (form.password !== form.confirm_password) errors.confirm_password = "Passwords do not match.";
  return errors;
}

const fields: { name: keyof CreateAccountInput; label: string; type: string; autoComplete: string }[] = [
  { name: "first_name", label: "First name", type: "text", autoComplete: "given-name" },
  { name: "last_name", label: "Last name", type: "text", autoComplete: "family-name" },
  { name: "email", label: "Email", type: "email", autoComplete: "email" },
  { name: "password", label: "Password", type: "password", autoComplete: "new-password" },
  { name: "confirm_password", label: "Confirm password", type: "password", autoComplete: "new-password" },
];

export default function CreateAccountPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<CreateAccountInput>(emptyForm);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user && !submitting) return <Navigate to="/account" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    const clientErrors = validate(form);
    setErrors(clientErrors);
    if (Object.keys(clientErrors).length > 0) return;

    setSubmitting(true);
    try {
      const newUser = await createAccount(form);
      setUser(newUser);
      navigate("/account", { replace: true, state: { welcome: true } });
    } catch (err) {
      if (err instanceof AuthError) {
        setErrors(err.fieldErrors);
        setFormError(err.message);
      } else {
        setFormError("Could not reach the server. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <section className="content-card narrow">
      <h1>Create Account</h1>
      {formError && <p className="form-error">{formError}</p>}
      <form className="form" onSubmit={handleSubmit} noValidate>
        {fields.map((field) => (
          <label key={field.name}>
            {field.label}
            <input
              type={field.type}
              name={field.name}
              autoComplete={field.autoComplete}
              value={form[field.name]}
              onChange={(event) => setForm({ ...form, [field.name]: event.target.value })}
              aria-invalid={Boolean(errors[field.name])}
            />
            {errors[field.name] && <span className="field-error">{errors[field.name]}</span>}
          </label>
        ))}
        <button type="submit" className="button" disabled={submitting}>
          {submitting ? "Creating account…" : "Create Account"}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}
