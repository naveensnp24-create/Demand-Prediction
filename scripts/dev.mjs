import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')
const python=path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python')
const vite=path.join(root,'frontend/node_modules/vite/bin/vite.js')
if(!existsSync(python)||!existsSync(vite)) {
  console.error('Dependencies are missing. Follow README.md setup instructions first.')
  process.exit(1)
}
const backend=spawn(python,['-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],{cwd:root,stdio:'inherit',windowsHide:true})
const frontend=spawn(process.execPath,[vite,'--host','127.0.0.1','--port','5173','--strictPort'],{cwd:path.join(root,'frontend'),stdio:'inherit',windowsHide:true})
let stopping=false
function stop(code=0) {
  if(stopping)return
  stopping=true
  for (const child of [backend, frontend]) {
    if (!child.pid || child.exitCode !== null) continue
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], {windowsHide:true,stdio:'ignore'})
    } else child.kill()
  }
  process.exitCode=code
}
for(const child of [backend,frontend]) {
  child.on('error',error=>{console.error(error.message);stop(1)})
  child.on('exit',code=>stop(code||0))
}
process.on('SIGINT',()=>stop())
process.on('SIGTERM',()=>stop())
console.log('DemandPredict: http://127.0.0.1:5173 | API docs: http://127.0.0.1:8000/docs')
