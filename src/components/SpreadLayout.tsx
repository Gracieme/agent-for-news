"use client";
import React from "react";

// 每行的牌索引，null = 空位（占位但不显示）
const LAYOUT_ROWS: Record<string, (number | null)[][]> = {
  single:       [[0]],
  yesno:        [[0, 1]],
  three:        [[0, 1, 2]],
  newMoon:      [[0, 1, 2]],
  // 三角：顶中，底左右
  mindBodySoul: [
    [null, 0, null],
    [1,    null,  2],
  ],
  // 2×2
  relationship: [
    [0, 1],
    [2, 3],
  ],
  // 菱形十字
  selfGrowth: [
    [null, 1, null],
    [0,    null,  2],
    [null, 3, null],
  ],
  career: [[0, 1, 2, 3, 4]],
  // 凯尔特十字
  celtic: [
    [null, 3, null],  // 未来
    [2,    0,    1],  // 过去 · 核心 · 挑战
    [null, 4, null],  // 结果
  ],
  moonCycle: [
    [0, 1, 2],
    [3, 4, 5],
  ],
  // 左A右B
  decision: [
    [0, 1],
    [2, 3],
    [4, 5],
  ],
  chakra: [[0, 1, 2, 3, 4, 5, 6]],
};

function getDefaultRows(count: number): (number | null)[][] {
  const cols = Math.min(count, 4);
  const rows: (number | null)[][] = [];
  for (let i = 0; i < count; i += cols) {
    rows.push(Array.from({ length: cols }, (_, j) => (i + j < count ? i + j : null)));
  }
  return rows;
}

interface SpreadLayoutProps {
  spreadId: string;
  count: number;
  children: React.ReactNode;
}

export default function SpreadLayout({ spreadId, count, children }: SpreadLayoutProps) {
  const rows = LAYOUT_ROWS[spreadId] ?? getDefaultRows(count);
  const childArray = React.Children.toArray(children);
  const maxCols = Math.max(...rows.map((r) => r.length));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", alignItems: "center", width: "100%" }}>
      {rows.map((row, rowIdx) => (
        <div
          key={rowIdx}
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${maxCols}, 1fr)`,
            gap: "12px",
            width: "100%",
          }}
        >
          {row.map((cardIdx, colIdx) => (
            <div
              key={colIdx}
              style={{
                visibility: cardIdx === null ? "hidden" : "visible",
                display: "flex",
                justifyContent: "center",
              }}
            >
              {cardIdx !== null ? childArray[cardIdx] : null}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
