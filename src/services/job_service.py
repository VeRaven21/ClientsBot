import crud.jobs as job_crud

async def get_all_services():
    return await job_crud.get_all_services()
