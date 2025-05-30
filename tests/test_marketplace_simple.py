import pytest
import uuid
from datetime import datetime

# Test marketplace schemas
from shared.schemas.marketplace import (
    AgentCreate, AgentUpdate, Agent, AgentSummary,
    AgentInstallationCreate, AgentInstallation,
    AgentReviewCreate, AgentReview,
    AgentSearchRequest, AgentSearchFilters, SortOption, PricingModel,
    EventType
)


class TestMarketplaceSchemas:
    """Test marketplace Pydantic schemas"""
    
    def test_agent_create_schema(self):
        """Test creating an agent with valid data"""
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent for testing",
            "category": "productivity",
            "tags": ["test", "automation"],
            "version": "1.0.0",
            "capabilities": ["testing", "automation"],
            "pricing_model": "free"
        }
        
        agent = AgentCreate(**agent_data)
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent for testing"
        assert agent.category == "productivity"
        assert agent.tags == ["test", "automation"]
        assert agent.pricing_model == PricingModel.FREE
        assert agent.price == 0.0
    
    def test_agent_create_paid_validation(self):
        """Test validation for paid agents"""
        with pytest.raises(ValueError, match="Paid agents must have a price > 0"):
            AgentCreate(
                name="Paid Agent",
                pricing_model="paid",
                price=0.0
            )
    
    def test_agent_create_free_validation(self):
        """Test validation for free agents with price"""
        with pytest.raises(ValueError, match="Free agents cannot have a price"):
            AgentCreate(
                name="Free Agent",
                pricing_model="free",
                price=10.0
            )
    
    def test_agent_installation_create(self):
        """Test creating agent installation data"""
        installation_data = {
            "settings": {
                "enabled": True,
                "notifications": False,
                "api_key": "test-key"
            }
        }
        
        installation = AgentInstallationCreate(**installation_data)
        assert installation.settings["enabled"] == True
        assert installation.settings["notifications"] == False
        assert installation.settings["api_key"] == "test-key"
    
    def test_agent_review_create(self):
        """Test creating agent review data"""
        review_data = {
            "rating": 5,
            "title": "Excellent agent!",
            "review_text": "This agent works perfectly for my needs."
        }
        
        review = AgentReviewCreate(**review_data)
        assert review.rating == 5
        assert review.title == "Excellent agent!"
        assert review.review_text == "This agent works perfectly for my needs."
    
    def test_agent_review_rating_validation(self):
        """Test rating validation (must be 1-5)"""
        with pytest.raises(ValueError):
            AgentReviewCreate(rating=0)
        
        with pytest.raises(ValueError):
            AgentReviewCreate(rating=6)
    
    def test_agent_search_request(self):
        """Test agent search request schema"""
        search_data = {
            "query": "productivity agent",
            "filters": {
                "category": "productivity",
                "tags": ["automation", "productivity"],
                "pricing_model": "free",
                "min_rating": 4.0,
                "is_verified": True
            },
            "sort": "rating",
            "page": 1,
            "limit": 20
        }
        
        search = AgentSearchRequest(**search_data)
        assert search.query == "productivity agent"
        assert search.filters.category == "productivity"
        assert search.filters.tags == ["automation", "productivity"]
        assert search.filters.pricing_model == PricingModel.FREE
        assert search.filters.min_rating == 4.0
        assert search.filters.is_verified == True
        assert search.sort == SortOption.RATING
        assert search.page == 1
        assert search.limit == 20
    
    def test_agent_search_defaults(self):
        """Test default values in agent search"""
        search = AgentSearchRequest()
        assert search.query is None
        assert search.filters is None
        assert search.sort == SortOption.POPULAR
        assert search.page == 1
        assert search.limit == 20
    
    def test_pagination_validation(self):
        """Test pagination validation"""
        # Page must be >= 1
        with pytest.raises(ValueError):
            AgentSearchRequest(page=0)
        
        # Limit must be between 1-100
        with pytest.raises(ValueError):
            AgentSearchRequest(limit=0)
        
        with pytest.raises(ValueError):
            AgentSearchRequest(limit=101)


