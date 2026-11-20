import fs from 'node:fs';
import { ANTIGRAVITY_CLIENT_ID, ANTIGRAVITY_CLIENT_SECRET, ANTIGRAVITY_REDIRECT_URI, ANTIGRAVITY_SCOPES, buildAntigravityLoadCodeAssistMetadata, fetchWithAgyCliTransport, buildAntigravityHarnessUserAgent, buildAgyAgentRequestMetadata, createAgyRequestSessionContext, orderAgyRequestPayloadInPlace, applyGeminiTransforms } from '@cortexkit/antigravity-auth-core';
// Header wait includes inference/prefill on large contexts, not just network RTT.
// Keep the helper's total deadline below Python's process deadline (330s).
const HEADER_TIMEOUT_MS=120000, IDLE_TIMEOUT_MS=120000, TOTAL_TIMEOUT_MS=300000;
const action=process.argv[2];
if(action==='config') {
  process.stdout.write(JSON.stringify({clientId:ANTIGRAVITY_CLIENT_ID,clientSecret:ANTIGRAVITY_CLIENT_SECRET,redirectUri:ANTIGRAVITY_REDIRECT_URI,scopes:ANTIGRAVITY_SCOPES,metadata:buildAntigravityLoadCodeAssistMetadata()}));
} else if(action==='request') {
  let input=''; for await(const x of process.stdin) {input+=x; if(input.length>16*1024*1024) throw new Error('Request too large');}
  const x=JSON.parse(input);
  const u=new URL(x.url);
  const allowed=['daily-cloudcode-pa.googleapis.com','cloudcode-pa.googleapis.com'];
  if(u.protocol!=='https:' || !allowed.includes(u.hostname) || u.port || !['/v1internal:loadCodeAssist','/v1internal:fetchAvailableModels','/v1internal:streamGenerateContent','/v1internal:onboardUser','/v1internal:retrieveUserQuotaSummary'].includes(u.pathname)) throw new Error('Endpoint rejected');
  let body=x.body;
  if(u.pathname.includes('streamGenerateContent')) {
    applyGeminiTransforms(body.request,{model:body.model});
    const ctx=createAgyRequestSessionContext('hermes-antigravity-direct');
    const meta=buildAgyAgentRequestMetadata(ctx,body.request,body.model);
    body.request.labels=meta.labels; body.request.sessionId=meta.sessionId;
    orderAgyRequestPayloadInPlace(body.request);
    body={project:body.project,requestId:meta.requestId,request:body.request,model:body.model,userAgent:'antigravity',requestType:'agent'};
  }
  try{fs.writeFileSync(new URL('./last-request.json', import.meta.url), JSON.stringify({url:x.url, model:x.body&&x.body.model, body:x.body}, null, 1));}catch{}  // diagnostic dump, no token
  const controller=new AbortController();
  const started=Date.now();
  let phase='connect', bytes=0, headerMs=null;
  const timer=setTimeout(()=>controller.abort(),TOTAL_TIMEOUT_MS);
  try {
    const res=await fetchWithAgyCliTransport(x.url,{method:'POST',headers:{'User-Agent':buildAntigravityHarnessUserAgent(),'X-Hermes-Attribution':'hermes-antigravity-direct/0.1.0',Authorization:'Bearer '+x.token,'Content-Type':'application/json','Accept-Encoding':'gzip'},body:JSON.stringify(body)},{timeoutMs:HEADER_TIMEOUT_MS,idleTimeoutMs:IDLE_TIMEOUT_MS,signal:controller.signal,onDebug:(s)=>{if(s.startsWith('agy transport request dispatched')) phase='headers';}});
    headerMs=Date.now()-started; phase='body';
    const OK=res.status>=200&&res.status<300;  // agy wrapper sets ok=false even on 200
    let text='';
    const decoder = new TextDecoder('utf-8');
    if(res.body) for await(const chunk of res.body) {bytes+=chunk.byteLength; if(bytes>8*1024*1024) throw new Error('Response too large'); text+=decoder.decode(chunk, {stream: true});}
    text += decoder.decode();
    phase='parse';
    const events=[];
    if(OK) {
      if(text.trim().startsWith('{') || text.trim().startsWith('[')) {const v=JSON.parse(text); events.push(...(Array.isArray(v)?v:[v]));}
      else for(const frame of text.replaceAll('\r\n','\n').split('\n\n')) {const data=frame.split('\n').filter(l=>l.startsWith('data:')).map(l=>l.slice(5).trimStart()).join('\n'); if(data && data!=='[DONE]') events.push(JSON.parse(data));}
    }
    let errorMessage=null, verificationUrls=[], rawError=null;
    if(!OK) {try {const parsed=JSON.parse(text);errorMessage=String(parsed.error?.message || '').slice(0,2000); verificationUrls=[...new Set((JSON.stringify(parsed.error?.details || []).match(/https:\/\/[^\s"<>]+/g) || []).filter(s=>{try {const h=new URL(s).hostname;return h==='google.com'||h.endsWith('.google.com');} catch {return false;}}))];} catch {}}
    const wireLog=(m)=>{try{fs.appendFileSync(new URL('./wire-errors.log', import.meta.url), new Date().toISOString()+' '+m+'\n');}catch{}};
      // The agy CLI transport can return error statuses with an empty body. When the
      // rejection carries no reason, re-send once over plain Node fetch (proxy comes
      // from NODE_USE_ENV_PROXY) purely to capture the real error body for the log.
      // The original request was already rejected, so this cannot double-charge.
      if(!errorMessage) {
        try {
          const res2=await fetch(x.url,{method:'POST',headers:{'User-Agent':buildAntigravityHarnessUserAgent(),'X-Hermes-Attribution':'hermes-antigravity-direct/0.1.0',Authorization:'Bearer '+x.token,'Content-Type':'application/json','Accept-Encoding':'gzip'},body:JSON.stringify(body),signal:AbortSignal.timeout(60000)});
          let t2=''; try {t2=await res2.text();} catch {}
          try {const p2=JSON.parse(t2); if(p2.error?.message) errorMessage=String(p2.error.message).slice(0,2000);} catch {}
          rawError='status2='+res.status+' statusProbe='+res2.status+' retryAfter='+(res2.headers.get('retry-after')||'')+' bytes2='+(t2||'').length+' '+String(t2||'').replace(/[\r\n]+/g,' ').slice(0,500);
        } catch(e2) {rawError='status2='+res.status+' probe_failed='+String(e2 && e2.message || '').slice(0,120);}
      wireLog('HTTP '+res.status+' '+(errorMessage||'')+' '+(rawError||''));
      }
    // Non-JSON rejections (plain-text rate-limit walls) carry no error.message; keep a
    // bounded raw snippet so the reason is not lost — 429 can come back as text/HTML.
    if(!errorMessage) rawError=String(text || '').replace(/[\r\n]+/g,' ').slice(0,600);
    process.stdout.write(JSON.stringify({status:res.status,events,errorMessage,rawError,verificationUrls,timing:{elapsedMs:Date.now()-started,headerMs,bytes}}));
  } catch(error) {
    // Never serialize raw messages/stacks: upstream errors can contain credentials.
    const timeout=/timed out|timeout|stalled/i.test(String(error?.message || ''));
    const classes=new Set(['Error','TypeError','SyntaxError','AbortError']);
    const codes=new Set(['ECONNRESET','ECONNREFUSED','ETIMEDOUT','EPIPE','ENOTFOUND','EAI_AGAIN','ERR_STREAM_PREMATURE_CLOSE','Z_DATA_ERROR']);
    const code=controller.signal.aborted?'TOTAL_TIMEOUT':timeout?(phase==='body'?'IDLE_TIMEOUT':phase==='connect'?'CONNECT_TIMEOUT':'HEADER_TIMEOUT'):phase==='parse'?'INVALID_RESPONSE':error?.message==='Response too large'?'RESPONSE_LIMIT':codes.has(error?.code)?error.code:'TRANSPORT_ERROR';
    process.stdout.write(JSON.stringify({transportError:{class:classes.has(error?.name)?error.name:'Error',code,phase,elapsedMs:Date.now()-started,headerMs,bytes}}));
    process.exitCode=1;
  } finally {clearTimeout(timer);}
} else throw new Error('Unsupported wire action');
