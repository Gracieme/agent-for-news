"use client";

import { TimingReference as TimingData } from "@/lib/reading-types";

export default function TimingReference({ data }: { data: TimingData }) {
  if (!data || !data.summary) return null;

  return (
    <div className="rounded-2xl p-5 mb-6" style={{ background: "rgba(155,168,141,0.08)", border: "1px solid rgba(139,154,125,0.2)" }}>
      <div className="flex items-start gap-3">
        <span className="text-lg flex-shrink-0 mt-0.5">🕐</span>
        <div className="flex-1">
          <div className="text-sm font-semibold mb-1" style={{ color: "var(--sage-deep)" }}>时间参考</div>
          <div className="text-sm leading-relaxed mb-2" style={{ color: "var(--text-warm)" }}>{data.summary}</div>

          <div className="space-y-1">
            {data.weeksEstimate !== null && (
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                <span className="font-medium">数字周算法：</span>
                数字{data.cardNumber} = 约{data.weeksEstimate}周
                {data.weeksEstimate <= 4 ? "（近期）" : data.weeksEstimate <= 8 ? "（一两个月内）" : "（两三个月内）"}
              </div>
            )}
            {data.zodiacMonth && (
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                <span className="font-medium">星座月算法：</span>
                {data.zodiacMonth}
              </div>
            )}
          </div>

          <div className="text-xs mt-2 italic" style={{ color: "var(--text-muted)" }}>
            ⓘ 建议参考时间窗口在3个月内，越近期越准确
          </div>
        </div>
      </div>
    </div>
  );
}
