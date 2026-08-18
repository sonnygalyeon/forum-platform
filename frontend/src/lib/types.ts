export type User = {
  id: string;
  nickname: string;
  email?: string;
  first_name: string;
  last_name: string;
  country: string;
  nationality: string;
  interface_language?: string;
  bio: string;
  date_joined: string;
  follower_count?: number;
  following_count?: number;
  is_following?: boolean;
  is_blocked?: boolean;
  is_muted?: boolean;
};

export type Tag = { id: string; name: string; slug: string };
export type CommunityCompact = { id: string; slug: string; name: string };
export type Community = CommunityCompact & {
  description: string;
  owner: User;
  subscriber_count: number;
  is_subscribed: boolean;
  created_at: string;
};

export type ContentBlock =
  | { type: "paragraph" | "quote"; text: string }
  | { type: "heading"; text: string; level: 1 | 2 | 3 | 4 }
  | { type: "code"; code: string; language?: string }
  | { type: "image" | "video" | "attachment"; asset_id: string; caption?: string };

export type Publication = {
  id: string;
  type: "post" | "article" | "topic";
  title: string;
  excerpt: string;
  author: User;
  community: CommunityCompact | null;
  tags: Tag[];
  revision: number;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
  content?: ContentBlock[];
  can_edit?: boolean;
  can_interact?: boolean;
};

export type Comment = {
  id: string;
  publication_id: string;
  kind: "answer" | "comment" | "reply";
  author: User;
  parent_id: string | null;
  content: Array<{ type: "paragraph" | "quote"; text: string } | { type: "code"; code: string; language?: string }>;
  depth: number;
  score: number;
  my_vote: -1 | 1 | null;
  can_vote: boolean;
  reply_count: number;
  is_accepted: boolean;
  can_accept: boolean;
  can_unaccept: boolean;
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type Notification = {
  id: string;
  kind: string;
  actor: User | null;
  publication: { id: string; type: string; title: string } | null;
  comment: { id: string; kind: string; excerpt: string } | null;
  report_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type CursorPage<T> = {
  next: string | null;
  previous: string | null;
  results: T[];
};
