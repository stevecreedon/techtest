import { Application } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";
import ChatController from "/static/js/controllers/chat_controller.js";

const application = Application.start();
application.register("chat", ChatController);
