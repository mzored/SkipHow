# Prototype

Build only when the requested outcome authorizes project changes or explicitly asks for an artifact. Otherwise describe the useful experiment without changing the project. State the single question the prototype must answer and choose the least fidelity that lets the owner judge it in real use.

For a UI question, place alternatives in the real screen and data context when practical. Make alternatives differ in the decision under test, not in decoration alone. Keep switching or comparison easy enough that a nontechnical owner can judge without setup help.

For a state or logic question, expose the relevant state and let the owner drive the important scenarios. Use domain language in labels and explanations. Keep the decision logic separate enough that a validated part can be implemented cleanly later.

Mark prototype code as disposable. Avoid real production mutations, persistent data, broad abstractions, and polish that does not help answer the question. Make it easy to run with the project's existing tools.

Show the artifact and explain what to evaluate. Once the question is answered, save the conclusion only when the owner asked for a record or an authorized change normally requires one. Implement the chosen behavior properly if requested, and remove prototype code from the delivered product unless the owner wants to keep it.
