"use client";

import { useAuth } from "@/lib/auth-context";

interface NavbarProps {
  onMenuToggle: () => void;
}

export default function Navbar({ onMenuToggle }: NavbarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 lg:px-6">
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 rounded-lg hover:bg-gray-100 text-gray-600"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className="flex-1" />

      <div className="flex items-center space-x-4">
        {user && (
          <span className="text-sm text-gray-600 hidden sm:block">
            {user.first_name} {user.last_name}
          </span>
        )}
        <button
          onClick={logout}
          className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-150"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span className="hidden sm:block">Logout</span>
        </button>
      </div>
    </header>
  );
}
