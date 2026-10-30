const { test, after } = require('node:test');
const assert = require('node:assert/strict');
require('tsx/cjs');
const jwt = require('jsonwebtoken');
const twilio = require('twilio');
const { createServer } = require('node:http');
const { once } = require('node:events');
process.env.JWT_SECRET = 'offline-test-secret';
process.env.VOICE_AGENT_PUBLIC_URL = 'https://voice.example.test';
process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN = 'offline-provider-secret';
for (const key of ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_VERIFY_SERVICE_SID', 'ELEVENLABS_API_KEY']) delete process.env[key];

const user = { id: 'alice', phoneNumber: '+15555550100', role: 'FARMER', name: 'Alice' };
const db = {
 user: { findUnique: async () => user },
 land: { findFirst: async () => ({ id: 'land-a', totalArea: 1 }), update: async args => args.data },
 field: { findFirst: async () => null },
 cropAssignment: { findFirst: async () => null },
 aIConversation: { create: async () => { throw new Error('Unexpected write'); } },
 auditLog: { create: async () => ({}) },
};
const dbPath = require.resolve('../src/db.ts');
require.cache[dbPath] = { id: dbPath, filename: dbPath, loaded: true, exports: { db } };
const auth = require('../src/valid/jwt.ts');
const { updateLandValidation } = require('../src/valid/landValid.ts');
const { updateLand } = require('../src/controller/landController.ts');
const { startConversation } = require('../src/controller/chatController.ts');
const security = require('../src/voice-agent/security.ts');
const app = require('../src/app.ts').default;
const originalSetInterval = global.setInterval;
global.setInterval = (...args) => originalSetInterval(...args).unref();
const voiceRoutes = require('../src/voice-agent/voiceAgentRoutes.ts');
global.setInterval = originalSetInterval;
app.use('/api/voice-agent', voiceRoutes.default);
let server;
let base;
async function setup() {
 if (!server) {
  server = createServer(app); voiceRoutes.setupVoiceAgentWebSocket(server);
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  base = `http://127.0.0.1:${server.address().port}`;
 }
}
after(async () => { if (server) { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); } });
const response = () => ({ statusCode: 200, status(n) { this.statusCode=n; return this; }, json(data) { this.body=data; return this; } });
async function verify(middleware, token, refresh=false) {
 const req={ headers: {authorization:`Bearer ${token}`}, cookies:{refreshToken:token} };
 const res=response(); let passed=false;
 middleware(req,res,()=>{passed=true;});
 await new Promise(resolve=>setImmediate(resolve));
 return {req,res,passed};
}

test('JWT purpose separates access and refresh, rejects legacy and expired tokens', async () => {
 const access=auth.signAccessToken(user), refresh=auth.signRefreshToken(user);
 assert.equal((await verify(auth.verifyAccessToken,access)).passed,true);
 assert.equal((await verify(auth.verifyRefreshToken,refresh)).passed,true);
 assert.equal((await verify(auth.verifyAccessToken,refresh)).passed,false);
 assert.equal((await verify(auth.verifyRefreshToken,access)).passed,false);
 for (const claims of [{id:user.id},{id:user.id, token_use:'access', exp:1},{token_use:'access', exp:9999999999}]) {
  assert.equal((await verify(auth.verifyAccessToken,jwt.sign(claims,process.env.JWT_SECRET))).passed,false);
 }
});

test('OTP cannot authenticate with missing configuration', async () => {
 const {OTPService}=require('../src/services/otpService.ts');
 assert.equal(await OTPService.checkVerification(user.phoneNumber,'123456'),false);
 assert.equal(await OTPService.checkVerification(user.phoneNumber,'000000'),false);
 await assert.rejects(OTPService.sendVerification(user.phoneNumber));
});

test('land validator strips nested role escalation and ownership reassignment at actual controller boundary', async () => {
 const safe={name:'My field',corners:[{lat:10,lng:20}],plantedCropManual:'Rice'};
 const req={user,body:{...safe,farmer:{update:{user:{update:{role:'ADMIN'}}}},fields:{connect:{id:'victim'}},farmerId:'victim'},query:{},params:{}};
 const res=response(); let passed=false;
 await updateLandValidation(req,res,()=>{passed=true;});
 assert.equal(passed,true); assert.deepEqual(req.body,safe);
 let written;
 db.land.update=async args => {written=args.data; return args.data;};
 await updateLand(req,res);
 assert.equal(res.statusCode,200); assert.deepEqual(written,safe);
});

test('conversation rejects foreign field and crop links before creation', async () => {
 for(const body of [{fieldId:'foreign'},{cropAssignmentId:'foreign'}]) {
  const res=response(); await startConversation({user,body},res); assert.equal(res.statusCode,404);
 }
 db.field.findFirst=async()=>({id:'own'});
 db.cropAssignment.findFirst=async()=>({id:'own-crop'});
 db.aIConversation.create=async args=>args.data;
 const res=response(); await startConversation({user,body:{fieldId:'own',cropAssignmentId:'own-crop'}},res);
 assert.equal(res.statusCode,201);
});

test('CORS only permits known origins', async () => {
 await setup();
 for (const [origin,allowed] of [['http://localhost:5173',true],['https://evil.example',false],['https://evil.vercel.app',false]]) {
  const res=await fetch(base+'/health',{headers:{Origin:origin}});
  assert.equal(res.headers.get('access-control-allow-origin'),allowed?origin:null);
 }
});

