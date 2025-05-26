"use client";
import { useAuthStore } from "@/stores/authStore";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const Homepage = () => {
  const { user } = useAuthStore();
  const router = useRouter(); // 获取 router 实例
  const [userLoaded, setUserLoaded] = useState(false);

  useEffect(() => {
    // When the component mounts or user state changes, set userLoaded to true
    setUserLoaded(true);
  }, [user]);

  if (!userLoaded) {
    return null; // Optionally, you could return a loading indicator here
  } 

  if (user && user.name) {
    window.location.href = "/ai-chat";
  } else {
    window.location.href = "/sign-in";
  }
  
  // router.push("/sign-in");
  // window.location.href = "/sign-in";

  return (
    <></>
  );
};

export default Homepage;
