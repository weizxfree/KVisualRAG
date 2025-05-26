import { useState, useEffect } from 'react';

interface LoadingCircleProps {
}

const LoadingCircle: React.FC<LoadingCircleProps> = () => {
  const [progress, setProgress] = useState<number>(0);

  // 模拟进度条加载
  useEffect(() => {
    if (progress < 100) {
      const interval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 1, 99));
      }, 100);
      return () => clearInterval(interval);
    }
  }, [progress]);

  return (
    <div className="relative flex justify-center items-center h-[300px] w-[300px]">
        <div className="flex flex-col items-center">
          {/* 加载圈 */}
          <div className="w-10 h-10 border-4 border-gray-300 border-t-indigo-500 rounded-full animate-spin"></div>
          
          {/* 进度条 */}
          <div className="w-3/4 bg-gray-300 rounded-full h-2 mt-4">
            <div
              className="bg-indigo-500 h-full rounded-full transition-all duration-300 ease-in-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          <p className="mt-2 text-gray-500">{progress}%</p>
        </div>
    </div>
  );
};

export default LoadingCircle;
