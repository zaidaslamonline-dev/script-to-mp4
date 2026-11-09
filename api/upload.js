const https = require("node:https");

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "same-origin");
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Use POST." });
  }
  const token = process.env.GITHUB_UPLOAD_TOKEN;
  if (!token) return res.status(503).json({ error: "Upload service is not configured yet." });
  const type = String(req.headers["content-type"] || "").split(";")[0].toLowerCase();
  const allowed = { "audio/mpeg": "voiceover.mp3", "audio/wav": "voiceover.wav", "audio/x-wav": "voiceover.wav" };
  if (!allowed[type]) return res.status(415).json({ error: "Upload an MP3 or WAV voiceover." });
  const chunks = [];
  let size = 0;
  try {
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 3 * 1024 * 1024) {
        res.status(413).json({ error: "This first upload endpoint accepts files up to 3 MB. MP3 is recommended." });
        req.destroy();
        return;
      }
      chunks.push(chunk);
    }
    if (!size) return res.status(400).json({ error: "The uploaded file is empty." });
    const content = Buffer.concat(chunks).toString("base64");
    const path = "content/" + allowed[type];
    const body = JSON.stringify({
      message: "Upload supplied voiceover from production portal",
      content
    });
    const options = {
      hostname: "api.github.com",
      path: "/repos/zaidaslamonline-dev/script-to-mp4/contents/" + path,
      method: "PUT",
      headers: {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fixreach-production-portal",
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body)
      }
    };
    const result = await new Promise((resolve, reject) => {
      const r = https.request(options, response => {
        let data = "";
        response.setEncoding("utf8");
        response.on("data", part => data += part);
        response.on("end", () => resolve({ status: response.statusCode, data }));
      });
      r.on("error", reject);
      r.write(body);
      r.end();
    });
    if (result.status < 200 || result.status >= 300) {
      return res.status(502).json({ error: "GitHub rejected the upload. Check the portal's repository token configuration.", detail: "HTTP " + result.status });
    }
    return res.status(200).json({ ok: true, path, bytes: size, message: "Voiceover received. The production workflow will start from this upload." });
  } catch (error) {
    return res.status(500).json({ error: "Upload failed.", detail: error.message });
  }
};
