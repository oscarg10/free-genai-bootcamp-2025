const API_BASE_URL = 'http://localhost:5000';

// Group types
export interface Group {
  id: number;
  group_name: string;
  word_count: number;
}

export interface GroupsResponse {
  groups: Group[];
  total_pages: number;
  current_page: number;
}

// Word types
export interface WordGroup {
  id: number;
  name: string;
}

export interface Word {
  id: number;
  german: string;
  pronunciation: string;
  english: string;
  article: string;
  word_type: 'noun' | 'verb' | 'adjective';
  additional_info: {
    plural?: string;
    gender?: 'masculine' | 'feminine' | 'neuter';
    declension?: {
      nominative: { singular: string; plural: string; };
      accusative: { singular: string; plural: string; };
      dative: { singular: string; plural: string; };
      genitive: { singular: string; plural: string; };
    };
    comparative?: string;
    superlative?: string;
  };
  correct_count: number;
  wrong_count: number;
  groups: WordGroup[];
}

interface WordsResponse {
  data: {
    words: Word[];
    pagination: {
      current_page: number;
      total_pages: number;
      total_words: number;
      words_per_page: number;
    };
  }
}

// Study Session types
export type StudySessionSortKey = 'start_time' | 'end_time' | 'activity_name' | 'review_items_count';

export interface StudySession {
  id: number;
  group_id: number;
  group_name: string;
  activity_id: number;
  activity_name: string;
  start_time: string;
  end_time: string;
  review_items_count: number;
}

export interface WordReview {
  word_id: number;
  is_correct: boolean;
}

// API function to create a group
export async function createGroup(groupName: string): Promise<Group> {
  const response = await fetch(`${API_BASE_URL}/groups`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name: groupName }),
  });

  if (!response.ok) {
    throw new Error('Failed to create group');
  }

  return response.json();
}

// Dashboard types
export interface RecentSession {
  id: number;
  group_id: number;
  activity_name: string;
  created_at: string;
  correct_count: number;
  wrong_count: number;
}

export interface StudyStats {
  total_vocabulary: number;
  total_words_studied: number;
  mastered_words: number;
  success_rate: number;
  total_sessions: number;
  active_groups: number;
  current_streak: number;
}

// API Functions

// Group API
export async function fetchGroups(
  page: number = 1,
  sortBy: string = 'name',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/groups?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) throw new Error('Failed to fetch groups');
  return response.json();
}

export interface GroupDetails {
  id: number;
  group_name: string;
  word_count: number;
}

export interface GroupWordsResponse {
  words: Word[];
  total_pages: number;
  current_page: number;
}

export async function fetchGroupDetails(
  groupId: number,
  page: number = 1,
  sortBy: string = 'german',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupDetails> {
  const response = await fetch(
    `${API_BASE_URL}/groups/${groupId}`
  );
  if (!response.ok) throw new Error('Failed to fetch group details');
  return response.json();
}

export async function fetchGroupWords(
  groupId: number,
  page: number = 1,
  sortBy: string = 'german',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupWordsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/groups/${groupId}/words?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) throw new Error('Failed to fetch group words');
  return response.json();
}

// Word API
export async function fetchWords(
  page: number = 1,
  wordType?: 'noun' | 'verb' | 'adjective',
  sortBy: string = 'german',
  order: 'asc' | 'desc' = 'asc'
): Promise<WordsResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    sort_by: sortBy,
    order: order,
    ...(wordType && { word_type: wordType })
  });

  const response = await fetch(`${API_BASE_URL}/words?${params}`);
  if (!response.ok) throw new Error('Failed to fetch words');
  return response.json();
}

export async function fetchWordDetails(wordId: number): Promise<Word> {
  const response = await fetch(`${API_BASE_URL}/words/${wordId}`);
  if (!response.ok) throw new Error('Failed to fetch word details');
  return response.json();
}

export async function createWord(word: {
  german: string;
  english: string;
  article?: string;
  word_type: 'noun' | 'verb' | 'adjective';
  pronunciation?: string;
  additional_info?: {
    plural?: string;
    gender?: 'masculine' | 'feminine' | 'neuter';
    comparative?: string;
    superlative?: string;
  };
  group_ids?: number[];
}): Promise<Word> {
  const response = await fetch(`${API_BASE_URL}/words`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(word),
  });
  if (!response.ok) throw new Error('Failed to create word');
  return response.json();
}

// Study Session API
export async function createStudySession(
  groupId: number,
  studyActivityId: number
): Promise<{ session_id: number }> {
  const response = await fetch(`${API_BASE_URL}/api/study-sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      group_id: groupId,
      study_activity_id: studyActivityId,
    }),
  });
  if (!response.ok) throw new Error('Failed to create study session');
  return response.json();
}

export async function submitStudySessionReview(
  sessionId: number,
  reviews: WordReview[]
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/study-sessions/${sessionId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reviews }),
  });
  if (!response.ok) throw new Error('Failed to submit review');
}

export interface StudySessionsResponse {
  items: StudySession[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export async function fetchStudySessions(
  page: number = 1,
  perPage: number = 10
): Promise<StudySessionsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/study-sessions?page=${page}&per_page=${perPage}`
  );
  if (!response.ok) throw new Error('Failed to fetch study sessions');
  return response.json();
}

export async function fetchGroupStudySessions(
  groupId: number,
  page: number = 1,
  sortBy: string = 'created_at',
  order: 'asc' | 'desc' = 'desc'
): Promise<StudySessionsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/groups/${groupId}/study-sessions?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) throw new Error('Failed to fetch group study sessions');
  return response.json();
}

// Study Activity types
export interface StudyActivity {
  id: number;
  title: string;
  launch_url: string;
  preview_url: string;
}

// Study Activity API
export async function fetchStudyActivities(): Promise<StudyActivity[]> {
  const response = await fetch(`${API_BASE_URL}/api/study-activities`);
  if (!response.ok) {
    throw new Error('Failed to fetch study activities');
  }
  return response.json();
}

// Dashboard API
export async function fetchRecentStudySession(): Promise<RecentSession | null> {
  const response = await fetch(`${API_BASE_URL}/dashboard/recent-session`);
  if (!response.ok) throw new Error('Failed to fetch recent study session');
  const data = await response.json();
  return data.session || null;
}

export async function fetchStudyStats(): Promise<StudyStats> {
  const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
  if (!response.ok) throw new Error('Failed to fetch study stats');
  return response.json();
}
