// 格式化 label
const formatLabel = (key) => {
  const words = key.split(/(?=[A-Z])/);
  return words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};

// 使用 Moment.js 将 n 个月转换为 x 年 y 月的代码：
function convertMonthsToYearsAndMonths(months) {
  const duration = moment.duration(months, 'months');
  const years = Math.floor(duration.asYears());
  const remainingMonths = Math.floor(duration.asMonths()) % 12;
  return `${years}年${remainingMonths}月`;
}
