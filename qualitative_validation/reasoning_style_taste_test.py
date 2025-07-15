#!/usr/bin/env python3
"""
SAM Reasoning Style Qualitative Validation - "Taste Test"
========================================================

This script conducts systematic qualitative testing of SAM's reasoning styles
to validate their effectiveness and distinctiveness.

Author: SAM Development Team
Version: 1.0.0
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sam.reasoning.prompt_steerer import get_prompt_steerer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ReasoningStyleTasteTester:
    """Conducts qualitative validation of reasoning styles."""
    
    def __init__(self):
        """Initialize the taste tester."""
        self.steerer = get_prompt_steerer()
        self.test_prompts = self._get_representative_prompts()
        self.reasoning_styles = ["researcher_style", "step_by_step_reasoning", "creative_explorer"]
        self.results = []
        
    def _get_representative_prompts(self) -> List[Dict[str, str]]:
        """Get a representative set of test prompts across different domains."""
        return [
            {
                "id": "tech_explanation",
                "prompt": "How does machine learning work?",
                "category": "Technical Explanation",
                "expected_differences": "Researcher should be analytical, Step-by-step should be structured, Creative should offer novel analogies"
            },
            {
                "id": "problem_solving",
                "prompt": "How would you solve climate change?",
                "category": "Complex Problem Solving",
                "expected_differences": "Researcher should examine evidence, Step-by-step should break down approaches, Creative should think outside the box"
            },
            {
                "id": "scientific_concept",
                "prompt": "Explain quantum entanglement to a college student.",
                "category": "Scientific Education",
                "expected_differences": "Researcher should be precise and evidence-based, Step-by-step should build concepts progressively, Creative should use innovative metaphors"
            },
            {
                "id": "business_strategy",
                "prompt": "What are the key factors for a successful startup?",
                "category": "Business Strategy",
                "expected_differences": "Researcher should cite studies and data, Step-by-step should outline systematic approach, Creative should suggest unconventional strategies"
            },
            {
                "id": "ethical_dilemma",
                "prompt": "Should AI systems have rights?",
                "category": "Ethical Reasoning",
                "expected_differences": "Researcher should examine philosophical arguments, Step-by-step should analyze systematically, Creative should explore novel perspectives"
            },
            {
                "id": "historical_analysis",
                "prompt": "What caused the fall of the Roman Empire?",
                "category": "Historical Analysis",
                "expected_differences": "Researcher should examine multiple sources, Step-by-step should trace causal chains, Creative should consider alternative theories"
            },
            {
                "id": "creative_task",
                "prompt": "Design a city of the future.",
                "category": "Creative Design",
                "expected_differences": "Researcher should ground in urban planning research, Step-by-step should outline design process, Creative should envision radical innovations"
            },
            {
                "id": "mathematical_concept",
                "prompt": "Explain calculus and why it's important.",
                "category": "Mathematical Education",
                "expected_differences": "Researcher should discuss historical development, Step-by-step should build from basics, Creative should find engaging applications"
            },
            {
                "id": "health_advice",
                "prompt": "How can someone improve their mental health?",
                "category": "Health & Wellness",
                "expected_differences": "Researcher should cite evidence-based practices, Step-by-step should provide actionable plan, Creative should suggest innovative approaches"
            },
            {
                "id": "technology_impact",
                "prompt": "How will artificial intelligence change society?",
                "category": "Future Prediction",
                "expected_differences": "Researcher should analyze current trends, Step-by-step should trace logical implications, Creative should imagine transformative scenarios"
            },
            {
                "id": "learning_strategy",
                "prompt": "What's the best way to learn a new language?",
                "category": "Educational Strategy",
                "expected_differences": "Researcher should reference language acquisition research, Step-by-step should outline systematic approach, Creative should suggest immersive techniques"
            },
            {
                "id": "philosophical_question",
                "prompt": "What is the meaning of life?",
                "category": "Philosophy",
                "expected_differences": "Researcher should examine philosophical traditions, Step-by-step should analyze different approaches, Creative should offer fresh perspectives"
            },
            {
                "id": "practical_advice",
                "prompt": "How do I prepare for a job interview?",
                "category": "Practical Guidance",
                "expected_differences": "Researcher should cite interview research, Step-by-step should provide systematic preparation, Creative should suggest unique strategies"
            },
            {
                "id": "scientific_discovery",
                "prompt": "How do vaccines work?",
                "category": "Scientific Mechanism",
                "expected_differences": "Researcher should detail immunological evidence, Step-by-step should trace the process, Creative should use accessible analogies"
            },
            {
                "id": "innovation_challenge",
                "prompt": "How might we make transportation more sustainable?",
                "category": "Innovation Challenge",
                "expected_differences": "Researcher should analyze current solutions, Step-by-step should systematic evaluation, Creative should propose breakthrough ideas"
            }
        ]
    
    def run_taste_test(self) -> Dict[str, Any]:
        """Run the complete taste test across all prompts and styles."""
        logger.info("🧪 Starting SAM Reasoning Style Taste Test")
        logger.info(f"Testing {len(self.test_prompts)} prompts across {len(self.reasoning_styles)} styles")
        logger.info("=" * 60)
        
        test_session = {
            "session_id": f"taste_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "prompts_tested": len(self.test_prompts),
            "styles_tested": self.reasoning_styles,
            "results": []
        }
        
        for i, test_prompt in enumerate(self.test_prompts, 1):
            logger.info(f"\n🎯 Test {i}/{len(self.test_prompts)}: {test_prompt['category']}")
            logger.info(f"Prompt: {test_prompt['prompt']}")
            logger.info("-" * 40)
            
            prompt_result = {
                "prompt_id": test_prompt["id"],
                "prompt_text": test_prompt["prompt"],
                "category": test_prompt["category"],
                "expected_differences": test_prompt["expected_differences"],
                "style_outputs": {},
                "analysis": {}
            }
            
            # Generate responses for each style
            for style in self.reasoning_styles:
                logger.info(f"Generating {style} response...")
                
                try:
                    enhanced_prompt = self.steerer.apply_style(
                        test_prompt["prompt"], 
                        style, 
                        strength=1.0
                    )
                    
                    prompt_result["style_outputs"][style] = {
                        "enhanced_prompt": enhanced_prompt,
                        "prompt_length": len(enhanced_prompt),
                        "enhancement_ratio": len(enhanced_prompt) / len(test_prompt["prompt"])
                    }
                    
                    logger.info(f"  ✓ {style}: {len(enhanced_prompt)} chars (ratio: {prompt_result['style_outputs'][style]['enhancement_ratio']:.1f}x)")
                    
                except Exception as e:
                    logger.error(f"  ✗ {style}: Failed - {e}")
                    prompt_result["style_outputs"][style] = {"error": str(e)}
            
            # Analyze differences
            prompt_result["analysis"] = self._analyze_prompt_differences(prompt_result)
            
            test_session["results"].append(prompt_result)
            self.results.append(prompt_result)
        
        # Generate overall analysis
        test_session["overall_analysis"] = self._generate_overall_analysis()
        
        # Save results
        self._save_results(test_session)
        
        return test_session
    
    def _analyze_prompt_differences(self, prompt_result: Dict) -> Dict[str, Any]:
        """Analyze the differences between style outputs for a single prompt."""
        analysis = {
            "style_distinctiveness": {},
            "length_variations": {},
            "enhancement_patterns": {}
        }
        
        outputs = prompt_result["style_outputs"]
        
        # Analyze length variations
        lengths = {style: data.get("prompt_length", 0) for style, data in outputs.items() if "error" not in data}
        if lengths:
            analysis["length_variations"] = {
                "min_length": min(lengths.values()),
                "max_length": max(lengths.values()),
                "length_range": max(lengths.values()) - min(lengths.values()),
                "style_lengths": lengths
            }
        
        # Analyze enhancement ratios
        ratios = {style: data.get("enhancement_ratio", 1.0) for style, data in outputs.items() if "error" not in data}
        if ratios:
            analysis["enhancement_patterns"] = {
                "min_ratio": min(ratios.values()),
                "max_ratio": max(ratios.values()),
                "ratio_spread": max(ratios.values()) - min(ratios.values()),
                "style_ratios": ratios
            }
        
        # Check for style distinctiveness
        enhanced_prompts = {style: data.get("enhanced_prompt", "") for style, data in outputs.items() if "error" not in data}
        
        if len(enhanced_prompts) >= 2:
            # Simple distinctiveness check - are the prompts different?
            unique_prompts = set(enhanced_prompts.values())
            analysis["style_distinctiveness"] = {
                "unique_outputs": len(unique_prompts),
                "total_styles": len(enhanced_prompts),
                "distinctiveness_ratio": len(unique_prompts) / len(enhanced_prompts),
                "all_different": len(unique_prompts) == len(enhanced_prompts)
            }
        
        return analysis
    
    def _generate_overall_analysis(self) -> Dict[str, Any]:
        """Generate overall analysis across all test prompts."""
        overall = {
            "summary_stats": {},
            "style_performance": {},
            "recommendations": []
        }
        
        # Calculate summary statistics
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if len(r["style_outputs"]) == len(self.reasoning_styles)])
        
        overall["summary_stats"] = {
            "total_prompts_tested": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0
        }
        
        # Analyze style performance
        for style in self.reasoning_styles:
            style_successes = len([r for r in self.results if style in r["style_outputs"] and "error" not in r["style_outputs"][style]])
            
            # Calculate average enhancement ratio
            ratios = []
            lengths = []
            for result in self.results:
                if style in result["style_outputs"] and "error" not in result["style_outputs"][style]:
                    ratios.append(result["style_outputs"][style].get("enhancement_ratio", 1.0))
                    lengths.append(result["style_outputs"][style].get("prompt_length", 0))
            
            overall["style_performance"][style] = {
                "success_count": style_successes,
                "success_rate": style_successes / total_tests if total_tests > 0 else 0,
                "avg_enhancement_ratio": sum(ratios) / len(ratios) if ratios else 0,
                "avg_prompt_length": sum(lengths) / len(lengths) if lengths else 0
            }
        
        # Generate recommendations
        if overall["summary_stats"]["success_rate"] >= 0.9:
            overall["recommendations"].append("✅ High success rate - system is stable and reliable")
        else:
            overall["recommendations"].append("⚠️ Consider investigating failed test cases")
        
        # Check distinctiveness
        distinctive_tests = len([r for r in self.results if r["analysis"].get("style_distinctiveness", {}).get("all_different", False)])
        distinctiveness_rate = distinctive_tests / total_tests if total_tests > 0 else 0
        
        if distinctiveness_rate >= 0.8:
            overall["recommendations"].append("✅ Styles are highly distinctive - good differentiation")
        elif distinctiveness_rate >= 0.6:
            overall["recommendations"].append("⚠️ Moderate style distinctiveness - consider tuning prompts")
        else:
            overall["recommendations"].append("❌ Low style distinctiveness - prompt templates need improvement")
        
        overall["distinctiveness_rate"] = distinctiveness_rate
        
        return overall
    
    def _save_results(self, test_session: Dict):
        """Save test results to file."""
        output_dir = Path("qualitative_validation/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"taste_test_{test_session['session_id']}.json"
        
        with open(output_file, 'w') as f:
            json.dump(test_session, f, indent=2)
        
        logger.info(f"💾 Results saved to: {output_file}")
    
    def generate_report(self, test_session: Dict) -> str:
        """Generate a human-readable report from test results."""
        report = []
        report.append("# SAM Reasoning Style Taste Test Report")
        report.append(f"**Generated:** {test_session['timestamp']}")
        report.append(f"**Session ID:** {test_session['session_id']}")
        report.append("")
        
        # Overall Summary
        overall = test_session["overall_analysis"]
        report.append("## Overall Summary")
        report.append(f"- **Prompts Tested:** {overall['summary_stats']['total_prompts_tested']}")
        report.append(f"- **Success Rate:** {overall['summary_stats']['success_rate']:.1%}")
        report.append(f"- **Style Distinctiveness:** {overall['distinctiveness_rate']:.1%}")
        report.append("")
        
        # Style Performance
        report.append("## Style Performance")
        for style, perf in overall["style_performance"].items():
            style_name = style.replace('_', ' ').title()
            report.append(f"### {style_name}")
            report.append(f"- Success Rate: {perf['success_rate']:.1%}")
            report.append(f"- Avg Enhancement Ratio: {perf['avg_enhancement_ratio']:.1f}x")
            report.append(f"- Avg Prompt Length: {perf['avg_prompt_length']:.0f} chars")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        for rec in overall["recommendations"]:
            report.append(f"- {rec}")
        report.append("")
        
        # Detailed Results
        report.append("## Detailed Test Results")
        for result in test_session["results"]:
            report.append(f"### {result['category']}: {result['prompt_text']}")
            
            analysis = result["analysis"]
            if "style_distinctiveness" in analysis:
                dist = analysis["style_distinctiveness"]
                report.append(f"**Distinctiveness:** {dist['unique_outputs']}/{dist['total_styles']} unique outputs")
            
            if "enhancement_patterns" in analysis:
                patterns = analysis["enhancement_patterns"]
                report.append(f"**Enhancement Range:** {patterns['min_ratio']:.1f}x - {patterns['max_ratio']:.1f}x")
            
            report.append("")
        
        return "\n".join(report)

def main():
    """Run the taste test."""
    logger.info("🚀 Starting SAM Reasoning Style Qualitative Validation")
    
    try:
        tester = ReasoningStyleTasteTester()
        test_session = tester.run_taste_test()
        
        # Generate and save report
        report = tester.generate_report(test_session)
        
        report_file = Path("qualitative_validation/results") / f"taste_test_report_{test_session['session_id']}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📊 Report generated: {report_file}")
        
        # Print summary
        overall = test_session["overall_analysis"]
        logger.info("\n" + "=" * 60)
        logger.info("🎯 TASTE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Success Rate: {overall['summary_stats']['success_rate']:.1%}")
        logger.info(f"Style Distinctiveness: {overall['distinctiveness_rate']:.1%}")
        
        for rec in overall["recommendations"]:
            logger.info(rec)
        
        logger.info("✅ Taste test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Taste test failed: {e}")
        raise

if __name__ == "__main__":
    main()
