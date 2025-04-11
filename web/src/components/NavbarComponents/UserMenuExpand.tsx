"use client";

import Link from "next/link";
import { useState } from "react";
import Image from "next/image";
import { logoutUser } from "@/lib/auth";
import { useAuthStore } from "@/stores/authStore";

const UserMenuExpand = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserInfoOpen, setIsUserInfoOpen] = useState(false);
  const { user } = useAuthStore();

  return (
    <div className="fixed right-[2%] gap-3 h-8 flex items-center justify-between px-6 border-indigo-500">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="currentColor"
        className="size-8 text-indigo-500 cursor-pointer"
        onClick={() => setIsUserInfoOpen((prev) => !prev)}
      >
        <path
          fillRule="evenodd"
          d="M18.685 19.097A9.723 9.723 0 0 0 21.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 0 0 3.065 7.097A9.716 9.716 0 0 0 12 21.75a9.716 9.716 0 0 0 6.685-2.653Zm-12.54-1.285A7.486 7.486 0 0 1 12 15a7.486 7.486 0 0 1 5.855 2.812A8.224 8.224 0 0 1 12 20.25a8.224 8.224 0 0 1-5.855-2.438ZM15.75 9a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"
          clipRule="evenodd"
        />
      </svg>

      {/* <Image
        src={"/noAvatar.png"}
        alt=""
        width={24}
        height={24}
        className="cursor-pointer w-6 h-6 object-cover rounded-xs"
        onClick={() => setIsUserInfoOpen((prev) => !prev)}
      /> */}
      <div
        className="flex flex-col gap-[4.5px] cursor-pointer"
        onClick={() => setIsMenuOpen((prev) => !prev)}
      >
        <div
          className={`w-6 h-1 bg-indigo-500 rounded-xs ${
            isMenuOpen ? "rotate-45" : ""
          } origin-left ease-in-out duration-500`}
        />
        <div
          className={`w-6 h-1 bg-indigo-500 rounded-xs ${
            isMenuOpen ? "opacity-0" : ""
          } ease-in-out duration-500`}
        />
        <div
          className={`w-6 h-1 bg-indigo-500 rounded-xs ${
            isMenuOpen ? "-rotate-45" : ""
          } origin-left ease-in-out duration-500`}
        />
      </div>
      {isMenuOpen && (
        <div className="z-20 bg-white/100 shadow-2xl absolute left-0 top-10 w-full h-[calc(20vh-98px)] flex flex-col items-center justify-center gap-[10%] font-medium text-sm rounded-3xl">
          <div
            className="cursor-pointer text-red-400 font-semibold"
            onClick={logoutUser}
          >
            Log out
          </div>
        </div>
      )}
      {isUserInfoOpen && (
        <div className="p-6 z-20 bg-white/100 shadow-2xl absolute right-0 top-10 flex flex-col items-start justify-center gap-4 font-medium text-sm rounded-3xl">
          <div className="whitespace-nowrap">Username: {user?.name}</div>
          <div className="whitespace-nowrap">Email: {user?.email}</div>
        </div>
      )}
    </div>
  );
};

export default UserMenuExpand;
