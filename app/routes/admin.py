"""Minimal administrative readiness function, protected by server-side allowlist."""
import os
from fastapi import APIRouter,Depends,HTTPException
from app.security import current_user

router=APIRouter(prefix='/admin',tags=['admin'])


def current_admin(username:str=Depends(current_user)):
    administrators={x.strip() for x in os.getenv('TOURSHIELD_ADMIN_USERS','').split(',') if x.strip()}
    if username not in administrators:
        raise HTTPException(403,'Acesso administrativo não autorizado')
    return username


@router.get('/status',summary='Consultar prontidão administrativa',
            description='JWT e usuário explicitamente autorizado na configuração do servidor. '
                        'Roles no texto, body ou claims extras não concedem privilégio.',
            responses={401:{'description':'Sessão inválida'},403:{'description':'Usuário não administrador'}})
def admin_status(username:str=Depends(current_admin)):
    return {'status':'ok','scope':'administrative-readiness-only'}
