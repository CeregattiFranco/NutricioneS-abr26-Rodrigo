from nutriciones.models.agenda import Agenda
from nutriciones.models.consultas import Consulta
from nutriciones.models.pacientes import (Paciente, PacienteEmail,
                                          PacienteEndereco, PacienteTelefone)
from nutriciones.models.planos import PlanoAlimentar
from nutriciones.models.prontuario import Prontuario
from nutriciones.models.mensagens import Mensagem
from nutriciones.models.biometria import ExameLaboratorial
from nutriciones.models.primary_key import HasPrimaryKey
from nutriciones.services.google import auth_service
from nutriciones.services.google.sheets.indices import get_indices
from nutriciones.services.google.sheets.types import (
    PedidoAtualizacaoRecurso, PedidoInsercaoListaRecursos,
    PedidoInsercaoRecurso, PedidoListagemRecursos, SheetRange)


def listar_recursos[R](request: PedidoListagemRecursos[R]) -> tuple[list[R], SheetRange]:
    """
    Lista recursos de uma planilha Google Sheets.

    Args:
        request: Objeto contendo o ID da planilha, o nome da aba, o range e a função de desserialização.

    Returns:
        Uma lista de recursos do tipo R.

    Raises:
        Qualquer ValueError que o deserializer retornar.
    """
    svc = auth_service.get_ssot_sheets_service()
    out = svc.spreadsheets().values().get(
        spreadsheetId=request.spreadsheet_id,
        range=f'{request.spreadsheet_name}!{request.spreadsheet_range}'
    ).execute()

    match out:
        case {'values': list(rows), 'range': str(range)}:
            range = SheetRange(range)

        case {'range': str(range)}:
            range = SheetRange(range)
            rows = []

        case _:
            raise ValueError(out)

    lista_recursos: list[R] = []
    for row in rows:
        match request.deserialize(row):
            case (recurso, None):
                lista_recursos.append(recurso)

            case (None, error_deserializing_resource):
                raise error_deserializing_resource

    return lista_recursos, range


# @auditable
def inserir_recurso[R: HasPrimaryKey](request: PedidoInsercaoRecurso[R]) -> SheetRange:
    """
    Insere um único recurso em uma planilha Google Sheets.

    Args:
        request: Objeto contendo o ID da planilha, o nome da aba, o recurso a ser inserido e a função de serialização.

    Returns:
        Um objeto SheetsRangeResponse contendo informações sobre o range atualizado.

    Raises:
        ValueError: Se a resposta do Google Sheets não contiver o range atualizado.
    """
    svc = auth_service.get_ssot_sheets_service()
    linha = request.serialize(request.recurso)
    request_body = {'values': [linha]}

    out = svc.spreadsheets().values().append(
        spreadsheetId=request.spreadsheet_id,
        range=f'{request.spreadsheet_name}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=request_body
    ).execute()

    match out:
        case {'updates': {'updatedRange': str(range)}}:
            range = SheetRange(range)
            with get_indices() as indices:
                indices.upsert(request.recurso, range)

            return range

        case _:
            raise ValueError(f"erro ao inserir recurso: {out!r}")


# @auditable
def inserir_lista_recursos[R: HasPrimaryKey](request: PedidoInsercaoListaRecursos[R]) -> SheetRange:
    """
    Insere uma lista de recursos em uma planilha Google Sheets.

    Args:
        request: Objeto contendo o ID da planilha, o nome da aba, a lista de recursos a serem inseridos e a função de serialização.

    Returns:
        Um objeto SheetsRangeResponse contendo informações sobre o range atualizado.

    Raises:
        ValueError: Se a resposta do Google Sheets não contiver o range atualizado.
    """
    svc = auth_service.get_ssot_sheets_service()

    def multiline_range_to_individual_enumerated_ranges(range: SheetRange):
        # ranges will be in the format e.g. A5:E9
        # objective: yield A5:E5, A6:E6, ...
        # together with their respective resource ids for caching
        for row_num, resource in enumerate(request.recursos, start=range.row_start):
            yield resource, SheetRange(range.row(row_num))

    linhas = [
        request.serialize(recurso)
        for recurso in request.recursos
    ]

    request_body = {'values': linhas}

    out = svc.spreadsheets().values().append(
        spreadsheetId=request.spreadsheet_id,
        range=f'{request.spreadsheet_name}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=request_body
    ).execute()

    match out:
        case {'updates': {'updatedRange': str(range)}}:
            range = SheetRange(range)
            with get_indices() as indices:
                for (resource, range_in_sheets) in multiline_range_to_individual_enumerated_ranges(range):
                    indices.upsert(resource, range_in_sheets)

            return range

        case _:
            raise ValueError(f"erro ao inserir lista de recursos: {out!r}")


# @auditable
def atualizar_recurso[R: HasPrimaryKey](request: PedidoAtualizacaoRecurso[R]) -> SheetRange:
    """
    Atualiza um recurso em uma planilha Google Sheets.

    Args:
        request: Objeto contendo o ID da planilha, o nome da aba, o range específico, o recurso atualizado e a função de serialização.

    Returns:
        Um objeto SheetsRangeResponse contendo informações sobre o range atualizado.

    Raises:
        ValueError: Se a resposta do Google Sheets não contiver o range atualizado ou se a operação falhar.

    """
    svc = auth_service.get_ssot_sheets_service()
    linha = request.serialize(request.recurso)
    request_body = {'values': [linha]}

    out = svc.spreadsheets().values().update(
        spreadsheetId=request.spreadsheet_id,
        range=f"{request.spreadsheet_name}!{request.spreadsheet_range}",
        valueInputOption='USER_ENTERED',
        body=request_body
    ).execute()

    match out:
        case {'updatedRange': str(range)}:
            range = SheetRange(range)
            if not range.raw.endswith(request.spreadsheet_range):
                with get_indices() as indices:
                    indices.upsert(request.recurso, range)
            return range

    raise ValueError(f"update com sheets fodeu: {out!r}")


def rollback(spreadsheet_id: str, range: SheetRange) -> SheetRange:
    """
    Realiza um rollback em uma planilha Google Sheets, limpando os dados no range especificado.

    Args:
        spreadsheet_id: str: O ID da planilha.
        range: SheetsRangeResponse: O range que deve ser limpo.

    Returns:
        Um objeto SheetsRangeResponse confirmando o range limpo.

    Raises:
        ValueError: Se a operação de limpeza falhar.
    """
    svc = auth_service.get_ssot_sheets_service()
    out = svc.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range.raw
    ).execute()

    match out:
        case {'clearedRange': str(range_)}:
            return SheetRange(range_)

    raise ValueError(f"erro ao fazer rollback: {out!r}")


sheet_name_of_resource_type: dict[type[HasPrimaryKey], str] = {
    Agenda: 'db_agenda',
    Consulta: 'db_consultas',
    Paciente: 'db_pacientes',
    PacienteTelefone: 'db_pacientes_telefones',
    PacienteEmail: 'db_pacientes_emails',
    PacienteEndereco: 'db_pacientes_enderecos',
    PlanoAlimentar: 'db_planosAlimentares',
    Prontuario: 'db_prontuarios',
    Mensagem: 'db_mensagens',
    ExameLaboratorial: 'db_exames_laboratoriais',
}
