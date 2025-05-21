"use client";
import Alert from "@/components/Alert";
import { loginUser, registerUser } from "@/lib/auth";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import './page.css';

const SignInPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [pending, setPending] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showAlert, setShowAlert] = useState({
    show: false,
    message: "",
    type: "",
  });

  const router = useRouter(); // 获取 router 实例
  const searchParams = useSearchParams();

  const toggleAuthMode = () => {
    setIsLogin(!isLogin);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPending(true);
    setError("");
    try {
      if (isLogin) {
        await loginUser(name, password);
        setShowAlert({
          show: true,
          message: "Login Success!",
          type: "success",
        });
        // 获取 returnUrl 参数
        const returnUrl = searchParams.get("returnUrl");
        router.push(returnUrl || "/"); // 登录成功后跳转到 returnUrl 或者首页
      } else {
        await registerUser(name, email, password);
        setShowAlert({
          show: true,
          message: "Sign-in Success!",
          type: "success",
        });
        setIsLogin(true);
        // 获取 returnUrl 参数
        const returnUrl = searchParams.get("returnUrl");
        router.push(returnUrl || "/"); // 登录成功后跳转到 returnUrl 或者首页
      }
    } catch (err) {
      console.log(err);
      setError("Invalid credentials");
      setShowAlert({
        show: true,
        message: "Login/Sign-in Failed!",
        type: "error",
      });
    } finally {
      setName("");
      setEmail("");
      setPassword("");
      setPending(false);
    }
  };

  // Automatically hide the alert after 2 seconds
  useEffect(() => {
    if (showAlert.show) {
      const timer = setTimeout(() => {
        setShowAlert({ ...showAlert, show: false });
      }, 5000); // 自动关闭弹窗

      return () => clearTimeout(timer); // 清除计时器，防止内存泄漏
    }
  }, [showAlert]);

  return (
    <div className="login-page">
      {showAlert.show && <Alert showAlert={showAlert} />}
      <div
        className={`login-container`}
      >
        <div
          className={`login-title`}
        >
          <div className="login-title-logo"></div>
          <div className="login-title-text">KnowFlow</div>
        </div>

        <div className="tip">
          {isLogin ? "很高兴再次见到您" : "很高兴您加入"}
        </div>

        <form className="w-full" onSubmit={handleSubmit}>
          <div>
            <input
              id="name"
              name="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              required
              placeholder="请输入账号"
              className={`mt-4 w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:border-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm`}
            />
          </div>

          {!isLogin && (
            <div>
              {/* <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email address
              </label> */}
              <input
                id="email"
                name="email"
                type="email"
                value={email}
                placeholder="请输入邮箱地址"
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                className={`mt-4 w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:border-2 focus:ring-indigo-500 focus:border-indigo-500
                     sm:text-sm`}
              />
            </div>
          )}

          <div>
            {/* <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label> */}
            <input
              id="password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              placeholder="请输入密码"
              className={`mt-4 w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:border-2 "focus:ring-indigo-500 focus:border-indigo-500"
                  focus:ring-slate-600 focus:border-slate-600 sm:text-sm`}
            />
          </div>

          <div>
            <button
              type="submit"
              className={`submit-btn mt-[50px] w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-xs text-sm font-medium text-white
                 cursor-pointer disabled:cursor-not-allowed`}
              disabled={pending}
            >
              {pending ? "进行中..." : isLogin ? "登 录" : "注 册"}
            </button>
          </div>
        </form>

        <div className="text-sm mt-4 text-center">
          {isLogin ? (
            <p>
              没有账号?{" "}
              <button
                onClick={toggleAuthMode}
                className={`font-medium text-indigo-600 hover:text-indigo-500
                     cursor-pointer disabled:cursor-not-allowed`}
                disabled={pending}
              >
                注册
              </button>
            </p>
          ) : (
            <p>
              已有账号?{" "}
              <button
                onClick={toggleAuthMode}
                className={`font-medium text-indigo-600 hover:text-indigo-500 cursor-pointer disabled:cursor-not-allowed`}
                disabled={pending}
              >
                登录
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// 使用 Suspense 包裹整个页面组件
const Page = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <SignInPage />
  </Suspense>
);

export default Page;
