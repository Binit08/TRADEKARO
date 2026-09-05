import pytest
import time
from dataclasses import dataclass
from app.core.event_bus import EventBus

@dataclass
class MockEventA:
    message: str
    
@dataclass
class MockEventB:
    value: int

def test_event_bus_pub_sub_async():
    bus = EventBus()
    
    received_a = []
    received_b = []
    
    def on_event_a(event: MockEventA):
        received_a.append(event)
        
    def on_event_b(event: MockEventB):
        received_b.append(event)
        
    bus.subscribe(MockEventA, on_event_a)
    bus.subscribe(MockEventB, on_event_b)
    
    bus.start()
    
    bus.publish(MockEventA(message="hello"))
    bus.publish(MockEventB(value=42))
    
    # Allow some time for background thread to process
    time.sleep(0.1)
    
    bus.stop()
    
    assert len(received_a) == 1
    assert received_a[0].message == "hello"
    
    assert len(received_b) == 1
    assert received_b[0].value == 42
