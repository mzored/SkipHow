# Prototype

Build only when the requested outcome authorizes project changes or explicitly asks for an artifact. Otherwise describe the useful experiment without changing the project. State what the prototype must answer and choose the least fidelity that lets the owner judge it in real use.

For a UI question, place alternatives in the real screen and data context when practical. Make alternatives differ in the decision under test, not in decoration alone. When the choice genuinely belongs to the owner, keep comparison easy enough that they can judge without setup help. Otherwise evaluate the alternatives against the requested outcome and current product evidence yourself.

For a state or logic question, expose the relevant state and exercise the important scenarios. Use domain language in labels and explanations. Keep the decision logic separate enough that a validated part can be implemented cleanly later.

Mark prototype code as disposable. Avoid real production mutations, persistent data, broad abstractions, and polish that does not help answer the question. Make it easy to run with the project's existing tools.

Show the artifact and explain what to evaluate when owner judgment is the requested result. Otherwise use the experiment to settle the reversible technical choice and report the evidence. Once the question is answered, save the conclusion only when the owner asked for a record or an authorized change normally requires one. Implement the chosen behavior properly if requested, and remove prototype code from the delivered product unless the owner wants to keep it.
