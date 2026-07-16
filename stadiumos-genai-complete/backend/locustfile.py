"""
Locust load testing configuration for StadiumOS GenAI.

Simulates realistic matchday traffic patterns including:
- Fan navigation queries
- AI chat interactions
- Transport lookup
- Crowd monitoring
- Accessibility requests

Usage:
    # Web UI mode
    locust -f locustfile.py --host http://localhost:8000

    # Headless mode (CLI)
    locust -f locustfile.py --headless -u 500 -r 50 -t 5m --host http://localhost:8000

    # Generate HTML report
    locust -f locustfile.py --headless -u 1000 -r 100 -t 10m \
        --host http://localhost:8000 \
        --html evidence/load-testing/report.html
"""
from __future__ import annotations

import random

from locust import HttpUser, between, task


class StadiumFanUser(HttpUser):
    """
    Simulates a typical stadium fan using StadiumOS GenAI during a match.
    
    Behavior mimics real user patterns:
    - Arrives, checks navigation (high weight)
    - Occasionally asks chat questions
    - Checks transport options before/after match
    - Lower frequency for other features
    """
    
    # Users wait 1-5 seconds between requests (realistic think time)
    wait_time = between(1, 5)
    
    # Sample data for realistic requests
    origins = ["gate_a", "gate_b", "gate_c", "main_entrance"]
    destinations = [
        "section_101", "section_120", "section_215", "section_310",
        "family_zone", "accessible_seating", "medical_station",
        "restroom_a", "food_court", "merchandise"
    ]
    
    languages = ["English", "Spanish", "French", "German", "Portuguese"]
    
    accessibility_needs = [
        [],
        ["wheelchair"],
        ["visual_impairment"],
        ["hearing_impairment"],
    ]
    
    chat_questions = [
        "Where is the nearest restroom?",
        "How do I get to my seat in section 215?",
        "What food options are available?",
        "Is there a family area?",
        "Where can I buy merchandise?",
        "How do I access accessible seating?",
        "What time does the match start?",
        "Where is the first aid station?",
    ]
    
    def on_start(self):
        """Called when a user starts. Can be used for login, etc."""
        self.language = random.choice(self.languages)
        self.needs_accessibility = random.random() < 0.15  # 15% need accessibility
    
    @task(10)  # Weight: 10 (most common request)
    def navigate_to_seat(self):
        """User navigating to their seat or facility."""
        origin = random.choice(self.origins)
        destination = random.choice(self.destinations)
        
        payload = {
            "origin": origin,
            "destination": destination,
            "language": self.language,
            "accessibility_needs": random.choice(self.accessibility_needs) if self.needs_accessibility else []
        }
        
        with self.client.post(
            "/api/v1/navigate",
            json=payload,
            catch_response=True,
            name="/api/v1/navigate"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("steps"):
                    response.success()
                else:
                    response.failure("No navigation steps returned")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)  # Weight: 5
    def ask_chat_question(self):
        """User asking a question via chat."""
        question = random.choice(self.chat_questions)
        role = random.choice(["fan", "volunteer"])
        
        payload = {
            "message": question,
            "language": self.language,
            "role": role,
            "context": {
                "location": random.choice(self.origins),
                "time_to_match": random.randint(5, 120)
            }
        }
        
        with self.client.post(
            "/api/v1/chat",
            json=payload,
            catch_response=True,
            name="/api/v1/chat"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("response"):
                    response.success()
                else:
                    response.failure("No chat response")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)  # Weight: 3
    def check_transport(self):
        """User checking transport options."""
        payload = {
            "mode_preferences": random.choice([
                ["public_transit"],
                ["parking"],
                ["rideshare"],
                ["public_transit", "walking"],
            ]),
            "accessibility_needs": random.choice(self.accessibility_needs) if self.needs_accessibility else []
        }
        
        with self.client.post(
            "/api/v1/transport",
            json=payload,
            catch_response=True,
            name="/api/v1/transport"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("options"):
                    response.success()
                else:
                    response.failure("No transport options")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)  # Weight: 2
    def get_accessibility_info(self):
        """User requesting accessibility information."""
        payload = {
            "need_type": random.choice([
                "wheelchair_access",
                "visual_impairment",
                "hearing_impairment",
                "sensory_accommodations",
                "general_accessibility"
            ]),
            "location": random.choice(self.origins),
            "language": self.language
        }
        
        with self.client.post(
            "/api/v1/accessibility",
            json=payload,
            catch_response=True,
            name="/api/v1/accessibility"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)  # Weight: 2
    def get_sustainability_tips(self):
        """User requesting sustainability information."""
        payload = {
            "category": random.choice([
                "general",
                "transportation",
                "waste_recycling",
                "local_engagement"
            ]),
            "language": self.language
        }
        
        with self.client.post(
            "/api/v1/sustainability",
            json=payload,
            catch_response=True,
            name="/api/v1/sustainability"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)  # Weight: 1 (rare)
    def translate_message(self):
        """User requesting translation."""
        texts = [
            "Where is the bathroom?",
            "Thank you very much",
            "Can you help me?",
            "Where is section 215?",
        ]
        
        payload = {
            "text": random.choice(texts),
            "target_language": random.choice([lang for lang in self.languages if lang != self.language]),
            "source_language": self.language
        }
        
        with self.client.post(
            "/api/v1/translate",
            json=payload,
            catch_response=True,
            name="/api/v1/translate"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("translated_text"):
                    response.success()
                else:
                    response.failure("No translation returned")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)  # Weight: 1 (rare but important)
    def check_health(self):
        """Monitoring/health check."""
        with self.client.get(
            "/api/v1/health",
            catch_response=True,
            name="/api/v1/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class StadiumOperatorUser(HttpUser):
    """
    Simulates stadium operator/staff checking crowd and system status.
    Lower frequency but important for operational monitoring.
    """
    
    wait_time = between(5, 15)  # Operators check less frequently
    
    @task(5)  # Weight: 5
    def analyze_crowd(self):
        """Operator checking crowd levels."""
        zones = ["gate_a", "gate_b", "gate_c", "concourse_north", "concourse_south"]
        
        payload = {
            "zones": [
                {
                    "zone_id": zone,
                    "current_occupancy": random.randint(50, 800),
                    "capacity": random.randint(500, 1000)
                }
                for zone in random.sample(zones, k=random.randint(2, 4))
            ],
            "generate_briefing": random.random() < 0.3  # 30% want AI briefing
        }
        
        with self.client.post(
            "/api/v1/crowd/analyze",
            json=payload,
            catch_response=True,
            name="/api/v1/crowd/analyze"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("analysis"):
                    response.success()
                else:
                    response.failure("No crowd analysis")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)  # Weight: 2
    def emergency_check(self):
        """Operator checking emergency procedures."""
        payload = {
            "incident_type": random.choice([
                "medical_emergency",
                "crowd_surge",
                "weather_alert",
                "security_concern",
                "accessibility_issue"
            ]),
            "severity": random.choice(["low", "medium", "high"]),
            "affected_zones": random.sample(["gate_a", "section_101", "concourse_north"], k=2),
            "language": "English"
        }
        
        with self.client.post(
            "/api/v1/emergency",
            json=payload,
            catch_response=True,
            name="/api/v1/emergency"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


# Configure load test shapes
class MatchdayTraffic(HttpUser):
    """
    Combined user type with realistic matchday distribution:
    - 90% fans
    - 10% operators/staff
    """
    tasks = {
        StadiumFanUser: 9,
        StadiumOperatorUser: 1
    }
    wait_time = between(1, 5)
