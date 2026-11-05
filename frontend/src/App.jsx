import { useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { findCompanies } from "./companies.js";

const NEW_CUSTOMER = "Nieuwe klant";

// dd-mm-yyyy (slashes are not allowed in file names)
function today() {
  return new Date().toLocaleDateString("nl-NL", { day: "2-digit", month: "2-digit", year: "numeric" }).replaceAll("/", "-");
}

export default function App() {
  const [query, setQuery] = useState("");
  const [company, setCompany] = useState(null); // the chosen company, null until picked from the list
  const [isNew, setIsNew] = useState(false); // "Nieuwe klant": free text instead of the list
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [webSearch, setWebSearch] = useState(true);
  const [kvk, setKvk] = useState(false); // mockup only
  const [userInput, setUserInput] = useState(""); // extra info for the agent, sent along as user_input
  const [editingInput, setEditingInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null); // { searches, writing, text, error, company }
  const abortRef = useRef(null); // aborts the running research when the user cancels

  const matches = company ? [] : findCompanies(query);
  // The dropdown always ends with "Nieuwe klant" for companies that aren't in the list
  const options = isNew || company ? [] : [...matches, NEW_CUSTOMER];
  const name = isNew ? query.trim() : company; // the company the research will be about

  function onInput(e) {
    const value = e.target.value;
    if (isNew) {
      setQuery(value);
      return;
    }
    // Only accept text that still matches at least one company
    if (value && findCompanies(value).length === 0) return;
    setQuery(value);
    setCompany(null);
    setActive(0);
    setOpen(true);
  }

  function choose(option) {
    if (option === NEW_CUSTOMER) {
      setIsNew(true);
      setQuery("");
      setCompany(null);
    } else {
      setQuery(option);
      setCompany(option);
    }
    setOpen(false);
  }

  function backToList() {
    setIsNew(false);
    setQuery("");
    setCompany(null);
  }

  function onKeyDown(e) {
    if (!open || options.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % options.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + options.length) % options.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(options[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  async function submit(e) {
    e.preventDefault();
    if (!name || loading) return;

    let searches = [];
    let writing = false; // research is done, the report agent is writing
    let text = "";
    const update = (extra = {}) => setAnswer({ searches: [...searches], writing, text, error: null, company: name, ...extra });

    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    update();

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: name, website: webSearch, kvk, user_input: userInput.trim() }),
        signal: controller.signal,
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines.filter(Boolean)) {
          const event = JSON.parse(line);
          if (event.type === "search") {
            searches.push(event.value);
            update();
          } else if (event.type === "research") {
            writing = true;
            update();
          } else if (event.type === "text") {
            text += (text ? "\n\n" : "") + event.value;
            update();
          } else if (event.type === "error") {
            update({ error: "Er ging iets mis: " + event.value });
          }
        }
      }
    } catch {
      update({ error: controller.signal.aborted ? "Onderzoek geannuleerd." : "Kan de server niet bereiken." });
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  }

  // Closing the request also stops the agent on the server
  function cancel() {
    abortRef.current?.abort();
  }

  // The server turns the report markdown into a text-based PDF, which is saved straight away
  async function downloadPdf() {
    const company = answer.company.replace(/[\\/:*?"<>|]/g, "").trim();
    try {
      const res = await fetch("/api/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: answer.text }),
      });
      if (!res.ok) throw new Error();
      const url = URL.createObjectURL(await res.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = `werkingssfeeronderzoek_${company}_${today()}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setAnswer((a) => ({ ...a, error: "De PDF kon niet worden gemaakt." }));
    }
  }

  return (
    <>
      <header>
        <div className="header-inner">
          <div className="logo">
            AAFF<span>.</span>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="hero-inner">
          <h1>Begin je wso</h1>
          <p>
            Start met het invullen van de bedrijfsnaam. Kies daarna welke bronnen je wilt gebruiken
          </p>
        </div>
      </section>

      <main>
        <form className="composer" onSubmit={submit}>
          <div className="combo">
            <input
              type="text"
              role="combobox"
              aria-expanded={open && options.length > 0}
              aria-controls="company-list"
              aria-autocomplete="list"
              autoComplete="off"
              value={query}
              onChange={onInput}
              onKeyDown={onKeyDown}
              onFocus={() => setOpen(true)}
              onBlur={() => setOpen(false)}
              placeholder={
                isNew
                  ? "Typ de naam van de nieuwe klant"
                  : "Typ een bedrijfsnaam, bijvoorbeeld FrieslandCampina"
              }
            />
            {open && options.length > 0 && (
              <ul className="suggestions" id="company-list" role="listbox">
                {options.map((option, i) => (
                  <li
                    key={option}
                    role="option"
                    aria-selected={i === active}
                    className={(i === active ? "active " : "") + (option === NEW_CUSTOMER ? "new" : "")}
                    onMouseEnter={() => setActive(i)}
                    onMouseDown={(e) => {
                      e.preventDefault(); // keep focus so the click isn't lost to blur
                      choose(option);
                    }}
                  >
                    {option === NEW_CUSTOMER ? "+ " : ""}
                    {option}
                  </li>
                ))}
              </ul>
            )}
            {!name && (
              <div className="hint">
                {isNew ? "Vul de naam van de nieuwe klant in" : "Kies een bedrijf uit de lijst"}
              </div>
            )}
            {isNew && (
              <button type="button" className="back" onClick={backToList}>
                &larr; Kies een bestaande klant
              </button>
            )}
          </div>
          <div className="actions">
            <div className="actions-left">
              <div className="sources">
                <button
                  type="button"
                  className="toggle"
                  aria-pressed={webSearch}
                  onClick={() => setWebSearch((on) => !on)}
                >
                  <span className="switch" /> Website
                </button>
                {/* Mockup: not connected to the backend yet */}
                <button
                  type="button"
                  className="toggle"
                  aria-pressed={kvk}
                  onClick={() => setKvk((on) => !on)}
                >
                  <span className="switch" /> KVK
                </button>
              </div>
              <div className="extra">
                {editingInput ? (
                  // The value is already in state while typing, so leaving the field is all it takes to keep it
                  <div className="extra-edit">
                    <input
                      type="text"
                      autoFocus
                      autoComplete="off"
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onBlur={() => setEditingInput(false)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === "Escape") {
                          e.preventDefault(); // Enter would otherwise submit the form
                          e.currentTarget.blur();
                        }
                      }}
                      placeholder="Extra informatie voor het onderzoek"
                    />
                    <button
                      type="button"
                      className="confirm"
                      aria-label="Bewaar extra informatie"
                      onMouseDown={(e) => {
                        e.preventDefault(); // keep focus until we close, same effect as clicking outside
                        setEditingInput(false);
                      }}
                    >
                      &rarr;
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className="toggle extra-btn"
                      aria-pressed={!!userInput}
                      title={userInput || undefined}
                      onClick={() => setEditingInput(true)}
                    >
                      <span className="extra-label">Extra informatie</span>
                    </button>
                    {userInput && (
                      <button
                        type="button"
                        className="clear"
                        aria-label="Wis extra informatie"
                        title="Wis"
                        onClick={() => setUserInput("")}
                      >
                        &times;
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="actions-right">
              {loading ? (
                <button type="button" className="cancel" onClick={cancel}>
                  Annuleer onderzoek
                </button>
              ) : (
                <button type="submit" className="send" disabled={!name}>
                  Begin onderzoek &rarr;
                </button>
              )}
            </div>
          </div>
        </form>

        {answer && (
          <section className="answer">
            {answer.searches.length > 0 &&
              (loading && !answer.writing ? (
                // Carousel: only the latest search is visible, each new one slides in over the previous
                <div className="ticker" aria-live="polite">
                  <span className="pulse" />
                  <span className="ticker-item" key={answer.searches.length}>
                    Zoekt: {answer.searches.at(-1)}
                  </span>
                </div>
              ) : (
                <details className="searches">
                  <summary>{answer.searches.length} zoekacties uitgevoerd</summary>
                  <ul>
                    {answer.searches.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </details>
              ))}
            {answer.text && !answer.error && (
              <button type="button" className="download" disabled={loading} onClick={downloadPdf}>
                Download PDF
              </button>
            )}
            <div id="output">
              {answer.error ? (
                <p className="error">{answer.error}</p>
              ) : answer.text ? (
                <Markdown remarkPlugins={[remarkGfm]}>{answer.text}</Markdown>
              ) : (
                <p className="status">{answer.writing ? "Rapport wordt geschreven…" : "Onderzoek gestart…"}</p>
              )}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
