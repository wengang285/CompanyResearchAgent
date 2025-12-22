// 研究请求
export interface ResearchRequest {
  company: string;
  depth: 'basic' | 'standard' | 'deep';
  focus: string[];
}

// 研究进度
export interface ResearchProgress {
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  currentAgent: string;
  currentTask: string;
  estimatedTime: number;
}

// 研究任务
export interface ResearchTask {
  id: string;
  company: string;
  status: string;
  depth: string;
  focus_areas: string[];
  progress: number;
  current_agent: string;
  current_task: string;
  estimated_time: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  report_data: Report | null;
  error_message: string | null;
}

// 报告章节
export interface ReportSection {
  id?: string;
  title: string;
  content?: string;
  key_points?: string[];
  subsections?: ReportSubsection[];
  risks?: Risk[];
  recommendation?: string;
  reasoning?: string;
  catalysts?: string[];
  overall_score?: number;
  summary?: string;
  swot?: SwotData;
}

export interface ReportSubsection {
  title: string;
  content?: string;
  score?: number;
  strengths?: string[];
  weaknesses?: string[];
  opportunities?: string[];
  threats?: string[];
}

export interface SwotItem {
  item: string;
  detail?: string;
}

export type SwotItemType = string | SwotItem;

export interface SwotData {
  strengths: SwotItemType[];
  weaknesses: SwotItemType[];
  opportunities: SwotItemType[];
  threats: SwotItemType[];
}

export interface Risk {
  type: string;
  description: string;
  severity?: string;
}

// 报告元数据详情
export interface ReportMetadataDetail {
  company_name?: string;
  company?: string;
  stock_code?: string;
  industry?: string;
  research_date?: string;
  overall_score?: number;
  recommendation?: string;
}

// 报告
export interface Report {
  id?: string;
  task_id?: string;
  company: string;
  stock_code?: string;
  research_date: string;
  sections: ReportSection[];
  content?: ReportContent;
  pdf_path?: string;
  created_at?: string;
  metadata?: ReportMetadataDetail;
}

export interface ReportContent {
  company: string;
  stock_code: string;
  research_date: string;
  sections: ReportSection[];
  metadata?: ReportMetadataDetail;
}

// 报告元数据
export interface ReportMetadata {
  generated_at: string;
  depth: string;
  focus_areas: string[];
}





