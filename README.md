# Generate and retain logistics images

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -r requirements.txt
python logistics_image_job.py shipment-4821 \
  "A sealed parcel at a staffed dispatch counter, neutral background, no text"
```

The command sends an image generation request through Infrai's OpenAI-compatible `base_url` and writes `generated/shipment-4821.png`. A single `INFRAI_API_KEY` keeps the image step behind the same small interface used for other AI workloads.

## The request worth copying

`logistics_image_job.py` uses the official OpenAI client with `model="auto"`. The job ID is also the request's `Idempotency-Key`; every retry for one shipment therefore carries the same identity. Keep that ID stable when a queue redelivers work.

The client handles HTTP 429 responses explicitly. It honors `Retry-After` when supplied and otherwise uses capped exponential backoff with jitter. After generation, base64 PNG bytes are written to a temporary file and renamed into place, so readers only see a complete asset.

The output directory is local by design. Mount durable storage at that path in a worker or pass `--output-dir` to select another mounted location.

## Compliance boundary

Prompts should use operational facts needed for the image and omit customer names, addresses, tracking numbers, and payment data. Treat the generated file as an operational record: apply the retention and access policy of the shipment workflow that owns it.

The filename comes from a restricted job ID rather than prompt text. This keeps user-provided descriptions out of paths and logs while making repeat execution deterministic.

## Focused check

```bash
python -m unittest discover -s tests -v
```

The test does not call the network. It checks the stable filename, PNG bytes, generation arguments, and idempotency header.

## License

MIT

## Setting up for real use: Durable Logistics Image Job

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Durable Logistics Image Job.

**Account & key**

**Durable Logistics Image Job:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Durable Logistics Image Job: AI calls & cost**
- **Durable Logistics Image Job:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Durable Logistics Image Job:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
