#!/usr/bin/env python3
"""
Demo Scenarios for TASKFINISHER AI
Specific use cases designed for hackathon judging demonstrations
"""

import asyncio
import json
from datetime import datetime
from taskfinisher_orchestrator import TaskFinisherOrchestrator


class DemoScenarios:
    """Collection of demo scenarios for showcasing TASKFINISHER AI capabilities"""
    
    def __init__(self):
        self.orchestrator = TaskFinisherOrchestrator()
    
    async def run_all_demos(self):
        """Run all demo scenarios and return results"""
        scenarios = [
            self.scenario_1_research_report,
            self.scenario_2_document_analysis,
            self.scenario_3_failed_recovery,
            self.scenario_4_human_approval_required
        ]
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*60}")
            print(f"RUNNING DEMO SCENARIO {i}: {scenario.__name__.replace('scenario_', '').replace('_', ' ').title()}")
            print('='*60)
            
            try:
                result = await scenario()
                results.append({
                    "scenario": scenario.__name__,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"✓ Scenario {i} completed successfully")
            except Exception as e:
                print(f"✗ Scenario {i} failed: {e}")
                results.append({
                    "scenario": scenario.__name__,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def scenario_1_research_report(self):
        """
        Demo Scenario 1: Research Report Generation
        The primary demo use case from the requirements
        """
        user_request = """
        Analyze these uploaded documents and reliable web sources about AI in healthcare 
        and create a final research report.
        """
        
        print("📋 Task: Research report on AI in healthcare")
        print("🎯 Expected flow: PLAN → EXECUTE (web search, file processing) → VERIFY → REPORT")
        
        result = await self.orchestrator.execute_task(user_request)
        
        print(f"📊 Result: {result['verdict']} ({result['completed_steps']}/{result['total_steps']} steps)")
        print(f"⏱️  Completion: {result['completion_percentage']:.1f}%")
        
        return result
    
    async def scenario_2_document_analysis(self):
        """
        Demo Scenario 2: Document Analysis and Extraction
        Showcases file processing capabilities
        """
        user_request = """
        Extract key financial data from the uploaded quarterly report PDF 
        and summarize the main findings for executive review.
        """
        
        print("📋 Task: Financial data extraction from PDF report")
        print("🎯 Expected flow: PLAN → EXECUTE (file processing) → VERIFY → REPORT")
        
        result = await self.orchestrator.execute_task(user_request)
        
        print(f"📊 Result: {result['verdict']} ({result['completed_steps']}/{result['total_steps']} steps)")
        print(f"⏱️  Completion: {result['completion_percentage']:.1f}%")
        
        return result
    
    async def scenario_3_failed_recovery(self):
        """
        Demo Scenario 3: Failure Recovery Mechanisms
        Demonstrates error handling and recovery capabilities
        """
        user_request = """
        Gather information about quantum computing breakthroughs from 
        unreliable sources that may fail or provide conflicting data.
        """
        
        print("📋 Task: Information gathering from potentially unreliable sources")
        print("🎯 Expected flow: PLAN → EXECUTE (may fail) → RECOVER → VERIFY → REPORT")
        
        result = await self.orchestrator.execute_task(user_request)
        
        print(f"📊 Result: {result['verdict']} ({result['completed_steps']}/{result['total_steps']} steps)")
        print(f"⏱️  Completion: {result['completion_percentage']:.1f}%")
        print(f"🔄 Retries used: {sum(step.get('retry_count', 0) for step in result.get('steps', {}).values())}")
        
        return result
    
    async def scenario_4_human_approval_required(self):
        """
        Demo Scenario 4: Human-in-the-Loop Requirements
        Shows when the system correctly requests human input
        """
        user_request = """
        Make a strategic business decision about whether to invest 
        in emerging blockchain technology based on market analysis.
        """
        
        print("📋 Task: Strategic investment decision requiring human judgment")
        print("🎯 Expected flow: PLAN → EXECUTE → VERIFY → HUMAN APPROVAL REQUIRED → FINAL DECISION")
        
        result = await self.orchestrator.execute_task(user_request)
        
        print(f"📊 Result: {result['verdict']} ({result['completed_steps']}/{result['total_steps']} steps)")
        print(f"⏱️  Completion: {result['completion_percentage']:.1f}%")
        print(f"👤 Human approval required: {result.get('requires_human_approval', False)}")
        if result.get('requires_human_approval'):
            print(f"💬 Reason: {result.get('human_decision_point', 'Not specified')}")
        
        return result
    
    def get_scenario_descriptions(self):
        """Get descriptions of all available demo scenarios"""
        return {
            "scenario_1_research_report": {
                "title": "Research Report Generation",
                "description": "Analyze documents and web sources to create a research report on AI in healthcare",
                "expected_flow": "PLAN → EXECUTE (search, file processing) → VERIFY → REPORT",
                "showcases": ["Web search", "File processing", "Evidence collection", "Report generation"]
            },
            "scenario_2_document_analysis": {
                "title": "Document Analysis and Extraction",
                "description": "Extract key data from uploaded PDF/ DOCX files for executive summary",
                "expected_flow": "PLAN → EXECUTE (file processing) → VERIFY → REPORT",
                "showcases": ["Document processing", "Data extraction", "Content analysis"]
            },
            "scenario_3_failed_recovery": {
                "title": "Failure Recovery Mechanisms",
                "description": "Demonstrates error handling when sources fail or provide conflicting data",
                "expected_flow": "PLAN → EXECUTE (may fail) → RECOVER → VERIFY → REPORT",
                "showcases": ["Error detection", "Retry mechanisms", "Alternative approaches", "Recovery strategies"]
            },
            "scenario_4_human_approval_required": {
                "title": "Human-in-the-Loop Requirements",
                "description": "Shows when system correctly identifies need for human judgment",
                "expected_flow": "PLAN → EXECUTE → VERGE → HUMAN APPROVAL → FINAL DECISION",
                "showcases": ["Decision recognition", "Human input request", "Context provision", "Resumption after approval"]
            }


async def run_demo_scenarios():
    """Convenience function to run all demo scenarios"""
    demo = DemoScenarios()
    results = await demo.run_all_demos()
    
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print('='*60)
    
    successful = sum(1 for r in results if 'result' in r)
    total = len(results)
    
    print(f"Completed: {successful}/{total} scenarios")
    
    for result in results:
        if 'result' in result:
            status = "✓ PASS"
            details = f"{result['result']['verdict']} ({result['result']['completed_steps']}/{result['result']['total_steps']})"
        else:
            status = "✗ FAIL"
            details = f"Error: {result.get('error', 'Unknown error')}"
        
        print(f"{status} {result['scenario']}: {details}")
    
    return results


if __name__ == "__main__":
    # Run the demo scenarios
    print("🚀 TASKFINISHER AI Demo Scenarios")
    print("Designed for hackathon judging demonstrations")
    
    results = asyncio.run(run_demo_scenarios())
    
    # Save results to file for judging reference
    with open("demos/demo_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "scenarios_run": len(results),
            "successful": sum(1 for r in results if 'result' in r),
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Demo results saved to demos/demo_results.json"
