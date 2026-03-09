import { GoogleGenerativeAI } from '@google/generative-ai';

const modelCache = new Map();

const DEFAULT_MODEL = process.env.GEMINI_MODEL || 'gemini-2.5-flash';

export function getGeminiModel(modelName = DEFAULT_MODEL) {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error('缺少 GEMINI_API_KEY');
  }
  if (!modelCache.has(modelName)) {
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    modelCache.set(modelName, genAI.getGenerativeModel({ model: modelName }));
  }
  return modelCache.get(modelName);
}

export async function generateWithGemini(prompt, modelName) {
  const m = getGeminiModel(modelName);
  const res = await m.generateContent(prompt);
  return res.response.text().trim();
}
