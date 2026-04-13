const baseUrl = process.env.GATEWAY_BASE_URL ?? "http://localhost:4000";

const tests = [
  {
    alias: "reasoning-primary",
    prompt: "Give a one-sentence summary of why modular AI infrastructure is useful."
  },
  {
    alias: "fast-cheap",
    prompt: "Return a short bullet list of 2 benefits of lightweight routing."
  }
];

async function run(): Promise<void> {
  for (const test of tests) {
    const response = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: test.alias,
        messages: [{ role: "user", content: test.prompt }],
        temperature: 0.2,
        max_tokens: 120
      })
    });

    const body = await response.json();
    console.log(`\n[${test.alias}] status=${response.status}`);
    console.log(JSON.stringify(body, null, 2));
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
