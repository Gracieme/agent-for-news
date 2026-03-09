import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  if (!supabase) {
    return NextResponse.json(
      { error: "未配置 Supabase" },
      { status: 503 }
    );
  }
  const { searchParams } = new URL(req.url);
  const list = searchParams.get("list") === "1";
  const date = searchParams.get("date");

  try {
    if (list) {
      const { data, error } = await supabase
        .from("agent_digests")
        .select("date")
        .order("date", { ascending: false })
        .limit(30);
      if (error) throw error;
      return NextResponse.json({ dates: (data || []).map((r) => r.date) });
    }

    const { data, error } = date
      ? await supabase.from("agent_digests").select("date, digest").eq("date", date).maybeSingle()
      : await supabase.from("agent_digests").select("date, digest").order("date", { ascending: false }).limit(1).maybeSingle();

    if (error) throw error;
    if (!data) {
      return NextResponse.json({
        date: null,
        digest: null,
        message: "暂无推送，请先运行 agent-squad 并配置 Supabase 同步",
      });
    }
    return NextResponse.json({
      date: data.date,
      digest: data.digest,
    });
  } catch (e) {
    console.error("Agent digest fetch error:", e);
    return NextResponse.json(
      { error: "获取失败" },
      { status: 500 }
    );
  }
}
