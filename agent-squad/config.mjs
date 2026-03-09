/**
 * Agent 小队配置
 * - 英语学习助手：C1 习语/谚语，每日 10 条，标注地区，中英对照段落
 * - 美妆学习助手：冷橄榄皮、圆脸，每日推送适配内容
 * - 科研文献助手：博士生，研究方向见 RESEARCH_TOPICS，每日 3 篇论文
 */

// 使用丹佛时间（山地时区）
export const TZ = 'America/Denver';

// 默认收件邮箱
export const TARGET_EMAIL = 'jiaxinshen1208@gmail.com';

// 英语变体：用户在美国，语料以美式英语为主
export const ENGLISH_VARIETY = 'American';

// 英语助手：目标水平 C1
export const ENGLISH_LEVEL = 'C1';
export const IDIOMS_PER_DAY = 10;

// 美妆助手：用户肤质与脸型
export const USER_PROFILE = {
  skinTone: '冷橄榄皮', // cool olive undertone
  faceShape: '圆脸',
};

// 科研助手：研究方向关键词（用于检索与相关性判断）
export const RESEARCH_TOPICS = {
  languagePower: [
    'AP Chinese', 'assessment', 'epistemic injustice', 'hermeneutical injustice',
    'washback', 'metalinguistic asymmetry', 'CDA',
  ],
  classroomInteraction: [
    'CSL', 'peer interaction', 'translanguaging', 'LRE', 'NoM',
    'mediational architecture', 'MICM', 'novice-high',
  ],
  teachersAndInstitutions: [
    'charter', 'DLI', 'teacher vulnerability', 'decoupling',
    'emotional labor', 'autoethnography', 'policy implementation',
  ],
};

// 学术前沿 2.0：MICM 模型相关检索词（OpenAlex 优先近 3 年 + 引用排序）
export const ACADEMIC_FRONTIER_QUERIES = [
  'Multimodal Interactional Competence',
  'L2 SLA Classroom Interaction',
  'classroom interaction L2',
];

export const PAPERS_PER_DAY = 3;

// 文献数据源（可多源叠加，无需 API key）
export const SEMANTIC_SCHOLAR_BASE = 'https://api.semanticscholar.org/graph/v1';
export const OPENALEX_BASE = 'https://api.openalex.org';
