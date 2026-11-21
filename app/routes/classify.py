from fastapi import APIRouter, Depends, HTTPException
from app.security import current_user
from app.models import ClassifyRequest, ClassifyResponse
from app.classifier import classify_text

router=APIRouter(tags=['classify'])


@router.post('/classify',response_model=ClassifyResponse,summary='Classificar intenção do atendimento',
             description='JWT obrigatório. Texto em inglês (1–4.000 caracteres), 20 intenções CLINC150. '
                         'Probabilidade não calibrada; não aprova reservas, fraude, localização ou benefícios.',
             responses={401:{'description':'Bearer ausente ou inválido'},
                        422:{'description':'Texto inválido ou campo extra'},
                        503:{'description':'Modelo ausente, incompatível ou com integridade inválida'}})
def classify(payload:ClassifyRequest,username:str=Depends(current_user)):
    try:
        return classify_text(payload.text)
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(503,'Classificador indisponível') from None
