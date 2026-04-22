import crud.workers as worker_crud

async def get_all_workers():
    return await worker_crud.get_all_workers()