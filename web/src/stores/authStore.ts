import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: null | { name: string; email: string };
  setUser: (user: { name: string; email: string }) => void;
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      clearUser: () => set({ user: null }),
    }),
    {
      name: 'auth-storage', // 存储在 localStorage 中的 key
    }
  )
);
