export const State = {
  cfg: {
    baseUrl: window.location.origin,
  },
  user: {
    tg_user_id: null,
    name: null,
    user_id: null,
    super_cards: 3,
  },
  room: {
    id: null,
    code: null,
    status: 'active',
    round: null,
  }
};

export function setUser(u) {
  State.user = { ...State.user, ...u };
}

export function setRoom(r) {
  State.room = { ...State.room, ...r };
}
