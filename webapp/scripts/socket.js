import { State } from './state.js';
import { toast } from './ui.js';
import { renderAnswers } from './ui.js';
import { getQuestion, listAnswers } from './api.js';

let ws;

export function connectWS(onMessage) {
  if (!State.room.id) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/rooms/${State.room.id}`);
  ws.onopen = () => {
    // keepalive ping every 25s
    setInterval(() => ws?.readyState === 1 && ws.send('ping'), 25000);
  };
  ws.onmessage = async (ev) => {
    const msg = JSON.parse(ev.data);
    onMessage?.(msg);
    if (msg.type === 'player_joined') {
      toast(`Подключился игрок: ${msg.payload.name}`);
    } else if (msg.type === 'question_set') {
      const q = await getQuestion(State.room.id);
      document.getElementById('questionBlock').textContent = q.text || '—';
    } else if (msg.type === 'answer_added') {
      // optimistic update will also refresh answers list
    } else if (msg.type === 'answer_revealed') {
      // UI layer will flip the card
    } else if (msg.type === 'round_closed') {
      toast('Раунд закрыт. Начните новый вопрос.');
    }
  };
  ws.onclose = () => {
    toast('Соединение потеряно. Попробуйте обновить страницу.');
  };
}

export function wsSend(text) {
  try { ws?.send(text); } catch {}
}
