export type Role = 'user' | 'bot';

export interface Message {
  id: string;
  role: Role;
  text: string;
  timestamp: number;
}
