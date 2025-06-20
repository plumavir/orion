import json
import logging
from unittest import mock

import pytest

import orion.messaging.producer as producer
from orion.messaging.producer import (
    DEFAULT_HEADERS,
    LOG_FAIL,
    LOG_SENT,
    StompConnection,
    _build_headers,
    _ConnListener,
    _publish,
    create_dispatcher,
    dispatch,
)


@pytest.fixture(autouse=True)
def dummy_messenger(monkeypatch):
    class Dummy:
        host = "localhost"
        port = 61613
        heartbeat = (1000, 1000)
        connection_timeout = 10000
        client_id = "test-client"
        username = "user"
        password = "pass"
        default_destination = "default_queue"

    monkeypatch.setattr(producer, "messenger", Dummy)
    return Dummy


@pytest.fixture
def stomp_conn(monkeypatch):
    mock_conn = mock.Mock()
    monkeypatch.setattr(producer.stomp, "Connection", lambda *_, **__: mock_conn)
    return mock_conn


class TestHeaders:
    @pytest.mark.parametrize(
        "extra,expected",
        [
            (None, DEFAULT_HEADERS),
            ({"x": "y"}, {**DEFAULT_HEADERS, "x": "y"}),
        ],
    )
    def test_headers_are_correctly_built(self, extra, expected):
        headers = _build_headers(extra)
        assert headers == expected
        if extra is None:
            assert headers is not DEFAULT_HEADERS

        if extra:
            assert "x" not in DEFAULT_HEADERS


class TestConnectionListener:
    @pytest.mark.parametrize(
        "frame, level, msg",
        [
            (type("Frame", (), {"body": "err"})(), logging.ERROR, "STOMP Error: err"),
            ("plain error", logging.ERROR, "STOMP Error: plain error"),
        ],
    )
    def test_logs_error_on_stomp_error(self, caplog, frame, level, msg):
        caplog.set_level(level)
        _ConnListener().on_error(frame)
        assert msg in caplog.text

    def test_logs_warning_on_disconnection(self, caplog):
        caplog.set_level(logging.WARNING)
        _ConnListener().on_disconnected()
        assert "Desconectado do broker STOMP" in caplog.text


class TestStompConnection:
    def test_connects_with_credentials(self, stomp_conn, dummy_messenger):
        with StompConnection() as conn:
            assert conn is stomp_conn

        stomp_conn.set_listener.assert_called_once()
        stomp_conn.connect.assert_called_once_with(
            dummy_messenger.username, dummy_messenger.password, wait=True, headers={"client-id": dummy_messenger.client_id}
        )
        stomp_conn.disconnect.assert_called_once()

    def test_connects_anonymously_if_no_credentials(self, stomp_conn, dummy_messenger):
        dummy_messenger.username = None
        dummy_messenger.password = None

        with StompConnection():
            pass

        stomp_conn.connect.assert_called_once_with(wait=True, headers={"client-id": dummy_messenger.client_id})

    def test_logs_disconnect_failure(self, stomp_conn, caplog):
        stomp_conn.disconnect.side_effect = producer.ConnectFailedException("fail")
        caplog.set_level(logging.WARNING)

        with StompConnection():
            pass

        assert "Falha ao desconectar do broker: fail" in caplog.text


class TestDispatch:
    @pytest.mark.parametrize(
        "destination,headers",
        [
            (None, None),
            ("custom", None),
            (None, {"p": "h"}),
        ],
    )
    def test_dispatches_successfully(self, monkeypatch, caplog, destination, headers, dummy_messenger):
        called = {}

        def fake_publish(dest, body, hdrs):
            actual_dest = dest or dummy_messenger.default_destination
            called.update(dest=actual_dest, body=body, headers=hdrs)

        monkeypatch.setattr(producer, "_publish", fake_publish)
        caplog.set_level(logging.DEBUG)

        payload = {"k": "v"}
        result = dispatch(payload, destination=destination, headers=headers)

        assert result is True
        dest = destination or dummy_messenger.default_destination
        assert called["dest"] == dest
        assert json.loads(called["body"]) == payload
        assert all(k in called["headers"] for k in (headers or {}))
        assert LOG_SENT.split()[0] in caplog.text

    def test_returns_false_on_failure(self, monkeypatch, caplog):
        monkeypatch.setattr(producer, "_publish", lambda *_: (_ for _ in ()).throw(Exception("err")))
        caplog.set_level(logging.ERROR)

        result = dispatch({"a": 1})
        assert result is False
        assert LOG_FAIL.split()[0] in caplog.text

    def test_truncates_long_messages_in_logs(self, monkeypatch, caplog):
        monkeypatch.setattr(producer, "_publish", lambda *_: None)
        caplog.set_level(logging.DEBUG)

        long_payload = {"x": "y" * 200}
        dispatch(long_payload)

        assert "..." in caplog.text


class TestDispatcherCreation:
    def test_creates_partial_dispatcher(self, monkeypatch):
        mock_dispatch = mock.Mock(return_value="result")
        monkeypatch.setattr(producer, "dispatch", mock_dispatch)

        dispatcher = create_dispatcher("custom_queue", {"header": "value"})
        result = dispatcher({"data": "content"})

        mock_dispatch.assert_called_once_with(
            {"data": "content"},
            destination="custom_queue",
            headers={"header": "value"},
        )
        assert result == "result"


class TestPublishing:
    def test_publishes_to_stomp_broker(self, monkeypatch):
        mock_conn = mock.Mock()
        mock_context = mock.Mock(__enter__=lambda self: mock_conn, __exit__=mock.Mock())
        monkeypatch.setattr(producer, "StompConnection", lambda: mock_context)

        message = json.dumps({"data": "test"})
        headers = {"content-type": "application/json"}

        _publish("test_queue", message, headers)

        mock_conn.send.assert_called_once_with(
            destination="test_queue",
            body=message,
            headers=headers,
        )
