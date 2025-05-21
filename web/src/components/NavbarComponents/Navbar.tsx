import Link from "next/link";
import UserMenuExpand from "./UserMenuExpand";
import { useRouter,usePathname } from "next/navigation";
import './navbar.css'

const Navbar = () => {
  const pathName = usePathname(); // 获取 pathname
  const navbarButtonStyle = `flex flex-col items-center gap-2 p-2`;
  return (
    <div className="navbar-box z-10 w-[60px] h-full flex flex-col justify-between items-center">
      <div className="h-[200px]">
        <div className={navbarButtonStyle}>
          <Link href="/" className="font-bold text-sm">
            <div className="logo">
            </div>
          </Link>
        </div>
        <div className={navbarButtonStyle}>
          <Link href="/ai-chat" className="font-bold text-sm flex flex-col items-center">
            <div className={pathName === '/ai-chat' ? 'chat-icon-active icon' : 'chat-icon icon'}>
            </div>
            <div className="navbar-text">
              聊天
            </div>
          </Link>
        </div>

        <div className={navbarButtonStyle}>
          <Link href="/knowledge-base" className="font-bold text-sm flex flex-col items-center">
            <div className={pathName === '/knowledge-base' ? 'know-icon-active icon' : 'know-icon icon'}>
            </div>
            <div className="navbar-text">
              知识库
            </div>
          </Link>
        </div>

        {/* <div className={navbarButtonStyle}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="size-5"
          >
            <path
              fillRule="evenodd"
              d="M3.25 3A2.25 2.25 0 0 0 1 5.25v9.5A2.25 2.25 0 0 0 3.25 17h13.5A2.25 2.25 0 0 0 19 14.75v-9.5A2.25 2.25 0 0 0 16.75 3H3.25Zm.943 8.752a.75.75 0 0 1 .055-1.06L6.128 9l-1.88-1.693a.75.75 0 1 1 1.004-1.114l2.5 2.25a.75.75 0 0 1 0 1.114l-2.5 2.25a.75.75 0 0 1-1.06-.055ZM9.75 10.25a.75.75 0 0 0 0 1.5h2.5a.75.75 0 0 0 0-1.5h-2.5Z"
              clipRule="evenodd"
            />
          </svg>

          <Link
            href="/ai-chat"
            onClick={() => {
              window.confirm("coming soon...");
            }}
            className="font-bold text-sm"
          >
            Agent
          </Link>
        </div> */}

       
      </div>
      <div className="flex-1 flex flex-col justify-end">
        <UserMenuExpand />
      </div>
  </div>
  );
};

export default Navbar;
