/**
 * 学术前沿 2.0：服务于 MICM 模型
 * 主源：Semantic Scholar API（关键词：Multimodal Interactional Competence, L2 SLA, Classroom Interaction）
 * 结构：paper_id, relevance_to_MICM, methodology_snapshot, gap_identified, bibtex
 * 核心 Prompt：「这篇论文对 MICM 模型的维度构建有何启发？」
 */
import { runResearchAgent } from './research-agent.mjs';
import { generateWithGemini } from '../lib/gemini.mjs';

const SECTION_TITLES = ['MICM 相关', 'L2 课堂互动'];

export async function runAcademicFrontierAgent() {
  const research = await runResearchAgent('MICM');
  const papers = research.papers || [];
  if (papers.length === 0) {
    return { sections: [], summary: research.summary || '今日暂无学术前沿' };
  }

  const MICM_PROMPT = '这篇论文对 MICM 模型（Multimodal Interactional Competence Model）的维度构建有何启发？请用 2-4 句中文回答。';

  const papersWithExtras = [];
  for (const p of papers) {
    let relevanceToMICM = '';
    let methodologySnapshot = '';
    let gapIdentified = '';
    let bibtex = '';
    let keyFindings = [];
    let implications = '';

    try {
      const prompt = `You are an academic writing assistant for a PhD student building a MICM (Multimodal Interactional Competence Model) for L2 classroom interaction research.

Paper title: ${p.title}
Authors: ${p.authors}
Year: ${p.year}
Abstract: ${(p.abstract || '').slice(0, 600)}

Output valid JSON only, no markdown fences, with this exact structure:
{
  "relevance_to_MICM": "2-4 句中文：这篇论文对 MICM 模型的维度构建有何启发？",
  "methodology_snapshot": "1-2 句中文：研究方法的简要概括",
  "gap_identified": "1-2 句中文：本研究可补充的研究空白或局限",
  "bibtex": "@article{key, author={...}, title={...}, year={...}, journal={...}} 格式的 BibTeX 条目",
  "keyFindings": ["要点1", "要点2", "要点3"],
  "implications": "2-3 句中文：对语言教育或应用语言学的启示"
}`;
      const raw = await generateWithGemini(prompt);
      const cleaned = raw.replace(/^[\s\S]*?(\{[\s\S]*\})[\s\S]*$/m, '$1').trim();
      const data = JSON.parse(cleaned);
      relevanceToMICM = data.relevance_to_MICM || '';
      methodologySnapshot = data.methodology_snapshot || '';
      gapIdentified = data.gap_identified || '';
      bibtex = data.bibtex || '';
      keyFindings = Array.isArray(data.keyFindings) ? data.keyFindings.slice(0, 5) : [];
      implications = data.implications || '';
    } catch (e) {
      relevanceToMICM = p.relevance || '（解析暂不可用）';
      keyFindings = ['（暂无）'];
      implications = '（暂无）';
    }

    papersWithExtras.push({
      ...p,
      relevance: relevanceToMICM || p.relevance,
      relevance_to_MICM: relevanceToMICM,
      methodology_snapshot: methodologySnapshot,
      gap_identified: gapIdentified,
      bibtex,
      keyFindings: keyFindings.length ? keyFindings : ['（暂无）'],
      implications: implications || '（暂无）',
    });
  }

  const sections = [];
  if (papersWithExtras.length >= 2) {
    sections.push(
      { sectionTitle: SECTION_TITLES[0], papers: papersWithExtras.slice(0, 1) },
      { sectionTitle: SECTION_TITLES[1], papers: papersWithExtras.slice(1) }
    );
  } else {
    sections.push({ sectionTitle: SECTION_TITLES[0], papers: papersWithExtras });
  }

  return {
    sections,
    summary: `今日 ${papers.length} 篇学术前沿 · MICM 模型 · Key Findings & Implications`,
  };
}
