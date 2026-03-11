const getCurrencyFromLocale = (locale: string) => {
  const lang = locale.split('-')[0].toLowerCase();
  const euroLangs = ['de', 'fr', 'it', 'es', 'nl', 'be', 'at', 'pt', 'fi', 'el', 'ie', 'lu', 'sk', 'si', 'cy', 'mt', 'lv', 'lt', 'ee'];
  if (euroLangs.includes(lang)) return 'EUR';
  if (lang === 'en' && (locale.toLowerCase().includes('gb') || locale.toLowerCase().includes('uk'))) return 'GBP';
  return 'USD';
};

/**
 * Formats a number as currency based on the user's browser locale.
 */
export const formatCurrency = (amount: number | string | undefined | null) => {
  if (amount === undefined || amount === null) return "---";
  
  const numericAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(numericAmount)) return amount.toString();

  const locale = navigator.language;
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: getCurrencyFromLocale(locale),
  }).format(numericAmount);
};

/**
 * Formats a date string or object based on the user's browser locale.
 */
export const formatDate = (date: string | Date | undefined | null, options?: Intl.DateTimeFormatOptions) => {
  if (!date) return "---";
  
  const dateObj = typeof date === "string" ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return "Invalid Date";

  return new Intl.DateTimeFormat(navigator.language, options).format(dateObj);
};
