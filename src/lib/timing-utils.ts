import { TimingReference } from "./reading-types";

interface CardForTiming {
  nameZh: string;
  number?: number | null;
  suit?: string | null;
  reversed?: boolean;
  position?: string;
}

const SUIT_ZODIAC: Record<string, { months: string }> = {
  cups:      { months: "巨蟹月（6月底/7月）· 天蝎月（10月底/11月）· 双鱼月（2月底/3月）" },
  wands:     { months: "白羊月（3月底/4月）· 狮子月（7月底/8月）· 射手月（11月底/12月）" },
  swords:    { months: "双子月（5月底/6月）· 天秤月（9月底/10月）· 水瓶月（1月底/2月）" },
  pentacles: { months: "金牛月（4月底/5月）· 处女月（8月底/9月）· 摩羯月（12月底/1月）" },
};

function weeksLabel(n: number, reversed: boolean): string {
  const base = reversed ? n + 0.5 : n;
  if (base <= 2) return `约${base}周`;
  if (base <= 4) return `约${base}周（${Math.round(base / 4 * 10) / 10}个月左右）`;
  if (base < 8)  return `约${base}周（一个多月）`;
  if (base <= 10) return `约${base}周（两个多月）`;
  return `约${base}周（近三个月）`;
}

export function calculateTiming(cards: CardForTiming[]): TimingReference {
  if (!cards || cards.length === 0) {
    return { cardName: "", cardNumber: null, suit: null, weeksEstimate: null, zodiacMonth: null, summary: "" };
  }

  // Priority: find "核心" or "现在" position, else use first card
  const primary =
    cards.find(c => c.position?.includes("核心") || c.position?.includes("现在")) ??
    cards[0];

  const cardNumber = primary.number ?? null;
  const reversed   = primary.reversed ?? false;
  const suit       = primary.suit ?? null;

  const weeksEstimate = cardNumber !== null
    ? (reversed ? cardNumber + 0.5 : cardNumber)
    : null;

  const zodiacInfo = suit ? SUIT_ZODIAC[suit] : null;

  const parts: string[] = [];
  if (weeksEstimate !== null) parts.push(weeksLabel(weeksEstimate, reversed));
  if (zodiacInfo) parts.push(zodiacInfo.months.split("·")[0].trim());

  const summary = parts.length > 0
    ? `基于 ${primary.nameZh}${cardNumber ? `（数字${cardNumber}）` : ""} → ${parts.join(" / ")}`
    : "";

  return {
    cardName: primary.nameZh,
    cardNumber,
    suit,
    weeksEstimate,
    zodiacMonth: zodiacInfo?.months ?? null,
    summary,
  };
}
