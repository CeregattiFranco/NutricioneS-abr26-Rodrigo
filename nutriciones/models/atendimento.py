from dataclasses import dataclass


@dataclass(frozen=True)
class Os4Inputs:
    objetivo: str
    diagnostico: str
    conduta: str
    orientacao: str


# 18 perguntas - 3 conjuntos de 6
# anamnese - modelagem pré consulta
# paciente responde formulário
# -> a partir das respostas um score é calculado
# custo energético de vida
# fisiológico
# emocional
