import asyncio
import json
import queue
import threading
import time
import traceback
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

# Import our main orchestrator
from backend.orchestrator import NeuroOrchestrator

dashboard_app = FastAPI(title="NeuroOps Control Center")

# Global Event Queue for real-time logging
event_queue = queue.Queue()

# Global lock for approval handling
approval_lock = threading.Lock()
approval_decision = {"status": "resolved", "result": True}

class GoalRequest(BaseModel):
    goal: str

class ApprovalRequest(BaseModel):
    approved: bool

# Custom Logger that pushes events to the UI
class DashboardLogger:
    def log(self, agent: str, message: str, level: str = "info", is_code: bool = False):
        event_queue.put({
            "type": "log",
            "agent": agent,
            "message": message,
            "level": level,
            "isCode": is_code,
            "timestamp": time.strftime("%H:%M:%S")
        })

    def request_approval(self, message: str, task_data: dict = None) -> bool:
        with approval_lock:
            approval_decision["status"] = "waiting"
            approval_decision["message"] = message
            approval_decision["data"] = task_data
        
        event_queue.put({
            "type": "approval",
            "message": message,
            "data": task_data
        })
        
        while True:
            with approval_lock:
                if approval_decision["status"] == "resolved":
                    result = approval_decision["result"]
                    approval_decision["status"] = "pending"
                    approval_decision["result"] = None
                    return result
            time.sleep(0.2)

# The HTML Template (Updated JS to handle errors better)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroOps Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; }
        .log-entry { border-left-width: 3px; }
        .code-block { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 6px; overflow-x: auto; font-family: 'Fira Code', monospace; font-size: 0.85rem; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1f2937; }
        ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 4px; }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 h-screen flex flex-col overflow-hidden" x-data="agentApp()" x-init="initStream()">

    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 p-4 flex justify-between items-center shadow-md z-10">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center font-bold text-black">N</div>
            <h1 class="text-xl font-bold tracking-wide">NeuroOps <span class="text-green-400 text-sm font-normal">Control Center</span></h1>
        </div>
        <div class="flex items-center gap-4">
            <div class="text-xs text-gray-400">Status:</div>
            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider transition-colors duration-300"
                  :class="{
                      'bg-gray-600 text-gray-200': status === 'idle',
                      'bg-blue-600 text-white animate-pulse': status === 'running',
                      'bg-yellow-600 text-white': status === 'waiting_approval'
                  }"
                  x-text="status.replace('_', ' ')"></span>
        </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
        <!-- Left Panel: Controls -->
        <div class="w-1/3 min-w-[350px] bg-gray-800 border-r border-gray-700 flex flex-col p-6 gap-6 shadow-xl z-10">
            
            <!-- Input Area -->
            <div class="flex flex-col gap-2">
                <label class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Mission Goal</label>
                <textarea x-model="goal" 
                    class="w-full h-40 bg-gray-900 border border-gray-700 rounded-lg p-4 text-white focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none resize-none transition-all placeholder-gray-600"
                    placeholder="e.g., Search for latest AI news..."></textarea>
            </div>

            <!-- Action Button -->
            <button @click="startExecution" :disabled="status === 'running' || status === 'waiting_approval'" 
                class="w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg font-bold text-white shadow-lg transform active:scale-95 transition-all">
                <span x-show="status !== 'running'">🚀 Launch Agent</span>
                <span x-show="status === 'running'">⚙️ Processing...</span>
            </button>

            <!-- Approval Card -->
            <div x-show="status === 'waiting_approval'" 
                 class="bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-5 animate-fade-in">
                <div class="flex items-start gap-3 mb-3">
                    <span class="text-2xl">⚠️</span>
                    <div>
                        <h3 class="font-bold text-yellow-400">Action Requires Approval</h3>
                        <p class="text-sm text-yellow-200/80 mt-1" x-text="approvalMessage"></p>
                    </div>
                </div>
                <div class="flex gap-3 mt-4">
                    <button @click="handleApproval(true)" class="flex-1 bg-green-600 hover:bg-green-500 py-2 rounded font-semibold text-sm transition">✅ Approve</button>
                    <button @click="handleApproval(false)" class="flex-1 bg-red-600 hover:red-500 py-2 rounded font-semibold text-sm transition">❌ Reject</button>
                </div>
            </div>

            <!-- Stats -->
            <div class="mt-auto pt-6 border-t border-gray-700">
                <div class="grid grid-cols-2 gap-4 text-xs text-gray-500">
                    <div>Model: <span class="text-gray-300">Qwen 1.5B</span></div>
                    <div>Mode: <span class="text-gray-300">Low RAM</span></div>
                    <div>Tools: <span class="text-gray-300">Obsidian, Web, Py</span></div>
                    <div>Logs: <span class="text-gray-300" x-text="logs.length"></span></div>
                </div>
            </div>
        </div>

        <!-- Right Panel: Live Logs -->
        <div class="flex-1 bg-gray-900 flex flex-col relative">
            <div class="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-gray-900 to-transparent z-10 pointer-events-none">
                <h2 class="text-sm font-bold text-gray-500 uppercase tracking-widest">Live Execution Stream</h2>
            </div>
            
            <div class="flex-1 overflow-y-auto p-6 pb-20 space-y-4" id="log-container">
                <template x-for="(log, index) in logs" :key="index">
                    <div class="log-entry pl-4 py-2 rounded-r bg-gray-800/50"
                         :class="{
                             'border-blue-500': log.level === 'info',
                             'border-green-500': log.level === 'success',
                             'border-red-500': log.level === 'error',
                             'border-yellow-500': log.level === 'warning'
                         }">
                        <div class="flex justify-between items-baseline mb-1">
                            <span class="text-xs font-bold text-gray-400 uppercase" x-text="'[' + log.agent + ']'"></span>
                            <span class="text-[10px] text-gray-600" x-text="log.timestamp"></span>
                        </div>
                        
                        <div x-show="!log.isCode" class="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed" x-text="log.message"></div>
                        
                        <div x-show="log.isCode" class="mt-2">
                            <div class="code-block">
                                <pre><code class="language-python" x-html="highlightCode(log.message)"></code></pre>
                            </div>
                        </div>
                    </div>
                </template>
                
                <div x-show="logs.length === 0" class="h-full flex flex-col items-center justify-center text-gray-700">
                    <svg class="w-16 h-16 mb-4 opacity-20" fill="currentColor" viewBox="0 0 20 20"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"></path></svg>
                    <p>Ready for instructions...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function agentApp() {
            return {
                goal: '',
                status: 'idle',
                logs: [],
                approvalMessage: '',

                initStream() {
                    const eventSource = new EventSource('/stream');
                    eventSource.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleEvent(data);
                    };
                    eventSource.onerror = () => {
                        console.error("SSE Connection lost");
                    };
                },

                handleEvent(data) {
                    if (data.type === 'status') {
                        this.status = data.status;
                    } else if (data.type === 'log') {
                        this.logs.push(data);
                        this.$nextTick(() => {
                            const container = document.getElementById('log-container');
                            container.scrollTop = container.scrollHeight;
                            document.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                        });
                    } else if (data.type === 'approval') {
                        this.approvalMessage = data.message;
                        this.status = 'waiting_approval';
                    }
                },

                highlightCode(code) {
                    return code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                },

                async startExecution() {
                    if (!this.goal.trim()) return;
                    this.logs = [];
                    this.status = 'running';
                    
                    try {
                        const response = await fetch('/execute', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ goal: this.goal })
                        });
                        
                        // We don't expect a result here immediately because it runs in a thread
                        // The thread will push logs via SSE.
                        // If the thread fails instantly, we might not get a proper JSON back if the server crashes,
                        // but usually we get {"message": "Execution started"}.
                        
                        const result = await response.json();
                        
                        // We rely on the SSE stream to tell us if it succeeded or failed via logs.
                        // However, if the thread throws an unhandled exception before logging, we catch it here.
                        if (!response.ok) {
                             this.logs.push({
                                agent: 'SYSTEM',
                                message: '❌ Server Error: ' + result.detail,
                                level: 'error',
                                timestamp: new Date().toLocaleTimeString(),
                                isCode: false
                            });
                            this.status = 'idle';
                        }

                    } catch (e) {
                        this.logs.push({
                            agent: 'SYSTEM',
                            message: '❌ Network Error: ' + e.message,
                            level: 'error',
                            timestamp: new Date().toLocaleTimeString(),
                            isCode: false
                        });
                        this.status = 'idle';
                    }
                    // Note: We do NOT set status to idle here immediately because the thread is still running.
                    // The thread will send a 'status': 'idle' event via SSE when done.
                },

                async handleApproval(isApproved) {
                    this.status = 'running'; 
                    await fetch('/approve', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ approved: isApproved })
                    });
                }
            }
        }
    </script>
