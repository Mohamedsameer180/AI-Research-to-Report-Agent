#!/usr/bin/env python3
"""
Comprehensive Test Suite for TASKFINISHER AI
Tests all major components and functionality
"""

import sys
import os
import tempfile
import json
import gc
import asyncio
import io
import zipfile

# Add project directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'tools'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'database'))


def test_file_structure():
    """Test that all required files and directories exist"""
    print("🧪 Testing file structure...")
    
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    required_files = [
        'backend/taskfinisher_orchestrator.py',
        'backend/main.py',
        'backend/requirements.txt',
        'README.md',
        'demo.py',
        'test_basic.py'
    ]
    
    required_dirs = [
        'backend',
        'frontend',
        'backend/agents',
        'backend/tools',
        'tests',
        'docs',
        'backend/database',
        'demos'
    ]
    
    all_good = True
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            all_good = False
    
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if os.path.isdir(full_path):
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ (missing)")
            all_good = False
    
    return all_good


def test_python_syntax():
    """Test that Python files can be imported without syntax errors"""
    print("\\n🧪 Testing Python syntax...")
    
    try:
        # Test importing our main modules
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from taskfinisher_orchestrator import TaskFinisherOrchestrator, TaskStatus
        print("  ✓ taskfinisher_orchestrator.py imports successfully")
        
        from main import app
        print("  ✓ main.py imports successfully")
        
        # Test tools
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from tools.web_search_tool import web_search_tool
        from tools.file_processor_tool import file_processor_tool
        from tools.web_scraper_tool import web_scraper_tool
        print("  ✓ All tool modules import successfully")
        
        # Test database
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from database.db_manager import db_manager, TaskDatabase
        print("  ✓ Database module imports successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_orchestrator_initialization():
    """Test that the orchestrator initializes correctly"""
    print("\\n🧪 Testing orchestrator initialization...")
    
    try:
        from taskfinisher_orchestrator import TaskFinisherOrchestrator
        
        orchestrator = TaskFinisherOrchestrator()
        
        # Check that agents are initialized
        expected_agents = [
            "planner", "research", "document", "verification",
            "recovery", "report", "human_approval", "final_verifier"
        ]
        
        for agent_name in expected_agents:
            if agent_name in orchestrator.agents:
                print(f"  ✓ Agent '{agent_name}' initialized")
            else:
                print(f"  ✗ Agent '{agent_name}' missing")
                return False

        research_tools = [tool.name for tool in orchestrator.agents["research"].tools]
        document_tools = [tool.name for tool in orchestrator.agents["document"].tools]
        recovery_tools = [tool.name for tool in orchestrator.agents["recovery"].tools]

        assert research_tools == ["web_search", "web_scraper"]
        assert document_tools == ["file_processor"]
        assert recovery_tools == ["web_search", "web_scraper", "file_processor"]
        print("  ✓ Google ADK agents have the expected tool wiring")
        
        # Check that tools are initialized
        expected_tools = ["web_search", "file_processor", "web_scraper"]
        for tool_name in expected_tools:
            if tool_name in orchestrator.tools:
                print(f"  ✓ Tool '{tool_name}' initialized")
            else:
                print(f"  ✗ Tool '{tool_name}' missing")
                return False
        
        print("  ✓ Orchestrator initialized correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Orchestrator initialization failed: {e}")
        return False


def test_task_state_models():
    """Test that the Pydantic models work correctly"""
    print("\\n🧪 Testing Pydantic models...")
    
    try:
        from taskfinisher_orchestrator import TaskStatus, StepResult, TaskState
        from datetime import datetime
        
        # Test TaskStatus enum
        assert TaskStatus.PENDING.value == "PENDING"
        assert TaskStatus.COMPLETED.value == "COMPLETED"
        print("  ✓ TaskStatus enum works correctly")
        
        # Test StepResult model
        step = StepResult(
            step_id="test_step",
            status=TaskStatus.COMPLETED,
            description="Test step description",
            agent="TestAgent"
        )
        assert step.step_id == "test_step"
        assert step.status == TaskStatus.COMPLETED
        print("  ✓ StepResult model works correctly")
        
        # Test TaskState model
        task_state = TaskState(
            task_id="test_task_123",
            user_request="Test user request"
        )
        assert task_state.task_id == "test_task_123"
        assert task_state.user_request == "Test user request"
        assert task_state.status == TaskStatus.PENDING
        print("  ✓ TaskState model works correctly")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Pydantic model test failed: {e}")
        return False


def test_database_manager():
    """Test that the database manager works correctly"""
    print("\\n🧪 Testing database manager...")
    
    try:
        from database.db_manager import TaskDatabase
        import tempfile
        import os
        
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Initialize database
            db = TaskDatabase(db_path)
            print("  ✓ Database initialized successfully")
            
            # Test saving a task
            test_task = {
                "task_id": "test_task_001",
                "user_request": "Test task for database",
                "status": "completed",
                "verdict": "DONE",
                "completed_steps": 5,
                "total_steps": 5,
                "evidence_trail": ["Step 1 completed", "Step 2 completed"],
                "requires_human_approval": False,
                "human_decision_point": None
            }
            
            result = db.save_task(test_task)
            assert result == True
            print("  ✓ Task saved to database successfully")
            
            # Test retrieving the task
            retrieved_task = db.get_task("test_task_001")
            assert retrieved_task is not None
            assert retrieved_task["task_id"] == "test_task_001"
            assert retrieved_task["user_request"] == "Test task for database"
            assert retrieved_task["verdict"] == "DONE"
            print("  ✓ Task retrieved from database successfully")
            
            # Test getting recent tasks
            recent_tasks = db.get_recent_tasks(limit=5)
            assert len(recent_tasks) >= 1
            print("  ✓ Recent tasks retrieved successfully")
            
            # Test database stats
            stats = db.get_database_stats()
            assert "total_tasks" in stats
            assert stats["total_tasks"] >= 1
            print("  ✓ Database statistics retrieved successfully")
            
            return True
            
        finally:
            gc.collect()
            # Clean up temporary file
            if os.path.exists(db_path):
                try:
                    os.unlink(db_path)
                except PermissionError:
                    pass
        
    except Exception as e:
        print(f"  ✗ Database manager test failed: {e}")
        return False


def test_api_models():
    """Test that the API Pydantic models work correctly"""
    print("\\n🧪 Testing API Pydantic models...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from main import TaskRequest, TaskResponse
        
        # Test TaskRequest
        request = TaskRequest(user_request="Test task request")
        assert request.user_request == "Test task request"
        print("  ✓ TaskRequest model works correctly")
        
        # Test TaskResponse
        response = TaskResponse(
            task_id="test_123",
            verdict="DONE",
            status="completed",
            completed_steps=5,
            total_steps=5,
            completion_percentage=100.0,
            evidence_trail=["Step 1", "Step 2"],
            requires_human_approval=False
        )
        assert response.task_id == "test_123"
        assert response.verdict == "DONE"
        assert response.completed_steps == 5
        print("  ✓ TaskResponse model works correctly")
        
        return True
        
    except Exception as e:
        print(f"  ✗ API model test failed: {e}")
        return False


def test_partial_completion_evidence_summary():
    """Test partial completion reports 5 PDFs, 4/5 web sources, and 2 retries."""
    print("\\n🧪 Testing partial completion evidence summary...")

    try:
        from taskfinisher_orchestrator import TaskFinisherOrchestrator

        orchestrator = TaskFinisherOrchestrator()
        result = asyncio.run(orchestrator.run_demo("partial"))

        assert result["verdict"] == "PARTIALLY_DONE"
        assert result["status"] == "PARTIALLY_COMPLETED"
        assert result["requires_human_approval"] is False
        assert result["adk_trace"]
        print("  ✓ Partial scenario returns an honest partial verdict")

        document_step = result["steps"]["S3"]
        research_step = result["steps"]["S4"]

        pdf_evidence = [
            item for item in document_step["evidence"]
            if item["type"] == "document" and item["metadata"].get("processed") is True
        ]
        verified_web_sources = [
            item for item in research_step["evidence"]
            if item["type"] == "web_source" and item["metadata"].get("status") == "VALID"
        ]
        unverified_web_sources = [
            item for item in research_step["evidence"]
            if item["type"] == "web_source_unverified"
        ]

        assert len(pdf_evidence) == 5
        assert len(verified_web_sources) == 4
        assert len(unverified_web_sources) == 1
        assert unverified_web_sources[0]["metadata"]["retry_attempts"] == 2
        assert research_step["attempts"] == 3
        print("  ✓ Evidence captures 5/5 PDFs, 4/5 web sources, and two retries")

        trace_agents = {item["agent_name"] for item in result["adk_trace"]}
        assert "DocumentAgent" in trace_agents
        assert "ResearchAgent" in trace_agents
        assert "RecoveryAgent" in trace_agents
        assert "FinalVerifierAgent" in trace_agents
        assert any("web_search" in item["tools"] for item in result["adk_trace"])
        assert any("file_processor" in item["tools"] for item in result["adk_trace"])
        print("  ✓ Google ADK trace records agent roles and tool usage")

        report = result["final_report"]
        assert "PDFs processed: 5/5" in report
        assert "Web sources verified: 4/5" in report
        assert "Retry attempts for failed web source: 2" in report
        assert "Task status: PARTIALLY COMPLETED" in report
        assert "Google ADK Agent Trace:" in report
        print("  ✓ Final report includes the requested partial-completion summary")

        return True

    except Exception as e:
        print(f"  ✗ Partial completion evidence test failed: {e}")
        return False


def test_report_download_endpoint():
    """Test completed research produces a downloadable DOCX report file."""
    print("\\n🧪 Testing report download endpoint...")

    try:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        task_response = client.post("/api/demo/success")
        assert task_response.status_code == 200
        task = task_response.json()
        assert "report.docx" in task["artifacts"]

        download_response = client.get(f"/api/tasks/{task['task_id']}/report/download")
        assert download_response.status_code == 200
        assert "attachment" in download_response.headers.get("content-disposition", "")
        assert f"{task['task_id']}_report.docx" in download_response.headers.get("content-disposition", "")
        assert "officedocument.wordprocessingml.document" in download_response.headers.get("content-type", "")

        with zipfile.ZipFile(io.BytesIO(download_response.content)) as docx:
            names = set(docx.namelist())
            assert "[Content_Types].xml" in names
            assert "word/document.xml" in names
            document_xml = docx.read("word/document.xml").decode("utf-8")
            assert "TASK COMPLETION REPORT" in document_xml
            assert "Final verdict: DONE" in document_xml

        print("  ✓ Final report downloads as a valid DOCX attachment")

        return True

    except Exception as e:
        print(f"  ✗ Report download endpoint test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and return overall success"""
    print("🚀 Starting TASKFINISHER AI Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_python_syntax,
        test_orchestrator_initialization,
        test_task_state_models,
        test_database_manager,
        test_api_models,
        test_partial_completion_evidence_summary,
        test_report_download_endpoint
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_func.__name__}")
    
    print(f"\\nOverall: {passed}/{total} test groups passed")
    
    if passed == total:
        print("🎉 All tests passed! TASKFINISHER AI is ready for hackathon judging.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
