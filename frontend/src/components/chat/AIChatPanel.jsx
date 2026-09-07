import { useEffect, useMemo, useRef, useState } from "react";
import { useSelector } from "react-redux";

import "../../styles/AIChatPanel.css";

import DoctorSelection from "./DoctorSelection";
import ConfirmationCard from "./ConfirmationCard";

export default function AIChatPanel({
  chatting,
  messages,
  chatInput,
  setChatInput,
  sendMessage,
  onKeyDown,
  chatEndRef,
  offline,
}) {
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const [listening, setListening] = useState(false);

  const { readyForConfirmation } = useSelector((state) => state.crm);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function parseDoctors(content = "") {
    if (
      !content.includes("multiple Healthcare Professionals") &&
      !content.includes("Please reply with")
    ) {
      return null;
    }

    const doctors = [];

    const regex = /^\s*(\d+)\.\s*(.+?)\s*\((.+?)\)\s*$/gm;

    let match;

    while ((match = regex.exec(content)) !== null) {
      doctors.push({
        id: match[1],
        name: match[2],
        organization: match[3],
      });
    }

    return doctors.length ? doctors : null;
  }

  function handleDoctorSelection(number) {
    sendMessage(String(number));
  }

  function handleConfirmation() {
    sendMessage("yes");
  }

  function handleEdit() {
    setChatInput("");
    inputRef.current?.focus();
  }

  function toggleVoiceInput() {
    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!Recognition) {
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setChatInput((current) =>
        current.trim() ? `${current.trim()} ${transcript}` : transcript,
      );
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  }

  const renderedMessages = useMemo(() => {
    return messages.map((message, index) => {
      const doctors =
        message.role === "assistant" ? parseDoctors(message.content) : null;

      return (
        <div
          key={`${message.role}-${index}`}
          className={`message ${
            message.role === "user" ? "user-message" : "assistant-message"
          }`}
        >
          <div className="message-avatar">
            {message.role === "user" ? "U" : "N"}
          </div>

          <div className="message-content">
            <div
              style={{
                whiteSpace: "pre-wrap",
              }}
            >
              {message.content}
            </div>

            {doctors && (
              <DoctorSelection
                doctors={doctors}
                onSelect={handleDoctorSelection}
              />
            )}

            {readyForConfirmation &&
              index === messages.length - 1 &&
              message.role === "assistant" && (
                <ConfirmationCard
                  onConfirm={handleConfirmation}
                  onEdit={handleEdit}
                />
              )}
          </div>
        </div>
      );
    });
  }, [messages, readyForConfirmation]);

  return (
    <section className="nova-chat">
      <div className="nova-header">
        <div className="nova-title">
          <div className="nova-avatar">N</div>

          <div>
            <h2>Nova AI</h2>
            <p>Medical CRM Assistant</p>
          </div>
        </div>

        <div className={`nova-status ${chatting ? "thinking" : ""}`}>
          <span></span>
          {chatting ? "Thinking..." : "Ready"}
        </div>
      </div>

      {offline && (
        <div className="offline-banner">
          Offline mode: messages are saved and will retry automatically.
        </div>
      )}

      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome">
            <div className="welcome-logo">N</div>

            <h1>Welcome to Nova</h1>

            <p>Describe today's interaction naturally.</p>

            <div className="suggestions">
              <button
                onClick={() =>
                  setChatInput(
                    "I met Dr. Rajesh Sharma regarding diabetes medication.",
                  )
                }
              >
                New Interaction
              </button>

              <button
                onClick={() => setChatInput("Change HCP to Dr. Priya Mehta.")}
              >
                Change Doctor
              </button>

              <button onClick={() => setChatInput("Generate summary.")}>
                AI Summary
              </button>
            </div>
          </div>
        )}

        {renderedMessages}

        {chatting && (
          <div className="message assistant-message">
            <div className="message-avatar">N</div>

            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="input-area">
        <textarea
          ref={inputRef}
          rows={3}
          disabled={chatting}
          value={chatInput}
          placeholder="Describe today's interaction..."
          onChange={(e) => {
            setChatInput(e.target.value);
            window.localStorage.setItem("nova-chat-draft", e.target.value);
          }}
          onKeyDown={onKeyDown}
        />

        <div className="input-actions">
          {(window.SpeechRecognition || window.webkitSpeechRecognition) && (
            <button
              className={`voice-button ${listening ? "listening" : ""}`}
              type="button"
              onClick={toggleVoiceInput}
              disabled={chatting}
              title="Dictate interaction"
            >
              {listening ? "Stop" : "Voice"}
            </button>
          )}
          <button
            disabled={!chatInput.trim() || chatting}
            onClick={() => sendMessage()}
          >
            {chatting ? "Processing..." : "Send"}
          </button>
        </div>
      </div>
    </section>
  );
}
