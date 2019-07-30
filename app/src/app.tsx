import "./app.css";

import * as React from "react";
import { RuleResult } from "./result";
import { EvaluationResultT, Course, Transcript } from "./types";
import { StatusIcon } from "./components";

export function App() {
  return <Data>{props => <Contents {...props} />}</Data>;
}

type InnerProps = {
  result: null | EvaluationResultT;
  transcript: Transcript;
  error: null | object;
};

function Contents({ result, transcript, error }: InnerProps) {
  if (error) {
    return <pre>{JSON.stringify(error, null, 2)}</pre>;
  }

  if (!result) {
    return <p>That student's audit is not yet complete.</p>;
  }

  return (
    <article className="degreepath">
      <RuleResult result={result} topLevel={true} transcript={transcript} />
    </article>
  );
}

function Data({ children }: { children: typeof Contents }) {
  let { __dpResult: _r, __dpError: _e, __dpTranscript: _t } = window as any;

  if (process.env.NODE_ENV === "development") {
    _r = _r || JSON.parse(localStorage.getItem("dp-result") || "null");
    _t = _t || JSON.parse(localStorage.getItem("dp-transcript") || "null");
  }

  let [error, setError] = React.useState<null | object>(_e);
  let [result, setResult] = React.useState<null | EvaluationResultT>(_r);
  let [transcript, setTranscript] = React.useState<Course[]>(_t || []);

  transcript = transcript || [];

  let [transcriptError, setTrError] = React.useState(false);
  let [resultError, setRsError] = React.useState(false);

  let setSerializedError = (err: Error) => {
    setError({ error: err.message });
  };

  let transcriptRef = React.useRef<null | HTMLTextAreaElement>(null);
  let resultRef = React.useRef<null | HTMLTextAreaElement>(null);

  let processData = (ev: React.SyntheticEvent) => {
    console.log("submitting...");
    ev.preventDefault();

    let currentOrNull = (ref: React.MutableRefObject<any>) =>
      ref.current && ref.current.value ? ref.current.value : "null";

    try {
      let v = currentOrNull(transcriptRef);
      let studentOrTranscript = JSON.parse(v);
      if (Array.isArray(studentOrTranscript)) {
        setTranscript(studentOrTranscript);
        localStorage.setItem(
          "dp-transcript",
          JSON.stringify(studentOrTranscript),
        );
      } else {
        setTranscript(studentOrTranscript.courses);
        localStorage.setItem(
          "dp-transcript",
          JSON.stringify(studentOrTranscript.courses),
        );
      }
      setTrError(false);
    } catch (error) {
      setSerializedError(error);
      setTrError(true);
      localStorage.removeItem("dp-transcript");
    }

    try {
      let v = currentOrNull(resultRef);
      localStorage.setItem("dp-result", v);
      setResult(JSON.parse(v));
      setRsError(false);
    } catch (error) {
      setSerializedError(error);
      setRsError(true);
      localStorage.removeItem("dp-result");
    }
  };

  let transcriptMap: Transcript = new Map(transcript.map(c => [c.clbid, c]));

  return (
    <>
      {process.env.NODE_ENV === "development" ? (
        <form onSubmit={processData}>
          <label>Transcript</label>
          <textarea
            ref={transcriptRef}
            name="transcript"
            placeholder="transcript"
            defaultValue={JSON.stringify(_t)}
            style={{
              border: transcriptError ? "solid 2px #FF4136" : "default",
            }}
          />

          <label>Result</label>
          <textarea
            ref={resultRef}
            name="result"
            placeholder="result"
            defaultValue={JSON.stringify(_r)}
            style={{
              border: resultError ? "solid 2px #FF4136" : "default",
            }}
          />

          <button type="submit">Load</button>
        </form>
      ) : null}

      {children({ result, error, transcript: transcriptMap })}
    </>
  );
}