class TestEnums:
    """Test enum values"""
    
    def test_pricing_model_enum(self):
        """Test pricing model enum values"""
        assert PricingModel.FREE == "free"
        assert PricingModel.PAID == "paid"
        assert PricingModel.FREEMIUM == "freemium"
    
    def test_sort_option_enum(self):
        """Test sort option enum values"""
        assert SortOption.POPULAR == "popular"
        assert SortOption.RECENT == "recent"
        assert SortOption.RATING == "rating"
        assert SortOption.NAME == "name"
        assert SortOption.INSTALLS == "installs"
    
    def test_event_type_enum(self):
        """Test event type enum values"""
        assert EventType.VIEW == "view"
        assert EventType.INSTALL == "install"
        assert EventType.UNINSTALL == "uninstall"
        assert EventType.RUN == "run"
        assert EventType.RATE == "rate"
        assert EventType.REVIEW == "review"


class TestMarketplaceLogic:
    """Test marketplace business logic"""
    
    def test_trending_score_calculation(self):
        """Test trending score calculation logic"""
        # Mock agent data
        class MockAgent:
            def __init__(self, install_count, view_count, rating_average):
                self.install_count = install_count
                self.view_count = view_count
                self.rating_average = rating_average
                self.installations = []
        
        # Simple trending score: installs (50%) + views (30%) + rating (20%)
        def calculate_trending_score(agent):
            installs_score = min(agent.install_count, 1000) / 1000 * 0.5
            views_score = min(agent.view_count, 10000) / 10000 * 0.3
            rating_score = agent.rating_average / 5.0 * 0.2
            return installs_score + views_score + rating_score
        
        # Test different scenarios
        popular_agent = MockAgent(install_count=500, view_count=5000, rating_average=4.5)
        new_agent = MockAgent(install_count=10, view_count=100, rating_average=5.0)
        average_agent = MockAgent(install_count=100, view_count=1000, rating_average=3.5)
        
        popular_score = calculate_trending_score(popular_agent)
        new_score = calculate_trending_score(new_agent)
        average_score = calculate_trending_score(average_agent)
        
        # Popular agent should have highest score
        assert popular_score > new_score
        assert popular_score > average_score
        
        # Verify score components
        assert 0 <= popular_score <= 1
        assert 0 <= new_score <= 1
        assert 0 <= average_score <= 1


class TestMarketplaceConstants:
    """Test marketplace constants and configurations"""
    
    def test_default_configuration_schema(self):
        """Test default agent configuration schema"""
        default_schema = {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "API key for external services"},
                "max_requests": {"type": "integer", "default": 100},
                "enabled": {"type": "boolean", "default": True}
            }
        }
        
        # Verify schema structure
        assert default_schema["type"] == "object"
        assert "properties" in default_schema
        assert "api_key" in default_schema["properties"]
        assert "max_requests" in default_schema["properties"]
        
        # Verify property types
        assert default_schema["properties"]["api_key"]["type"] == "string"
        assert default_schema["properties"]["max_requests"]["type"] == "integer"
        assert default_schema["properties"]["max_requests"]["default"] == 100
    
    def test_marketplace_categories(self):
        """Test marketplace category definitions"""
        categories = [
            {"name": "productivity", "display_name": "Productivity"},
            {"name": "development", "display_name": "Development"},
            {"name": "content", "display_name": "Content Creation"},
            {"name": "analysis", "display_name": "Data Analysis"},
            {"name": "automation", "display_name": "Automation"},
            {"name": "communication", "display_name": "Communication"}
        ]
        
        # Verify all categories have required fields
        for category in categories:
            assert "name" in category
            assert "display_name" in category
            assert len(category["name"]) > 0
            assert len(category["display_name"]) > 0
    
    def test_marketplace_tags(self):
        """Test marketplace tag definitions"""
        tags = [
            "ai", "nlp", "automation", "productivity", "data-analysis",
            "machine-learning", "web-scraping", "email", "pdf", "scheduling"
        ]
        
        # Verify all tags are valid
        for tag in tags:
            assert isinstance(tag, str)
            assert len(tag) > 0
            assert tag.replace("-", "").replace("_", "").isalnum()


if __name__ == "__main__":
    pytest.main([__file__])