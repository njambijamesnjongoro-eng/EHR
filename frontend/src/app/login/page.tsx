"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import LoadingSpinner from "@/components/ui/loading-spinner";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { message?: string } } };
        setError(
          axiosErr.response?.data?.message || "Invalid email or password"
        );
      } else {
        setError("An error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">EHR</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">MediRecord EHR</h1>
          <p className="text-gray-500 mt-1">
            Hospital Electronic Health Record System
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Sign in to your account
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="doctor@hospital.com"
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Secure hospital system &mdash; authorized access only
        </p>
      </div>
    </div>
  );
}
