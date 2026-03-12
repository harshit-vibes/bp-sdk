"""Tests for BlueprintAPI client."""

from unittest.mock import MagicMock, patch
import pytest
import httpx

from sdk.api.blueprint import BlueprintAPI
from sdk.exceptions import APIError, NetworkError, TimeoutError


class TestBlueprintAPIInit:
    """Tests for BlueprintAPI initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        api = BlueprintAPI(
            bearer_token="test_token",
            organization_id="test_org",
        )
        assert api.bearer_token == "test_token"
        assert api.organization_id == "test_org"
        assert api.base_url == "https://pagos-prod.studio.lyzr.ai"
        assert api.timeout == 30.0

    def test_init_with_custom_url(self):
        """Test initialization with custom base URL."""
        api = BlueprintAPI(
            bearer_token="test_token",
            organization_id="test_org",
            base_url="https://custom.api.com/",
        )
        assert api.base_url == "https://custom.api.com"  # Trailing slash stripped

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        api = BlueprintAPI(
            bearer_token="test_token",
            organization_id="test_org",
            timeout=60.0,
        )
        assert api.timeout == 60.0


class TestBlueprintAPICreate:
    """Tests for BlueprintAPI.create()."""

    @patch.object(BlueprintAPI, "_request")
    def test_create_success(self, mock_request):
        """Test successful blueprint creation."""
        mock_request.return_value = {
            "_id": "bp_123",
            "name": "Test Blueprint",
        }

        api = BlueprintAPI("token", "org_123")
        result = api.create({"name": "Test Blueprint"})

        assert result["_id"] == "bp_123"
        mock_request.assert_called_once_with(
            method="POST",
            path="/api/v1/blueprints/blueprints",
            operation="create_blueprint",
            params={"organization_id": "org_123"},
            json_data={"name": "Test Blueprint"},
        )


class TestBlueprintAPIGet:
    """Tests for BlueprintAPI.get()."""

    @patch.object(BlueprintAPI, "_request")
    def test_get_success(self, mock_request):
        """Test successful blueprint retrieval."""
        mock_request.return_value = {
            "_id": "bp_123",
            "name": "Test Blueprint",
            "blueprint_data": {"nodes": []},
        }

        api = BlueprintAPI("token", "org_123")
        result = api.get("bp_123")

        assert result["_id"] == "bp_123"
        mock_request.assert_called_once_with(
            method="GET",
            path="/api/v1/blueprints/blueprints/bp_123",
            operation="get_blueprint:bp_123",
            params={"organization_id": "org_123"},
        )


class TestBlueprintAPIUpdate:
    """Tests for BlueprintAPI.update()."""

    @patch.object(BlueprintAPI, "_request")
    def test_update_success(self, mock_request):
        """Test successful blueprint update."""
        mock_request.return_value = {
            "_id": "bp_123",
            "name": "Updated Blueprint",
        }

        api = BlueprintAPI("token", "org_123")
        result = api.update("bp_123", {"name": "Updated Blueprint"})

        assert result["name"] == "Updated Blueprint"
        mock_request.assert_called_once_with(
            method="PUT",
            path="/api/v1/blueprints/blueprints/bp_123",
            operation="update_blueprint:bp_123",
            params={"organization_id": "org_123"},
            json_data={"name": "Updated Blueprint"},
        )


class TestBlueprintAPIDelete:
    """Tests for BlueprintAPI.delete()."""

    def test_delete_success_200(self):
        """Test successful deletion with 200 status."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "delete") as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            result = api.delete("bp_123")

            assert result is True
            mock_delete.assert_called_once()

    def test_delete_success_204(self):
        """Test successful deletion with 204 status."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "delete") as mock_delete:
            mock_response = MagicMock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response

            result = api.delete("bp_123")

            assert result is True

    def test_delete_timeout(self):
        """Test delete timeout raises TimeoutError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "delete") as mock_delete:
            mock_delete.side_effect = httpx.TimeoutException("timeout")

            with pytest.raises(TimeoutError) as exc_info:
                api.delete("bp_123")

            assert "delete_blueprint:bp_123" in str(exc_info.value)

    def test_delete_network_error(self):
        """Test delete network error raises NetworkError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "delete") as mock_delete:
            mock_delete.side_effect = httpx.RequestError("connection failed")

            with pytest.raises(NetworkError) as exc_info:
                api.delete("bp_123")

            assert "delete_blueprint:bp_123" in str(exc_info.value)


class TestBlueprintAPIList:
    """Tests for BlueprintAPI.list()."""

    @patch.object(BlueprintAPI, "_request")
    def test_list_defaults(self, mock_request):
        """Test list with default parameters."""
        mock_request.return_value = {
            "blueprints": [{"_id": "bp_1"}, {"_id": "bp_2"}],
            "total": 2,
            "page": 1,
        }

        api = BlueprintAPI("token", "org_123")
        result = api.list()

        assert len(result["blueprints"]) == 2
        # Verify default params
        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["page_size"] == 50
        assert call_args.kwargs["params"]["page"] == 1

    @patch.object(BlueprintAPI, "_request")
    def test_list_with_filters(self, mock_request):
        """Test list with various filters."""
        mock_request.return_value = {"blueprints": [], "total": 0}

        api = BlueprintAPI("token", "org_123")
        api.list(
            page_size=10,
            page=2,
            share_type="public",
            category="legal",
            search="contract",
            tags=["tag1", "tag2"],
        )

        call_args = mock_request.call_args
        params = call_args.kwargs["params"]
        assert params["page_size"] == 10
        assert params["page"] == 2
        assert params["share_type"] == "public"
        assert params["category"] == "legal"
        assert params["search"] == "contract"
        assert params["tags"] == "tag1,tag2"

    @patch.object(BlueprintAPI, "_request")
    def test_list_page_size_capped(self, mock_request):
        """Test that page_size is capped at 100."""
        mock_request.return_value = {"blueprints": []}

        api = BlueprintAPI("token", "org_123")
        api.list(page_size=200)

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["page_size"] == 100

    @patch.object(BlueprintAPI, "_request")
    def test_list_page_minimum(self, mock_request):
        """Test that page is at least 1."""
        mock_request.return_value = {"blueprints": []}

        api = BlueprintAPI("token", "org_123")
        api.list(page=0)

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["page"] == 1

    @patch.object(BlueprintAPI, "_request")
    def test_list_filter_by_org(self, mock_request):
        """Test list with organization filter."""
        mock_request.return_value = {"blueprints": []}

        api = BlueprintAPI("token", "org_123")
        api.list(filter_by_org=True)

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["user_organization_id"] == "org_123"

    @patch.object(BlueprintAPI, "_request")
    def test_list_no_org_filter_by_default(self, mock_request):
        """Test list does not include org filter by default."""
        mock_request.return_value = {"blueprints": []}

        api = BlueprintAPI("token", "org_123")
        api.list()

        call_args = mock_request.call_args
        assert "user_organization_id" not in call_args.kwargs["params"]


class TestBlueprintAPISetShareType:
    """Tests for BlueprintAPI.set_share_type()."""

    @patch.object(BlueprintAPI, "_request")
    def test_set_share_type(self, mock_request):
        """Test setting share type."""
        mock_request.return_value = {"_id": "bp_123", "share_type": "public"}

        api = BlueprintAPI("token", "org_123")
        result = api.set_share_type("bp_123", "public")

        assert result["share_type"] == "public"
        mock_request.assert_called_once_with(
            method="POST",
            path="/api/v1/blueprints/blueprints/bp_123/share",
            operation="set_share_type:bp_123",
            params={"organization_id": "org_123"},
            json_data={"share_type": "public"},
        )


class TestBlueprintAPIClone:
    """Tests for BlueprintAPI.clone()."""

    @patch.object(BlueprintAPI, "_request")
    def test_clone_minimal(self, mock_request):
        """Test clone with minimal parameters."""
        mock_request.return_value = {"_id": "bp_clone_123"}

        api = BlueprintAPI("token", "org_123")
        result = api.clone("bp_123", api_key="agent_key")

        assert result["_id"] == "bp_clone_123"
        call_args = mock_request.call_args
        assert call_args.kwargs["json_data"]["blueprint_id"] == "bp_123"
        assert call_args.kwargs["json_data"]["api_key"] == "agent_key"

    @patch.object(BlueprintAPI, "_request")
    def test_clone_with_new_name(self, mock_request):
        """Test clone with custom name."""
        mock_request.return_value = {"_id": "bp_clone_123", "name": "My Clone"}

        api = BlueprintAPI("token", "org_123")
        api.clone("bp_123", api_key="agent_key", new_name="My Clone")

        call_args = mock_request.call_args
        assert call_args.kwargs["json_data"]["blueprint_name"] == "My Clone"


class TestBlueprintAPIDuplicate:
    """Tests for BlueprintAPI.duplicate()."""

    @patch.object(BlueprintAPI, "_request")
    def test_duplicate_minimal(self, mock_request):
        """Test duplicate with minimal parameters."""
        mock_request.return_value = {"_id": "bp_dup_123"}

        api = BlueprintAPI("token", "org_123")
        result = api.duplicate("bp_123", new_name="Duplicated BP")

        assert result["_id"] == "bp_dup_123"
        call_args = mock_request.call_args
        assert call_args.kwargs["json_data"]["new_name"] == "Duplicated BP"

    @patch.object(BlueprintAPI, "_request")
    def test_duplicate_with_description(self, mock_request):
        """Test duplicate with new description."""
        mock_request.return_value = {"_id": "bp_dup_123"}

        api = BlueprintAPI("token", "org_123")
        api.duplicate("bp_123", new_name="Dup", new_description="New desc")

        call_args = mock_request.call_args
        assert call_args.kwargs["json_data"]["new_description"] == "New desc"


class TestBlueprintAPITrackUsage:
    """Tests for BlueprintAPI.track_usage()."""

    @patch.object(BlueprintAPI, "_request")
    def test_track_usage_default(self, mock_request):
        """Test track usage with default event type."""
        mock_request.return_value = {"message": "Usage tracked"}

        api = BlueprintAPI("token", "org_123")
        api.track_usage("bp_123")

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["event_type"] == "executed"

    @patch.object(BlueprintAPI, "_request")
    def test_track_usage_custom_event(self, mock_request):
        """Test track usage with custom event type."""
        mock_request.return_value = {"message": "Usage tracked"}

        api = BlueprintAPI("token", "org_123")
        api.track_usage("bp_123", event_type="cloned")

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["event_type"] == "cloned"


class TestBlueprintAPIErrorHandling:
    """Tests for error handling in _request method."""

    def test_timeout_error(self):
        """Test that timeout raises TimeoutError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("timeout")

            with pytest.raises(TimeoutError) as exc_info:
                api._request("GET", "/test", "test_op")

            assert exc_info.value.operation == "test_op"
            assert "timed out" in exc_info.value.reason

    def test_connect_error(self):
        """Test that connection error raises NetworkError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "request") as mock_request:
            mock_request.side_effect = httpx.ConnectError("connection refused")

            with pytest.raises(NetworkError) as exc_info:
                api._request("GET", "/test", "test_op")

            assert exc_info.value.operation == "test_op"
            assert "Failed to connect" in exc_info.value.reason

    def test_request_error(self):
        """Test that generic request error raises NetworkError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "request") as mock_request:
            mock_request.side_effect = httpx.RequestError("unknown error")

            with pytest.raises(NetworkError) as exc_info:
                api._request("GET", "/test", "test_op")

            assert exc_info.value.operation == "test_op"

    def test_api_error_on_non_2xx(self):
        """Test that non-2xx status raises APIError."""
        api = BlueprintAPI("token", "org_123")

        with patch.object(api._client, "request") as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Blueprint not found"
            mock_request.return_value = mock_response

            with pytest.raises(APIError) as exc_info:
                api._request("GET", "/test", "test_op")

            assert exc_info.value.status_code == 404
            assert exc_info.value.endpoint == "test_op"


class TestBlueprintAPIHandleResponse:
    """Tests for _handle_response method."""

    def test_handle_200_json(self):
        """Test handling 200 response with JSON."""
        api = BlueprintAPI("token", "org_123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        result = api._handle_response(mock_response, "test_op")
        assert result == {"data": "test"}

    def test_handle_201_json(self):
        """Test handling 201 response with JSON."""
        api = BlueprintAPI("token", "org_123")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"_id": "new_123"}

        result = api._handle_response(mock_response, "test_op")
        assert result == {"_id": "new_123"}

    def test_handle_200_no_json(self):
        """Test handling 200 response without JSON body."""
        api = BlueprintAPI("token", "org_123")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON")

        result = api._handle_response(mock_response, "test_op")
        assert result == {"status": "success"}

    def test_handle_error_status(self):
        """Test handling error status code."""
        api = BlueprintAPI("token", "org_123")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with pytest.raises(APIError) as exc_info:
            api._handle_response(mock_response, "test_op")

        assert exc_info.value.status_code == 500