</body>
</html>
"""

@dashboard_app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_TEMPLATE

@dashboard_app.get("/stream")
async def stream_events(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                event = event_queue.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                continue
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@dashboard_app.post("/execute")
async def execute_goal_endpoint(request: GoalRequest):
    def run_agent():
        logger = DashboardLogger()
        orchestrator = NeuroOrchestrator(logger=logger) 
        
        try:
            event_queue.put({"type": "status", "status": "running"})
            
            # Run the agent
            result = orchestrator.run(request.goal)
            
            # ✅ CRITICAL FIX: Explicitly send the final output to the UI
            if result.get("final_output"):
                logger.log(
                    agent="SYSTEM", 
                    message=f" Final Response:\n\n{result['final_output']}", 
                    level="success", 
                    is_code=False
                )
            
            event_queue.put({"type": "status", "status": "idle"})
            return {"success": True, "data": result}
            
        except Exception as e:
            error_trace = traceback.format_exc()
            event_queue.put({"type": "status", "status": "idle"})
            event_queue.put({
                "type": "log", 
                "agent": "SYSTEM", 
                "message": f"❌ Mission Failed:\n{str(e)}\n\nTraceback:\n{error_trace}", 
                "level": "error", 
                "timestamp": time.strftime("%H:%M:%S"),
                "isCode": True
            })
            return {"success": False, "error": str(e)}

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()
    
    return JSONResponse(content={"message": "Execution started"})

@dashboard_app.post("/approve")
async def approve_action(request: ApprovalRequest):
    with approval_lock:
        if approval_decision["status"] == "waiting":
            approval_decision["status"] = "resolved"
            approval_decision["result"] = request.approved
            return JSONResponse(content={"status": "ok"})
    return JSONResponse(content={"status": "error", "message": "No pending approval"}, status_code=400)