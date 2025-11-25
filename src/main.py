import json
import time
import uvicorn
from fastapi import FastAPI
import log_config
import posts_config
import workers
import tasks

HOST = "0.0.0.0"#本地运行
PORT = 8001

app=FastAPI()

@app.post("/api/v1/ai/startDetects")
async def startDetects(request: posts_config.request_start):
    log_config.logging.info(f"start request received:\n {request}")
    print(f"start request received: \n{request}")
    detect_id=time.time_ns()
    workers.processing_tasks[detect_id]= tasks.Task(request, detect_id)
    response = posts_config.response_start(
        messageCode="success",
        record = []
        )
    for stream in request.listStreamings:
        response.record.append(posts_config.Record(streaming=stream, detectId=detect_id))
    log_config.logging.info(f"start response send: \n{response}")
    print(f"start response send: \n{response}")
    return response

@app.post("/api/v1/ai/stopDetects")
async def stopDetects(request: posts_config.request_stop):
    log_config.logging.info(f"stop request received: \n{request}")
    if request.detectId in workers.processing_tasks:
        workers.processing_tasks[request.detectId].is_processing = False
        del workers.processing_tasks[request.detectId]
        response = posts_config.response_stop(
            messageCode="success",
            messageInfo=f"已停止监测:{request.detectId}"
        )
        log_config.logging.info(f"stop response send:\n {response}")
        print(f"stop response send: \n{response}")
        return json.dumps(response)
    else:
        response = posts_config.response_stop(
            messageCode="error",
            messageInfo=f"不存在监测:{request.detectId}"
        )
        log_config.logging.info(f"stop response send: \n{response}")
        print(f"stop response send: \n{response}")
        return response


@app.post("/api/v1/ai/stateDetects")
async def stateDetects(request: posts_config.request_state):
    log_config.logging.info(f"state request received: \n{request}")
    print(f"state request received: \n{request}")
    response = posts_config.response_state(
        messageCode=[]
    )
    for detect in request.detectId:
        response.messageCode.append(
            posts_config.MessageCode(detectId = detect, state = (detect in workers.processing_tasks)))
    log_config.logging.info(f"state response send: \n{response}")
    print(f"state response send: \n{response}")
    return response


if __name__ == "__main__":
    processor = workers.task_processor()
    uvicorn.run(app=app)#,host=HOST,port=PORT)

