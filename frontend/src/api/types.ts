export type ApiSuccess<T> = {
  code: number;
  message: string;
  data: T;
};

export type TokenData = {
  access_token: string;
  token_type: string;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type RegisterPayload = LoginPayload & {
  nickname?: string | null;
};

export type ChatSession = {
  id: number;
  user_id: number;
  title: string;
  created_time: string;
  updated_time: string;
};

export type ChatMessage = {
  id: number;
  session_id: number;
  role: string;
  content: string;
  created_time: string;
};

export type KnowledgeDocument = {
  id: number;
  user_id: number;
  filename: string;
  content_type: string | null;
  source_type: string;
  content: string;
  created_time: string;
  updated_time: string;
};

export type KnowledgeSource = {
  document_id: number;
  chunk_id: number;
  score: number;
  content: string;
};

export type KnowledgeAnswer = {
  answer: string;
  sources: KnowledgeSource[];
};
