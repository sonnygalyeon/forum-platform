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
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
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
  | { type: "paragraph"; text: string }
  | { type: "quote"; text: string }
  | { type: "heading"; text: string; level: 1 | 2 | 3 | 4 }
  | { type: "code"; code: string; language?: string }
  | { type: "image"; asset_id: string; caption?: string }
  | { type: "video"; asset_id: string; caption?: string }
  | { type: "attachment"; asset_id: string; caption?: string };

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
  content: Array<
    | { type: "paragraph"; text: string }
    | { type: "quote"; text: string }
    | { type: "code"; code: string; language?: string }
  >;
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

export type AdminPage<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type AdminOverview = {
  generated_at: string;
  users: { total: number; active: number; staff: number; joined_last_7d: number };
  publications: { total: number; published: number; hidden: number; created_last_24h: number };
  comments: { total: number; published: number; hidden: number; created_last_24h: number };
  communities: { total: number; active: number; inactive: number };
  reports: { open: number; reviewing: number; resolved_last_7d: number };
  notification_events: { pending: number; failed: number };
};
export type AdminUser = User & { is_active: boolean; is_staff: boolean; is_superuser: boolean; last_login: string | null; publication_count: number; comment_count: number };
export type AdminPublication = { id:string; type:string; title:string; excerpt:string; author:User; community:CommunityCompact|null; visibility:"published"|"hidden"; current_revision:number; report_count:number; comment_count:number; created_at:string; updated_at:string };
export type AdminComment = { id:string; publication:{id:string;title:string;type:string}; author:User; parent_id:string|null; kind:string; excerpt:string; depth:number; visibility:"published"|"hidden"; score:number; is_accepted:boolean; report_count:number; created_at:string; updated_at:string };
export type AdminCommunity = { id:string; slug:string; name:string; description:string; owner:User; is_active:boolean; subscriber_count:number; publication_count:number; created_at:string; updated_at:string };
export type AdminReport = { id:string; reporter:User; target_type:"publication"|"comment"|"user"; target_id:string|null; target_label:string; reason:string; details:string; status:"open"|"reviewing"|"resolved"|"dismissed"; moderator:User|null; resolution_note:string; created_at:string; updated_at:string; resolved_at:string|null };
export type AdminModerationAction = { id:string; actor:User; target_type:string; target_id:string|null; target_label:string; action:string; reason:string; report_id:string|null; created_at:string };
