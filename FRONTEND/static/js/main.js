// static/js/main.js
function togglePw(id) {
  const el = document.getElementById(id);
  if (!el) return;
  if (el.type === "password") el.type = "text";
  else el.type = "password";
}	