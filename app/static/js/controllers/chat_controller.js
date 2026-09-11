import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = ["input", "messages"];

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    this.socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat`);
    this.socket.addEventListener("message", (event) => {
      const data = JSON.parse(event.data);
      this.appendMessage(data.message, "response");
    });
  }

  disconnect() {
    this.socket?.close();
  }

  send(event) {
    event.preventDefault();
    const message = this.inputTarget.value.trim();
    if (!message) return;

    this.appendMessage(message, "question");
    this.socket.send(JSON.stringify({ message }));
    this.inputTarget.value = "";
  }

  appendMessage(text, kind) {
    const wrapper = document.createElement("div");
    wrapper.className = `flex w-full mb-2 ${kind === "question" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className =
      kind === "question"
        ? "w-2/3 rounded-lg px-4 py-2 shadow bg-green-500 text-white"
        : "w-2/3 rounded-lg px-4 py-2 shadow bg-white text-gray-800";
    bubble.textContent = text;

    wrapper.appendChild(bubble);
    this.messagesTarget.appendChild(wrapper);
    this.messagesTarget.scrollTop = this.messagesTarget.scrollHeight;
  }
}
