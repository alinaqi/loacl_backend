import pytest
from pydantic import BaseModel

from app.services.base import BaseService

pytestmark = pytest.mark.asyncio


# Test model
class TestModel(BaseModel):
    name: str
    value: int


class TestBaseService:
    @pytest.fixture
    def service(self, mocker):
        """Create a test service instance with mocked Supabase client"""
        mock_supabase = mocker.Mock()
        return BaseService(model_class=TestModel, supabase_client=mock_supabase)

    async def test_validate_model_success(self, service):
        """Test successful model validation"""
        data = {"name": "test", "value": 42}
        model = await service.validate_model(data)
        assert isinstance(model, TestModel)
        assert model.name == "test"
        assert model.value == 42

    async def test_validate_model_failure(self, service):
        """Test model validation failure"""
        data = {"name": "test"}  # Missing required field
        with pytest.raises(Exception):
            await service.validate_model(data)

    async def test_log_operation(self, service, caplog):
        """Test operation logging"""
        operation = "test_operation"
        details = {"key": "value"}
        await service.log_operation(operation, details)

        # Verify log message
        assert "Operation: test_operation" in caplog.text

    def test_supabase_client_initialization(self, mocker):
        """Test Supabase client initialization"""
        mock_supabase = mocker.Mock()
        service = BaseService(model_class=TestModel, supabase_client=mock_supabase)
        assert service.supabase_client == mock_supabase
