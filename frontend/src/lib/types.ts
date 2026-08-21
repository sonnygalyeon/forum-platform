export type IdentityFrame = {
  id: string;
  slug: string;
  name: string;
  description: string;
  tier: "base" | "rare" | "epic" | "legendary" | "staff";
  style_token: string;
  unlock_type: "free" | "reputation" | "badge" | "staff";
  unlock_value: number;
  required_badge_slug: string;
  sort_order: number;
};

export type IdentityBadge = {
  id: string;
  slug: string;
  name: string;
  description: string;
  tier: "base" | "rare" | "epic" | "legendary" | "staff";
  icon_key: string;
  rule_type: string;
  threshold: number;
  sort_order: number;
};

export type OwnedFrame = { frame: IdentityFrame; source: string; unlocked_at: string };
export type OwnedBadge = { badge: IdentityBadge; pinned: boolean; pin_order: number; source: string; awarded_at: string };
export type UserIdentity = {
  headline: string;
  accent: "emerald" | "jade" | "ice" | "violet";
  reputation: number;
  level: number;
  equipped_frame: IdentityFrame | null;
  badges: OwnedBadge[];
  updated_at: string | null;
};
export type MyIdentity = UserIdentity & { owned_frames: OwnedFrame[]; owned_badges: OwnedBadge[] };

export type MediaAsset = {
  id: string;
  original_name?: string;
  name?: string;
  declared_content_type?: string;
  content_type?: string;
  kind: "image" | "video" | "file";
  size_bytes: number;
  part_size?: number;
  part_count?: number;
  status: "uploading" | "pending_scan" | "ready" | "aborted" | "rejected";
  url: string | null;
  created_at?: string;
  completed_at?: string | null;
};

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
  avatar: MediaAsset | null;
  banner: MediaAsset | null;
  identity: UserIdentity;
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
  publication_count: number;
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

export type PublicationMedia = {
  asset_id: string;
  role: "preview_image" | "preview_video" | "attachment" | "inline" | string;
  sort_order: number;
  name: string;
  kind: "image" | "video" | "file";
  content_type: string;
  size_bytes: number;
  status: string;
  url: string | null;
};

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
  comment_count: number;
  created_at: string;
  updated_at: string;
  content?: ContentBlock[];
  media?: PublicationMedia[];
  can_edit?: boolean;
  can_interact?: boolean;
};

export type CommentBlock =
  | { type: "paragraph"; text: string }
  | { type: "quote"; text: string }
  | { type: "code"; code: string; language?: string };

export type Comment = {
  id: string;
  publication_id: string;
  kind: "answer" | "comment" | "reply";
  author: User;
  parent_id: string | null;
  content: CommentBlock[];
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
  publication?: { id: string; type: string; title: string; created_at: string };
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

export type NotificationPreferences = {
  followed_user_publications: boolean;
  community_publications: boolean;
  publication_responses: boolean;
  comment_replies: boolean;
  accepted_answers: boolean;
  new_followers: boolean;
  moderation_updates: boolean;
  updated_at: string;
};

export type SocialUserEdge = { user: User; followed_at?: string; blocked_at?: string; muted_at?: string };

export type CursorPage<T> = {
  next: string | null;
  previous: string | null;
  results: T[];
};


export type SearchScope = "all" | "publications" | "users" | "communities" | "tags";
export type SearchTag = { id: string; name: string; slug: string; publication_count: number };
export type SearchResponse = {
  query: string;
  scope: SearchScope;
  counts: { publications: number; users: number; communities: number; tags: number };
  publications: Publication[];
  users: User[];
  communities: Community[];
  tags: SearchTag[];
};
export type DiscoveryResponse = {
  popular_tags: SearchTag[];
  active_communities: Community[];
  open_topics: Publication[];
  top_users: User[];
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
export type AdminUser = User & { is_active: boolean; is_staff: boolean; is_superuser: boolean; last_login: string | null; publication_count: number; comment_count: number; reputation: number; level: number };
export type AdminPublication = { id:string; type:string; title:string; excerpt:string; author:User; community:CommunityCompact|null; visibility:"published"|"hidden"; current_revision:number; report_count:number; comment_count:number; created_at:string; updated_at:string };
export type AdminComment = { id:string; publication:{id:string;title:string;type:string}; author:User; parent_id:string|null; kind:string; excerpt:string; depth:number; visibility:"published"|"hidden"; score:number; is_accepted:boolean; report_count:number; created_at:string; updated_at:string };
export type AdminCommunity = { id:string; slug:string; name:string; description:string; owner:User; is_active:boolean; subscriber_count:number; publication_count:number; created_at:string; updated_at:string };
export type AdminReport = { id:string; reporter:User; target_type:"publication"|"comment"|"user"; target_id:string|null; target_label:string; reason:string; details:string; status:"open"|"reviewing"|"resolved"|"dismissed"; moderator:User|null; resolution_note:string; created_at:string; updated_at:string; resolved_at:string|null };
export type AdminModerationAction = { id:string; actor:User; target_type:string; target_id:string|null; target_label:string; action:string; reason:string; report_id:string|null; created_at:string };


export type MessengerMember = { user: User; role: "owner" | "admin" | "member"; joined_at: string; is_muted: boolean; is_archived: boolean; online: boolean };
export type MessengerReaction = { emoji: string; count: number; reacted_by_me: boolean };
export type MessengerReplyPreview = { id: string; sender_nickname: string; text: string; deleted: boolean };
export type MessengerMessage = {
  id: string; conversation_id: string; sender: User; client_id: string; text: string;
  reply_to: MessengerReplyPreview | null; attachments: MediaAsset[]; reactions: MessengerReaction[]; read_by_count: number;
  deleted: boolean; created_at: string; edited_at: string | null; deleted_at: string | null;
};
export type MessengerConversation = {
  id: string; kind: "direct" | "group"; title: string; display_title: string; members: MessengerMember[];
  last_message: { id:string; sender_id:string; sender_nickname:string; text:string; created_at:string; deleted:boolean } | null;
  unread_count: number; is_muted: boolean; is_archived: boolean; created_at: string; updated_at: string; last_message_at: string | null;
};
export type MessengerMessagesPage = { next_before: string | null; results: MessengerMessage[] };
export type MessengerSocketEvent = { type: string; conversation_id?: string; message_id?: string; user_id?: string; nickname?: string; active?: boolean; sender_id?: string };
