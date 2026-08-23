from src.api.app import capabilities
from src.integrations import builtin_integration_surfaces


def test_builtin_surfaces_share_one_operation_contract() -> None:
    surfaces = builtin_integration_surfaces()
    assert {surface.surface_id for surface in surfaces} == {
        "trident_web",
        "feishu_companion",
        "m365_copilot_agent",
    }
    operation_sets = [
        tuple(operation.operation_id for operation in surface.operations)
        for surface in surfaces
    ]
    assert len(set(operation_sets)) == 1
    assert "run_research" in operation_sets[0]
    assert "submit_action_feedback" in operation_sets[0]


def test_chat_surfaces_do_not_claim_to_replace_full_workspace() -> None:
    surfaces = {surface.surface_id: surface for surface in builtin_integration_surfaces()}
    assert surfaces["trident_web"].supports_full_workspace is True
    assert surfaces["feishu_companion"].supports_full_workspace is False
    assert surfaces["m365_copilot_agent"].supports_full_workspace is False


def test_capabilities_publish_integration_contract() -> None:
    payload = capabilities()
    assert "external-integration-contract" in payload["delivery_channels"]
    assert len(payload["integration_surfaces"]) == 3
    research = next(
        operation
        for operation in payload["integration_surfaces"][1]["operations"]
        if operation["operation_id"] == "run_research"
    )
    assert research["execution"] == "asynchronous_job"
    assert research["requires_human_confirmation"] is True
