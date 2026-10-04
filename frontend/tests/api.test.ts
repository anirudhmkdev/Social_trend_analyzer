import { test, afterEach } from "node:test";
import assert from "node:assert/strict";
import { api, ApiError, fetchJson } from "../src/lib/api";

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; });
test("dataset list preserves the response envelope", async () => {
  globalThis.fetch = async () => Response.json({ datasets: [{ id: "dataset-a" }], total: 1 });
  const result = await api.getDatasets();
  assert.equal(result.total, 1);
  assert.equal(result.datasets[0].id, "dataset-a");
});
test("search sends canonical dataset/run and all server filters", async () => {
  globalThis.fetch = async input => {
    const url = new URL(String(input));
    for (const [key, value] of Object.entries({ dataset_id: "d", analysis_run_id: "r", platform: "reddit", sentiment: "positive", topic_id: "t", q: "100% AI_", offset: "20", limit: "20", date_from: "2026-09-01T00:00:00Z" })) assert.equal(url.searchParams.get(key), value);
    return Response.json({ items: [], total: 30, offset: 20, limit: 20 });
  };
  assert.equal((await api.searchPosts({ dataset_id: "d", analysis_run_id: "r", platform: "reddit", sentiment: "positive", topic_id: "t", q: "100% AI_", offset: 20, limit: 20, date_from: "2026-09-01T00:00:00Z" })).total, 30);
});
test("upload sends one multipart body without a JSON content type", async () => {
  globalThis.fetch = async (_input, options) => {
    assert.ok(options?.body instanceof FormData);
    assert.equal(new Headers(options.headers).has("Content-Type"), false);
    return Response.json({ id: "staged" }, { status: 201 });
  };
  assert.equal((await api.uploadDataset(new File(["body,when"], "fixture.csv"))).id, "staged");
});
test("backend and unavailable errors remain actionable", async () => {
  globalThis.fetch = async () => Response.json({ error: "Import this dataset first." }, { status: 409 });
  await assert.rejects(fetchJson("/analysis/run"), (error: unknown) => error instanceof ApiError && error.status === 409 && error.message.includes("Import"));
  globalThis.fetch = async () => { throw new TypeError("offline"); };
  await assert.rejects(fetchJson("/datasets"), /Start the backend/);
});
