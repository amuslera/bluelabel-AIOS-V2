"""
Performance monitoring service for ROI workflow optimization.
Tracks performance metrics, memory usage, and processing times.
"""
import psutil
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any] = None


class PerformanceMonitor:
    """Performance monitoring and metrics collection service"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.processing_times: deque = deque(maxlen=max_history)
        self.memory_usage: deque = deque(maxlen=max_history)
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Start background monitoring
        self._monitoring_active = True
        self._monitoring_task = None
    
    def start_monitoring(self):
        """Start background monitoring task"""
        if not self._monitoring_task or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitor_system_metrics())
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            await self._monitoring_task
    
    async def _monitor_system_metrics(self):
        """Background task to monitor system metrics"""
        while self._monitoring_active:
            try:
                # Memory usage
                memory = psutil.virtual_memory()
                self.record_metric("memory_usage_percent", memory.percent, "percent")
                self.record_metric("memory_used_gb", memory.used / (1024**3), "GB")
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_metric("cpu_usage_percent", cpu_percent, "percent")
                
                # Store in memory usage history
                self.memory_usage.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "cpu_percent": cpu_percent
                })
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def record_metric(self, name: str, value: float, unit: str, context: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_name=name,
            value=value,
            unit=unit,
            context=context or {}
        )
        
        self.metrics_history[name].append(asdict(metric))
    
    def start_workflow_timer(self, workflow_id: str) -> str:
        """Start timing a workflow"""
        timer_id = f"workflow_{workflow_id}"
        self.active_workflows[timer_id] = {
            "workflow_id": workflow_id,
            "start_time": time.time(),
            "steps": {}
        }
        return timer_id
    
    def start_step_timer(self, workflow_id: str, step_name: str) -> str:
        """Start timing a workflow step"""
        timer_id = f"workflow_{workflow_id}"
        if timer_id in self.active_workflows:
            self.active_workflows[timer_id]["steps"][step_name] = {
                "start_time": time.time()
            }
        return f"{timer_id}_{step_name}"
    
    def end_step_timer(self, workflow_id: str, step_name: str, success: bool = True, cache_hit: bool = False):
        """End timing a workflow step"""
        timer_id = f"workflow_{workflow_id}"
        if timer_id in self.active_workflows and step_name in self.active_workflows[timer_id]["steps"]:
            start_time = self.active_workflows[timer_id]["steps"][step_name]["start_time"]
            duration = time.time() - start_time
            
            # Record step performance
            self.record_metric(
                f"step_{step_name}_duration",
                duration,
                "seconds",
                {
                    "workflow_id": workflow_id,
                    "success": success,
                    "cache_hit": cache_hit
                }
            )
            
            # Update step info
            self.active_workflows[timer_id]["steps"][step_name].update({
                "end_time": time.time(),
                "duration": duration,
                "success": success,
                "cache_hit": cache_hit
            })
    
    def end_workflow_timer(self, workflow_id: str, success: bool = True) -> float:
        """End timing a workflow and return duration"""
        timer_id = f"workflow_{workflow_id}"
        if timer_id not in self.active_workflows:
            return 0.0
        
        start_time = self.active_workflows[timer_id]["start_time"]
        duration = time.time() - start_time
        
        # Record workflow performance
        self.record_metric(
            "workflow_total_duration",
            duration,
            "seconds",
            {
                "workflow_id": workflow_id,
                "success": success,
                "steps": self.active_workflows[timer_id]["steps"]
            }
        )
        
        # Store in processing times
        self.processing_times.append({
            "workflow_id": workflow_id,
            "duration": duration,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": self.active_workflows[timer_id]["steps"]
        })
        
        # Clean up
        del self.active_workflows[timer_id]
        
        return duration
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent processing times
        recent_times = [
            pt for pt in self.processing_times
            if datetime.fromisoformat(pt["timestamp"]) > cutoff
        ]
        
        # Calculate statistics
        if recent_times:
            durations = [pt["duration"] for pt in recent_times if pt["success"]]
            avg_duration = sum(durations) / len(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            
            # Calculate cache performance
            cache_hits = 0
            cache_misses = 0
            for pt in recent_times:
                for step_name, step_data in pt.get("steps", {}).items():
                    if step_data.get("cache_hit"):
                        cache_hits += 1
                    else:
                        cache_misses += 1
            
            cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
        else:
            avg_duration = min_duration = max_duration = 0
            cache_hit_rate = 0
            cache_hits = cache_misses = 0
        
        # Get recent memory usage
        recent_memory = list(self.memory_usage)[-10:] if self.memory_usage else []
        avg_memory = sum(m["memory_percent"] for m in recent_memory) / len(recent_memory) if recent_memory else 0
        avg_cpu = sum(m["cpu_percent"] for m in recent_memory) / len(recent_memory) if recent_memory else 0
        
        return {
            "time_window_hours": hours,
            "total_workflows": len(recent_times),
            "successful_workflows": len([pt for pt in recent_times if pt["success"]]),
            "failed_workflows": len([pt for pt in recent_times if not pt["success"]]),
            "processing_times": {
                "average_seconds": avg_duration,
                "min_seconds": min_duration,
                "max_seconds": max_duration
            },
            "cache_performance": {
                "hit_rate_percent": cache_hit_rate,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses
            },
            "system_performance": {
                "average_memory_percent": avg_memory,
                "average_cpu_percent": avg_cpu
            },
            "active_workflows": len(self.active_workflows)
        }
    
    def get_step_performance(self, step_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance data for a specific step"""
        if step_name not in self.metrics_history:
            return {"error": f"No data found for step: {step_name}"}
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        metric_name = f"step_{step_name}_duration"
        
        if metric_name not in self.metrics_history:
            return {"error": f"No timing data found for step: {step_name}"}
        
        recent_metrics = [
            m for m in self.metrics_history[metric_name]
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not recent_metrics:
            return {"message": f"No recent data for step: {step_name}"}
        
        durations = [m["value"] for m in recent_metrics]
        cache_hits = len([m for m in recent_metrics if m.get("context", {}).get("cache_hit", False)])
        
        return {
            "step_name": step_name,
            "executions": len(recent_metrics),
            "cache_hits": cache_hits,
            "cache_hit_rate": (cache_hits / len(recent_metrics)) * 100,
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return {
            "metrics_history": dict(self.metrics_history),
            "processing_times": list(self.processing_times),
            "memory_usage": list(self.memory_usage),
            "active_workflows": self.active_workflows
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()