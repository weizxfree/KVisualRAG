"use client";
import { useAuthStore } from "../stores/authStore";
import { verifyToken } from "../lib/api/chatApi";
import Cookies from "js-cookie";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Alert from "@/components/Alert";

const withAuth = (WrappedComponent: any) => {
  const AuthComponent = (props: any) => {
    const router = useRouter();
    const { user, clearUser } = useAuthStore();
    const [isCheckingAuth, setIsCheckingAuth] = useState(true); // 用于跟踪身份验证状态
    const [response, setResponse] = useState({ username: "" }); // 用于跟踪身份验证状态

    useEffect(() => {
      const checkAuth = async () => {
        const token = Cookies.get("token");
        if (!token) {
          const returnUrl = encodeURIComponent(window.location.pathname); // 保存当前路径
          router.push(`/sign-in?returnUrl=${returnUrl}`);
          return;
        }

        try {
          const { data } = await verifyToken();
          setResponse(data);
          //setUser({ name: data.user.username, email: data.user.email });
        } catch (err) {
          Cookies.remove("token");
          clearUser();
          const returnUrl = encodeURIComponent(window.location.pathname); // 保存当前路径
          router.push(`/sign-in?returnUrl=${returnUrl}`);
        } finally {
          setIsCheckingAuth(false); // 验证完成
        }
      };

      checkAuth();
    }, [router, clearUser, user?.name]);

    useEffect(() => {
      if (!isCheckingAuth && response.username !== user?.name) {
        const returnUrl = encodeURIComponent(window.location.pathname); // Save current path
        router.push(`/sign-in?returnUrl=${returnUrl}`);
      }
    }, [isCheckingAuth, response.username, router, user?.name]);

    // 在身份验证完成之前显示加载状态
    if (isCheckingAuth) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100 opacity-80">
          <Alert
            showAlert={{
              show: true,
              message: "check login state...",
              type: "success",
            }}
          />
        </div>
      );
    }

    // 如果用户已登录，渲染目标页面
    return <WrappedComponent {...props} />;
  };

  return AuthComponent;
};

export default withAuth;
