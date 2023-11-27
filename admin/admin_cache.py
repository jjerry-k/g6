import asyncio
from fastapi import APIRouter, Depends, Query, Request, Form, HTTPException, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sse_starlette import EventSourceResponse
from common.database import get_db, engine
import common.models as models 
from lib.common import *

from lib.plugin.service import get_admin_plugin_menus, get_all_plugin_module_names

router = APIRouter()
templates = Jinja2Templates(directory=[ADMIN_TEMPLATES_DIR, EDITOR_PATH])
templates.env.globals['get_admin_menus'] = get_admin_menus
templates.env.globals["get_all_plugin_module_names"] = get_all_plugin_module_names

CACHE_MENU_KEY = "100900"

@router.get("/cache_file_delete")
async def cache_file_delete(request: Request, db: Session = Depends(get_db)):
    '''
    캐시파일 일괄삭제
    '''
    request.session["menu_key"] = CACHE_MENU_KEY

    error = auth_check_menu(request, request.session.get("menu_key"), "w")
    if error:
        raise AlertException(error)    

    context = {
        "request": request,
    }
    return templates.TemplateResponse("cache_file_delete.html", context)


@router.get("/cache_file_deleting")
async def cache_file_deleting(request: Request, db: Session = Depends(get_db)):
    '''
    캐시파일 일괄삭제 처리
    
    '''
    error = auth_check_menu(request, request.session.get("menu_key"), "w")
    if error:
        raise AlertException(error)    
    
    async def send_events():
        count = 0
        cache_directory = "data/cache"
        try:
            # 캐시 디렉토리가 존재하는지 확인
            if os.path.exists(cache_directory):
                # 디렉토리 내의 모든 파일 및 폴더 삭제
                for filename in os.listdir(cache_directory):
                    file_path = os.path.join(cache_directory, filename)
                    # 파일이나 디렉토리를 삭제
                    file_dir = ""
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        file_dir = "파일"
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        file_dir = "디렉토리"
                
                    count += 1
                    # 10명마다 1초씩 쉬어줍니다.
                    if count % 10 == 0:
                        await asyncio.sleep(0.1)  # 비동기 sleep 사용
        
                    # return {"status": "Cache cleared successfully"}
                    yield f"data: ({count}) {filename} {file_dir} 삭제 \n\n"
            else:
                yield f"data: {cache_directory} 디렉토리가 존재하지 않습니다. \n\n"
                # return {"status": "Cache directory does not exist"}
        except Exception as e:
            yield f"data: 오류가 발생했습니다. {str(e)} \n\n"
            # return {"status": "Error occurred", "details": str(e)}        
        
        # 종료 메시지 전송
        yield f"data: 총 {count}개의 파일과 디렉토리를 삭제했습니다.\n\n"
        yield "data: [끝]\n\n"
        
    return EventSourceResponse(send_events())
