import { useAuthStore } from "../stores/authStore";
import { login, refreshToken, register } from "./api/chatApi";
import { removeToken, setToken } from "@/utils/cookie";

// Refactor login to handle secure token storage
export const loginUser = async (name: string, password: string) => {
  try {
    const { data } = await login(name, password);
    // Set token securely in cookies
    setToken(data.access_token);
    // Store only non-sensitive user info in Zustand
    useAuthStore.getState().setUser({ name: data.user.username, email: data.user.email });
    return data;
  } catch (error) {
    throw new Error("Login failed");
  }
};

// Logout logic for production
export const logoutUser = () => {
  removeToken();
  useAuthStore.getState().clearUser();
};

export const refreshUser = async () => {
  try {
    const { data } = await refreshToken();
    setToken(data.token);
  } catch (error) {
    // Handle refresh token failure (e.g., redirect to login)
    removeToken();
    useAuthStore.getState().clearUser();
    window.location.href = "/sign-in";
  }
};

export const registerUser = async (name:string, email: string, password: string) => {
  try {
    const { data } = await register(name, email, password);
    return data;
  } catch (error) {
    throw new Error("Register failed");
  }
};
