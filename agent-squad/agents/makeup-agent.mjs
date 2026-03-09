/**
 * 美妆学习助手：针对冷橄榄皮、圆脸，每日推送适配内容（妆容/产品/技巧）
 */
import { generateWithGemini } from '../lib/gemini.mjs';
import { USER_PROFILE } from '../config.mjs';

export async function runMakeupAgent() {
  const { skinTone, faceShape } = USER_PROFILE;

  const prompt = `你是一位专业美妆顾问。用户特征：肤质/肤色为「${skinTone}」，脸型为「${faceShape}」。请为今日推送一段美妆学习内容，要求：

1. 内容与「${skinTone}」和「${faceShape}」直接相关，例如：
   - 适合冷橄榄皮的底妆色号、腮红/唇色推荐（可具体到色调，如冷调玫瑰、橄榄友好色）
   - 适合圆脸的修容、腮红位置或发型建议，让脸型更立体
   - 避免显黄、显灰的雷区
2. 篇幅适中：一段话 150–250 字，实用、可操作。
3. 语气亲切，像每日小贴士。
4. 不要编造具体品牌名，可用「冷调豆沙色」「哑光修容」等描述；若提到品类即可（如「某款橄榄皮友好的粉底」）。

只输出这一段中文内容，不要标题、不要列表符号，纯段落。`;

  const content = await generateWithGemini(prompt);
  return {
    raw: content,
    summary: `今日美妆小贴士（${skinTone} · ${faceShape}）`,
  };
}
