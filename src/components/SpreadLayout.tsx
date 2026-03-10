"use client";
import React from "react";

type Placement = { col: number; row: number };
type LayoutConfig = { cols: number; rows: number; placements: Placement[] };

const LAYOUTS: Record<string, LayoutConfig> = {
  // 1张
  single: {
    cols: 1, rows: 1,
    placements: [{ col: 1, row: 1 }],
  },
  // 2张 横排
  yesno: {
    cols: 2, rows: 1,
    placements: [{ col: 1, row: 1 }, { col: 2, row: 1 }],
  },
  // 3张 横排
  three: {
    cols: 3, rows: 1,
    placements: [{ col: 1, row: 1 }, { col: 2, row: 1 }, { col: 3, row: 1 }],
  },
  newMoon: {
    cols: 3, rows: 1,
    placements: [{ col: 1, row: 1 }, { col: 2, row: 1 }, { col: 3, row: 1 }],
  },
  // 3张 三角（顶部居中，底部左右）
  mindBodySoul: {
    cols: 3, rows: 2,
    placements: [
      { col: 2, row: 1 }, // 行动/身体 — 顶中
      { col: 1, row: 2 }, // 感受/情绪 — 左下
      { col: 3, row: 2 }, // 精神/思维 — 右下
    ],
  },
  // 4张 2×2
  relationship: {
    cols: 2, rows: 2,
    placements: [
      { col: 1, row: 1 }, { col: 2, row: 1 },
      { col: 1, row: 2 }, { col: 2, row: 2 },
    ],
  },
  // 4张 菱形十字
  selfGrowth: {
    cols: 3, rows: 3,
    placements: [
      { col: 2, row: 1 }, // 内在阻力 — 上
      { col: 1, row: 2 }, // 当前状态 — 左
      { col: 3, row: 2 }, // 需要突破 — 右
      { col: 2, row: 3 }, // 潜藏力量 — 下
    ],
  },
  // 5张 横排
  career: {
    cols: 5, rows: 1,
    placements: [
      { col: 1, row: 1 }, { col: 2, row: 1 }, { col: 3, row: 1 },
      { col: 4, row: 1 }, { col: 5, row: 1 },
    ],
  },
  // 5张 凯尔特十字
  celtic: {
    cols: 3, rows: 3,
    placements: [
      { col: 2, row: 2 }, // 核心 — 中
      { col: 3, row: 2 }, // 挑战 — 右
      { col: 1, row: 2 }, // 过去 — 左
      { col: 2, row: 1 }, // 未来 — 上
      { col: 2, row: 3 }, // 结果 — 下
    ],
  },
  // 6张 3×2
  moonCycle: {
    cols: 3, rows: 2,
    placements: [
      { col: 1, row: 1 }, { col: 2, row: 1 }, { col: 3, row: 1 },
      { col: 1, row: 2 }, { col: 2, row: 2 }, { col: 3, row: 2 },
    ],
  },
  // 6张 2×3（左A右B）
  decision: {
    cols: 2, rows: 3,
    placements: [
      { col: 1, row: 1 }, { col: 2, row: 1 },
      { col: 1, row: 2 }, { col: 2, row: 2 },
      { col: 1, row: 3 }, { col: 2, row: 3 },
    ],
  },
  // 7张 横排
  chakra: {
    cols: 7, rows: 1,
    placements: [
      { col: 1, row: 1 }, { col: 2, row: 1 }, { col: 3, row: 1 },
      { col: 4, row: 1 }, { col: 5, row: 1 }, { col: 6, row: 1 },
      { col: 7, row: 1 },
    ],
  },
};

function getDefaultLayout(count: number): LayoutConfig {
  const cols = Math.min(count, 4);
  return {
    cols,
    rows: Math.ceil(count / cols),
    placements: Array.from({ length: count }, (_, i) => ({
      col: (i % cols) + 1,
      row: Math.floor(i / cols) + 1,
    })),
  };
}

interface SpreadLayoutProps {
  spreadId: string;
  count: number;
  children: React.ReactNode;
}

export default function SpreadLayout({ spreadId, count, children }: SpreadLayoutProps) {
  const layout = LAYOUTS[spreadId] ?? getDefaultLayout(count);
  const childArray = React.Children.toArray(children);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${layout.cols}, minmax(0, 1fr))`,
        gridTemplateRows: `repeat(${layout.rows}, auto)`,
        gap: "16px",
        justifyItems: "center",
        alignItems: "start",
      }}
    >
      {childArray.map((child, i) => {
        const placement = layout.placements[i];
        if (!placement) return null;
        return (
          <div
            key={i}
            style={{ gridColumn: placement.col, gridRow: placement.row, width: "100%" }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}
