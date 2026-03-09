import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  if (!supabase) return NextResponse.json({ reading: null });
  try {
    const reading = await req.json();
    const { data, error } = await supabase
      .from("readings")
      .insert([reading])
      .select()
      .single();
    if (error) throw error;
    return NextResponse.json({ reading: data });
  } catch (error) {
    console.error("Save reading error:", error);
    return NextResponse.json({ error: "保存失败" }, { status: 500 });
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const userId = searchParams.get("user_id");
  if (!userId) return NextResponse.json({ error: "缺少用户ID" }, { status: 400 });
  if (!supabase) return NextResponse.json({ readings: [] });
  try {
    const { data, error } = await supabase
      .from("readings")
      .select("*")
      .eq("user_id", userId)
      .order("created_at", { ascending: false })
      .limit(20);
    if (error) throw error;
    return NextResponse.json({ readings: data });
  } catch (error) {
    console.error("Fetch readings error:", error);
    return NextResponse.json({ error: "获取记录失败" }, { status: 500 });
  }
}
