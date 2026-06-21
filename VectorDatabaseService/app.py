import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import aio_pika
from config import RABBITMQ_URL

from config import APP_HOST, APP_PORT
from controller.books_controller import router as books_router
from controller.chat_controller import router as chat_router
from controller.reviews_controller import router as reviews_router
from saga.consumer import start_orderstatus_created_consumer
from saga.topology import declare_choreography_topology

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

import py_eureka_client.eureka_client as eureka_client
from config import EUREKA_SERVER, APP_NAME

app = FastAPI(
    title="Vector Database Service - Library",
    description="Books and reviews vector search API with semantic, hybrid, and chat endpoints.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup():
    await eureka_client.init_async(
        eureka_server=EUREKA_SERVER,
        app_name=APP_NAME,          # "vector-database-service" iz config.py
        instance_port=APP_PORT,     # 8000
    )

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(books_router)
app.include_router(reviews_router)
app.include_router(chat_router)

@app.on_event("startup")
async def startup_rabbitmq():
    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.rabbitmq_channel = await app.state.rabbitmq_connection.channel()

    # Koreografisana SAGA: deklarise exchange/queue/binding topologiju (idempotentno,
    # vidi saga/topology.py) i pokrece consumer koji slusa ChangeOfOrderStatusCreatedEvent.
    await declare_choreography_topology(app.state.rabbitmq_channel)
    await start_orderstatus_created_consumer(app.state.rabbitmq_channel)

@app.on_event("shutdown")
async def shutdown_rabbitmq():
    await app.state.rabbitmq_connection.close()

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "collection": "books + reviews"}


if __name__ == "__main__":
    uvicorn.run("app:app", host=APP_HOST, port=APP_PORT, reload=False)