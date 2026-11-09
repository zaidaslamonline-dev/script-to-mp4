const https = require("node:https");
function gh(method, path, token, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : "";
    const req = https.request({
      hostname: "api.github.com", path, method,
      headers: {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fixreach-production-portal",
        ...(body ? {"Content-Type":"application/json","Content-Length":Buffer.byteLength(payload)} : {})
      }
    }, response => {
      let data = "";
      response.setEncoding("utf8");
      response.on("data", part => data += part);
      response.on("end", () => resolve({status:response.statusCode,data}));
    });
    req.on("error", reject);
    if (payload) req.write(payload);
    req.end();
  });
}
module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") { res.setHeader("Allow","POST"); return res.status(405).json({error:"Use POST."}); }
  const token=process.env.GITHUB_UPLOAD_TOKEN;
  if (!token) return res.status(503).json({error:"Upload service is awaiting its one-time repository connection."});
  const type=String(req.headers["content-type"]||"").split(";")[0].toLowerCase();
  if (type!=="audio/mpeg") return res.status(415).json({error:"For now, upload MP3. The workflow converts it to the production WAV automatically."});
  const chunks=[]; let size=0;
  try {
    for await (const chunk of req) {
      size+=chunk.length;
      if(size>3*1024*1024) return res.status(413).json({error:"Maximum upload size is 3 MB. MP3 is recommended."});
      chunks.push(chunk);
    }
    if(!size) return res.status(400).json({error:"The uploaded file is empty."});
    const path="content/voiceover.mp3";
    const existing=await gh("GET","/repos/zaidaslamonline-dev/script-to-mp4/contents/"+path,token);
    let sha;
    if(existing.status===200) sha=JSON.parse(existing.data).sha;
    else if(existing.status!==404) return res.status(502).json({error:"Could not check the existing voiceover file.",detail:"GitHub HTTP "+existing.status});
    const payload={message:"Upload supplied voiceover from production portal",content:Buffer.concat(chunks).toString("base64")};
    if(sha) payload.sha=sha;
    const saved=await gh("PUT","/repos/zaidaslamonline-dev/script-to-mp4/contents/"+path,token,payload);
    if(saved.status<200||saved.status>=300) return res.status(502).json({error:"GitHub rejected the voiceover upload.",detail:"GitHub HTTP "+saved.status});
    return res.status(200).json({ok:true,path,bytes:size,message:"Voiceover received. Production workflow is starting."});
  } catch(e) { return res.status(500).json({error:"Upload failed.",detail:e.message}); }
};
