import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { findCompanies } from "./companies.js";

const NEW_CUSTOMER = "Nieuwe klant";

export default function App() {
  const [query, setQuery] = useState("");
  const [company, setCompany] = useState(null); // the chosen company, null until picked from the list
  const [isNew, setIsNew] = useState(false); // "Nieuwe klant": free text instead of the list
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [webSearch, setWebSearch] = useState(true);
  const [kvk, setKvk] = useState(false); // mockup only
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null); // { searches, text, error }

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
    let text = "";
    const update = (extra = {}) => setAnswer({ searches: [...searches], text, error: null, ...extra });

    setLoading(true);
    update();

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: name, website: webSearch, kvk }),
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
          } else if (event.type === "text") {
            text += (text ? "\n\n" : "") + event.value;
            update();
          } else if (event.type === "error") {
            update({ error: "Er ging iets mis: " + event.value });
          }
        }
      }
    } catch {
      update({ error: "Kan de server niet bereiken." });
    } finally {
      setLoading(false);
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
            {isNew && (
              <button type="button" className="back" onClick={backToList}>
                &larr; Kies een bestaande klant
              </button>
            )}
          </div>
          <div className="actions">
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
            <div className="actions-right">
              {!name && (
                <span className="hint">
                  {isNew ? "Vul de naam van de nieuwe klant in" : "Kies een bedrijf uit de lijst"}
                </span>
              )}
              <button type="submit" className="send" disabled={loading || !name}>
                Begin onderzoek &rarr;
              </button>
            </div>
          </div>
        </form>

        {answer && (
          <section className="answer">
            {answer.searches.length > 0 && (
              <div className="searches">
                {answer.searches.map((s, i) => (
                  <span className="chip" key={i}>
                    Zoekt: {s}
                  </span>
                ))}
              </div>
            )}
            <div id="output">
              {answer.error ? (
                <p className="error">{answer.error}</p>
              ) : answer.text ? (
                <Markdown remarkPlugins={[remarkGfm]}>{answer.text}</Markdown>
              ) : (
                <p className="status">Bezig met nadenken…</p>
              )}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
