from horizon.l2_use_cases.compute_sky_use_case import ComputeSkyUseCase
from horizon.l3_interface_adapters.gateways.ip_location_gateway import IPLocationGateway
from horizon.l3_interface_adapters.gateways.prefs_gateway import JsonPreferencesGateway
from horizon.l3_interface_adapters.presenters.sky_presenter import InMemorySkyPresenter


def test_pipeline_runs(tmp_path):
    prefs_path = tmp_path / 'prefs.json'
    gateway = JsonPreferencesGateway(prefs_path)
    presenter = InMemorySkyPresenter()
    interactor = ComputeSkyUseCase(presenter, IPLocationGateway(), gateway)
    interactor.execute()
    vm = presenter.latest
    assert vm is not None
    assert vm.horizon_hex.startswith('#')
    assert vm.zenith_hex.startswith('#')
