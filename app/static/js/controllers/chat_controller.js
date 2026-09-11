import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";

export default class extends Controller {
  static targets = ["input", "messages"];

  connect() {
    this.thinkingBubble = null;
    this.lastAnswerBubble = null;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    this.socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat`);
    this.socket.addEventListener("message", (event) => {
      this.handleEvent(JSON.parse(event.data));
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
    this.thinkingBubble = null;
    this.lastAnswerBubble = null;
    this.socket.send(JSON.stringify({ message }));
    this.inputTarget.value = "";
  }

  handleEvent(data) {
    switch (data.type) {
      case "thinking":
        this.appendThinking(data.text);
        break;
      case "tool_call":
        this.appendThinking(`→ calling ${data.tool_name}(${JSON.stringify(data.tool_input ?? {})})`);
        break;
      case "tool_result":
        break; // too technical to surface directly; the answer summarizes it
      case "answer":
        this.lastAnswerBubble = this.appendMessage(data.text, "response");
        this.thinkingBubble = null;
        break;
      case "download":
        this.appendDownloadLink(data.download_url);
        break;
    }
  }

  appendThinking(text) {
    if (!this.thinkingBubble) {
      this.thinkingBubble = this.appendMessage(text, "thinking");
      return;
    }
    this.thinkingBubble.textContent += `\n${text}`;
    this.messagesTarget.scrollTop = this.messagesTarget.scrollHeight;
  }

  appendDownloadLink(url) {
    const target = this.lastAnswerBubble;
    if (!target) return;

    const link = document.createElement("a");
    link.href = url;
    link.textContent = "Download CSV";
    link.className = "block mt-2 text-sm text-green-700 underline";
    target.appendChild(link);
    this.messagesTarget.scrollTop = this.messagesTarget.scrollHeight;
  }

  appendMessage(text, kind) {
    const wrapper = document.createElement("div");
    wrapper.className = `flex w-full mb-2 ${kind === "question" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className = `w-2/3 rounded-lg px-4 py-2 shadow whitespace-pre-line ${this.bubbleStyle(kind)}`;
    bubble.textContent = text;

    wrapper.appendChild(bubble);
    this.messagesTarget.appendChild(wrapper);
    this.messagesTarget.scrollTop = this.messagesTarget.scrollHeight;
    return bubble;
  }

  bubbleStyle(kind) {
    if (kind === "question") return "bg-green-500 text-white";
    if (kind === "thinking") return "bg-gray-100 text-gray-500 italic text-sm";
    return "bg-white text-gray-800";
  }
}
