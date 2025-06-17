if __name__ == "__main__":
    import uvicorn

    from orion.config import server

    uvicorn.run(
        "orion.server:app",
        host=server.host,
        port=server.port,
        reload=server.reload,
        workers=server.workers,
        loop=server.loop,
        http=server.http,
        log_level=server.log_level,
        proxy_headers=server.proxy_headers,
        forwarded_allow_ips=server.forwarded_allow_ips,
    )
