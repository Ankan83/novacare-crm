const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(endpoint, options = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || data.message || "Server Error");
  }

  return data;
}

/* ---------------- CHAT ---------------- */

export async function sendChat(payload) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTimeline(hcpId) {
  const query = hcpId ? `?hcp_id=${encodeURIComponent(hcpId)}` : "";
  return request(`/interactions/timeline${query}`);
}

export function getFollowUps() {
  return request("/copilot/follow-ups");
}

export function getMeetingPrep(hcpId) {
  return request(`/meeting-prep/${encodeURIComponent(hcpId)}`);
}

export function getAnalytics() {
  return request("/analytics");
}

export function checkCompliance(text) {
  return request("/compliance/check", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function findDuplicateHcps(payload) {
  return request("/hcps/duplicates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFollowUpEmail(interactionId) {
  return request(`/copilot/follow-ups/${encodeURIComponent(interactionId)}/email`, {
    method: "POST",
    body: JSON.stringify({ send: false }),
  });
}

export async function downloadCalendarEvent(payload) {
  const response = await fetch(`${BASE_URL}/copilot/calendar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || "Unable to create calendar event.");
  }
  return response.blob();
}

export default {
  sendChat,
  getTimeline,
  getFollowUps,
  getMeetingPrep,
  getAnalytics,
  checkCompliance,
  findDuplicateHcps,
  getFollowUpEmail,
  downloadCalendarEvent,
};