test('public voice operations require login and phone ownership; provider aliases still require signature', async () => {
 await setup();
 for(const path of ['/make-call','/network-fallback']) {
  const res=await fetch(base+'/api/voice-agent'+path,{method:'POST',headers:{'content-type':'application/json'},body:'{}'});
  assert.equal(res.status,401);
 }
 const bearer='Bearer '+auth.signAccessToken(user);
 let res=await fetch(base+'/api/voice-agent/make-call',{method:'POST',headers:{authorization:bearer,'content-type':'application/json'},body:JSON.stringify({phoneNumber:'+15555550200'})});
 assert.equal(res.status,403);
 for(const path of ['/sms-outbound','/request-address']) {
  res=await fetch(base+'/api/voice-agent'+path,{headers:{authorization:bearer}}); assert.equal(res.status,403);
 }
 for(const path of ['/sms-inbound','/SMS-INBOUND/']) {
  res=await fetch(base+'/api/voice-agent'+path,{method:'POST',headers:{authorization:bearer,'content-type':'application/x-www-form-urlencoded'},body:'From=%2B15555550100&Body=forged'});
  assert.equal(res.status,403);
 }
});

test('valid Twilio signature succeeds, forged headers and changed bodies fail', async () => {
 const path='/api/voice-agent/voice'; const body={From:'+15555550100'};
 const signature=twilio.getExpectedTwilioSignature(process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN,'https://voice.example.test'+path,body);
 const req={headers:{'x-twilio-signature':signature}};
 assert.equal(security.validTwilioSignature(req,path,body),true);
 assert.equal(security.validTwilioSignature(req,path,{From:'forged'}),false);
 assert.equal(security.validTwilioSignature({headers:{}},path,body),false);
 await setup();
 const res=await fetch(base+path,{method:'POST',headers:{'content-type':'application/x-www-form-urlencoded','x-twilio-signature':signature},body:new URLSearchParams(body)});
 assert.equal(res.status,200); assert.match(await res.text(),/wss:\/\/voice.example.test\/media-stream/);
 const wsSignature=twilio.getExpectedTwilioSignature(process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN,'wss://voice.example.test/media-stream',{});
 assert.equal(security.validTwilioSignature({headers:{'x-twilio-signature':wsSignature}},'/media-stream',{},true),true);
});

test('phone ownership checks query and body independently', () => {
 const res=response(); let passed=false;
 security.ownPhone({user,body:{phoneNumber:user.phoneNumber},query:{phone:'+15555550200'}},res,()=>{passed=true;});
 assert.equal(passed,false); assert.equal(res.statusCode,403);
 const own=response();
 security.ownPhone({user,body:{},query:{phone:user.phoneNumber}},own,()=>{passed=true;});
 assert.equal(passed,true);
});

test('OTP uses provider approval when configured, and rejects provider errors', async () => {
 const otpPath=require.resolve('../src/services/otpService.ts');
 const twilioPath=require.resolve('twilio');
 const original=require.cache[twilioPath].exports;
 let approved=true, fail=false, sent=0;
 const fake=()=>({verify:{v2:{services:()=>({
  verifications:{create:async()=>{sent++;}},
  verificationChecks:{create:async()=>{if(fail) throw new Error('provider unavailable');return {status:approved?'approved':'pending'};}}
 })}}});
 process.env.TWILIO_ACCOUNT_SID='AC'+'0'.repeat(32);
 process.env.TWILIO_AUTH_TOKEN='test-secret';
 process.env.TWILIO_VERIFY_SERVICE_SID='VA'+'0'.repeat(32);
 try {
  require.cache[twilioPath].exports=fake; delete require.cache[otpPath];
  const {OTPService}=require(otpPath);
  await OTPService.sendVerification(user.phoneNumber); assert.equal(sent,1);
  assert.equal(await OTPService.checkVerification(user.phoneNumber,'654321'),true);
  approved=false; assert.equal(await OTPService.checkVerification(user.phoneNumber,'654321'),false);
  fail=true; assert.equal(await OTPService.checkVerification(user.phoneNumber,'654321'),false);
 } finally {
  require.cache[twilioPath].exports=original; delete require.cache[otpPath];
  for(const key of ['TWILIO_ACCOUNT_SID','TWILIO_AUTH_TOKEN','TWILIO_VERIFY_SERVICE_SID']) delete process.env[key];
 }
});

test('WebSocket upgrade rejects forged signatures and accepts signed provider handshake', async () => {
 await setup();
 const WebSocket=require('ws');
 const wsUrl=base.replace('http:','ws:')+'/media-stream';
 const denied=new WebSocket(wsUrl);
 const status=await new Promise((resolve,reject)=>{
  denied.on('unexpected-response',(_req,res)=>{resolve(res.statusCode);res.resume();denied.terminate();});
  denied.on('error',()=>{}); denied.on('open',()=>reject(new Error('Unsigned upgrade accepted')));
 });
 assert.equal(status,401);
 const signature=twilio.getExpectedTwilioSignature(process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN,'wss://voice.example.test/media-stream',{});
 const allowed=new WebSocket(wsUrl,{headers:{'x-twilio-signature':signature}});
 await once(allowed,'open');
 allowed.send('not-json');
 const [code]=await once(allowed,'close'); assert.equal(code,1008);
});
