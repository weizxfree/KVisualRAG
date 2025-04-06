"use client";
import Link from "next/link";

const NotFound = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100/80">
      <div className="text-center">
        <h1 className={`text-6xl font-bold "text-indigo-600" mb-4`}>404</h1>
        <p className="text-lg text-gray-700 mb-8">
          Oops! The page you are looking for does not exist.
        </p>
        <Link
          href="/"
          className={`px-4 py-2 text-white rounded-md bg-indigo-600 hover:bg-indigo-700`}
        >
          Go back home
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
