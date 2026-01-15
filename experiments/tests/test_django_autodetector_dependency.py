import sys
import types
import uuid


def _stub_asgiref():
    """
    The upstream Django project depends on asgiref. It's not installed in this
    sandbox, but the migration autodetector logic exercised by this test
    doesn't require asgiref's full behavior.
    """

    asgiref = types.ModuleType("asgiref")
    asgiref.__path__ = []  # Mark as package so submodules can be imported.

    sync = types.ModuleType("asgiref.sync")
    local = types.ModuleType("asgiref.local")

    class Local:
        def __init__(self, *args, **kwargs):
            self.__dict__["_storage"] = {}

        def __getattr__(self, name):
            try:
                return self._storage[name]
            except KeyError as e:
                raise AttributeError(name) from e

        def __setattr__(self, name, value):
            self._storage[name] = value

    def async_to_sync(func=None, *args, **kwargs):
        return func

    def sync_to_async(func=None, *args, **kwargs):
        return func

    def iscoroutinefunction(obj):
        return False

    def markcoroutinefunction(func):
        return func

    sync.async_to_sync = async_to_sync
    sync.sync_to_async = sync_to_async
    sync.iscoroutinefunction = iscoroutinefunction
    sync.markcoroutinefunction = markcoroutinefunction
    local.Local = Local

    sys.modules.setdefault("asgiref", asgiref)
    sys.modules.setdefault("asgiref.sync", sync)
    sys.modules.setdefault("asgiref.local", local)


def test_alter_uuid_to_fk_adds_dependency_on_related_app_leaf_node():
    _stub_asgiref()

    # Import Django from the checked-in source tree in this workspace.
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="x",
            INSTALLED_APPS=[],
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
            },
            USE_I18N=False,
            USE_L10N=False,
            USE_TZ=False,
        )

    import django

    django.setup(set_prefix=False)

    from django.db import models
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.graph import MigrationGraph
    from django.db.migrations.state import ModelState, ProjectState

    def make_state(model_states):
        state = ProjectState()
        for model_state in model_states:
            state.add_model(model_state)
        return state

    app2 = ModelState(
        "otherapp",
        "App2",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
        ],
    )
    app1_old = ModelState(
        "testapp",
        "App1",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
            ("another_app", models.UUIDField(null=True, blank=True)),
        ],
    )
    app1_new = ModelState(
        "testapp",
        "App1",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
            (
                "another_app",
                models.ForeignKey(
                    "otherapp.App2",
                    null=True,
                    blank=True,
                    on_delete=models.SET_NULL,
                ),
            ),
        ],
    )

    before = make_state([app1_old, app2])
    after = make_state([app1_new, app2])

    graph = MigrationGraph()
    graph.add_node(("otherapp", "0001_initial"), None)

    autodetector = MigrationAutodetector(before, after)
    changes = autodetector._detect_changes(graph=graph)

    assert set(changes) == {"testapp"}
    assert len(changes["testapp"]) == 1
    migration = changes["testapp"][0]
    assert ("otherapp", "0001_initial") in migration.dependencies
    assert [op.__class__.__name__ for op in migration.operations] == ["AlterField"]


def test_alter_uuid_to_fk_adds_dependency_when_fk_uses_model_class_reference():
    _stub_asgiref()

    # Import Django from the checked-in source tree in this workspace.
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="x",
            INSTALLED_APPS=[],
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
            },
            USE_I18N=False,
            USE_L10N=False,
            USE_TZ=False,
        )

    import django

    django.setup(set_prefix=False)

    from django.db import models
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.graph import MigrationGraph
    from django.db.migrations.state import ModelState, ProjectState

    class _Meta:
        app_label = "otherapp"
        model_name = "app2"

    class App2:
        _meta = _Meta()

    def make_state(model_states):
        state = ProjectState()
        for model_state in model_states:
            state.add_model(model_state)
        return state

    # The target model doesn't need to be a real Django model for this test.
    app2 = ModelState(
        "otherapp",
        "App2",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
        ],
    )
    app1_old = ModelState(
        "testapp",
        "App1",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
            ("another_app", models.UUIDField(null=True, blank=True)),
        ],
    )
    app1_new = ModelState(
        "testapp",
        "App1",
        [
            (
                "id",
                models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
            ),
            ("text", models.CharField(max_length=100)),
            (
                "another_app",
                models.ForeignKey(
                    App2, null=True, blank=True, on_delete=models.SET_NULL
                ),
            ),
        ],
    )

    before = make_state([app1_old, app2])
    after = make_state([app1_new, app2])

    graph = MigrationGraph()
    graph.add_node(("otherapp", "0001_initial"), None)

    autodetector = MigrationAutodetector(before, after)
    changes = autodetector._detect_changes(graph=graph)

    migration = changes["testapp"][0]
    assert ("otherapp", "0001_initial") in migration.dependencies
