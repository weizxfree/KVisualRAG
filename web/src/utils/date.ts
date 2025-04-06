export const getTimeLabel = (lastModifyAt: string): string => {
  const now = new Date();
  const localOffset = now.getTimezoneOffset() * 60000; // 当前时区与UTC的偏移，单位为毫秒
  const beijingOffset = 8 * 60 * 60 * 1000; // 北京时间与UTC的偏移，单位为毫秒

  // 获取当前北京时间的日期对象
  const beijingNow = new Date(now.getTime() + localOffset + beijingOffset);
  
  // 获取今天和昨天的开始时间（北京时间）
  const todayStart = new Date(beijingNow.getFullYear(), beijingNow.getMonth(), beijingNow.getDate());
  const yesterdayStart = new Date(todayStart.getTime() - 24 * 60 * 60 * 1000); // 昨天0点

  const lastModifyDate = new Date(lastModifyAt); // 直接使用 ISO 字符串创建日期对象
  const timeDiff = lastModifyDate.getTime() + 8 * 60 * 60 * 1000; // 获取最后修改时间的毫秒数

  if (timeDiff >= todayStart.getTime()) {
      return "Today";
  } else if (timeDiff >= yesterdayStart.getTime()) {
      return "Yesterday";
  } else if (timeDiff >= todayStart.getTime() - 7 * 24 * 60 * 60 * 1000) {
      return "Within 7 days";
  } else if (timeDiff >= todayStart.getTime() - 30 * 24 * 60 * 60 * 1000) {
      return "Within 30 days";
  } else {
      return "Earlier";
  }
};
