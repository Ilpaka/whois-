import { State, setUser, setRoom } from './state.js';

async function j(method, path, body) {
  const res = await fetch(`${State.cfg.baseUrl}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function upsertUser(tg_user_id, name) {
  const data = await j('POST', '/users', { tg_user_id, name });
  setUser({ user_id: data.user_id, name });
  return data;
}

export async function createRoom() {
  const data = await j('POST', '/rooms', { room_code:"", tg_user_id: String(State.user.tg_user_id), name: State.user.name });
  setRoom({ id: data.room_id, code: data.room_code });
  return data;
}

export async function joinRoom(code) {
  const data = await j('POST', '/rooms/join', { room_code: code, tg_user_id: String(State.user.tg_user_id), name: State.user.name });
  setRoom({ id: data.room_id, code, status: 'active' });
  State.user.super_cards = data.super_cards;
  return data;
}

export async function getRoom(room_id) {
  const data = await j('GET', `/rooms/${room_id}`);
  setRoom({ id: data.room_id, code: data.room_code, status: data.status, round: data.current_round });
  return data;
}

export async function setQuestion(room_id, text) {
  return j('POST', `/rooms/${room_id}/question`, { text });
}

export async function getQuestion(room_id) {
  return j('GET', `/rooms/${room_id}/question`);
}

export async function sendAnswer(room_id, round_id, text) {
  const body = { round_id, text, author_id: State.user.user_id };
  return j('POST', `/rooms/${room_id}/answers`, body);
}

export async function listAnswers(room_id, round_id) {
  return j('GET', `/rooms/${room_id}/answers?round_id=${encodeURIComponent(round_id)}`);
}

export async function reveal(room_id, round_id, answer_id) {
  return j('POST', `/rooms/${room_id}/reveal`, { round_id, answer_id, actor_id: State.user.user_id });
}
