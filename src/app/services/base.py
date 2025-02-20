from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from supabase import Client

from app.core.logger import get_logger

# Type variable for the model
T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    """
    Base service class that provides common functionality for all services.

    Attributes:
        model_class (Type[T]): The Pydantic model class associated with this service
        logger: Logger instance for this service
        supabase_client (Optional[Client]): Supabase client if needed
    """

    def __init__(
        self,
        model_class: Type[T],
        supabase_client: Optional[Client] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the base service.

        Args:
            model_class: The Pydantic model class for this service
            supabase_client: Optional Supabase client
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.model_class = model_class
        self.supabase_client = supabase_client
        self.logger = get_logger(self.__class__.__name__)

        # Initialize any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def validate_model(self, data: dict) -> T:
        """
        Validate input data against the model schema.

        Args:
            data: Dictionary of data to validate

        Returns:
            Validated model instance

        Raises:
            ValidationError: If validation fails
        """
        return self.model_class(**data)

    async def log_operation(self, operation: str, details: Any = None) -> None:
        """
        Log an operation with optional details.

        Args:
            operation: Name of the operation
            details: Optional details to log
        """
        self.logger.info(
            f"Operation: {operation}", extra={"details": details} if details else {}
        )
