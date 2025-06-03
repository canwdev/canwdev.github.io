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

  let result = ''
  if (years !== 0) {
    result += `${years}年`
  }
  if (remainingMonths !== 0) {
    result += `${remainingMonths}月`
  }
  if (!result) {
    result = '初始'
  }
  return result;
}

/** 数字金额大写转换(可以处理整数,小数,负数) */
function numberToChineseMoney(n) {
  var fraction = ['角', '分'];
  var digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
  var unit = [['元', '万', '亿'], ['', '拾', '佰', '仟']];
  var head = n < 0 ? '欠' : '';
  n = Math.abs(n);

  var s = '';

  for (var i = 0; i < fraction.length; i++) {
    s += (digit[Math.floor(n * 10 * Math.pow(10, i)) % 10] + fraction[i]).replace(/零./, '');
  }
  s = s || '整';
  n = Math.floor(n);

  for (var i = 0; i < unit[0].length && n > 0; i++) {
    var p = '';
    for (var j = 0; j < unit[1].length && n > 0; j++) {
      p = digit[n % 10] + unit[1][j] + p;
      n = Math.floor(n / 10);
    }
    s = p.replace(/(零.)*零$/, '').replace(/^$/, '零') + unit[0][i] + s;
  }
  return head + s.replace(/(零.)*零元/, '元').replace(/(零.)+/g, '零').replace(/^整$/, '零元整');
}

function numberWithCommas(num, decimalPlaces = 2) {
  const numStr = Number(num).toFixed(decimalPlaces); // 将数值转换为字符串并控制小数点位数
  const [integerPart, fractionalPart] = numStr.split('.'); // 分割整数和小数部分

  const formattedIntegerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ','); // 使用正则表达式将整数部分用逗号分隔

  if (fractionalPart) {
    return `${formattedIntegerPart}.${fractionalPart}`; // 如果有小数部分，则将整数和小数部分连接起来
  } else {
    return formattedIntegerPart; // 否则只返回整数部分
  }
}
