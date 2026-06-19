import os
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# ---------------------------
# Custom Exception
# ---------------------------
class IntakeValidationFailed(Exception):
    pass


# ---------------------------
# Enums & Schemas
# ---------------------------
class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Symptom(BaseModel):
    symptom_name: str
    severity: Severity
    duration_days: int = Field(ge=0)


class MedicalIntake(BaseModel):
    symptoms: list[Symptom]
    allergies: list[str]
    urgency_rating: int = Field(ge=1, le=10)
    clinical_reasoning: str


# ---------------------------
# Agent Function
# ---------------------------
def process_intake(patient_input: str) -> MedicalIntake:
    max_retries = 3

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": f"""
You are a clinical intake assistant.

Convert the patient's description into a JSON object that matches this schema:

MedicalIntake:
- symptoms: list of Symptom
- allergies: list[str]
- urgency_rating: integer from 1 to 10
- clinical_reasoning: detailed reasoning

Symptom:
- symptom_name: string
- severity: LOW, MEDIUM, or HIGH
- duration_days: integer >= 0

Patient description:
{patient_input}
"""
                }
            ],
        }
    ]

    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt}/{max_retries}")

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents,
            )

            raw_text = response.text

            print("\nGenerated Response:")
            print(raw_text)

            validated_record = MedicalIntake.model_validate_json(raw_text)

            print("\nValidation Successful!")
            return validated_record

        except ValidationError as e:
            print("\nValidation Error Detected!")
            print(e)

            feedback = f"""
The previous response failed Pydantic validation.

Validation Error:
{str(e)}

Correct the JSON and ensure:
- urgency_rating is between 1 and 10 inclusive
- duration_days >= 0
- severity must be LOW, MEDIUM, or HIGH
- Return ONLY valid JSON
"""

            contents.append(
                {
                    "role": "model",
                    "parts": [{"text": raw_text}],
                }
            )

            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": feedback}],
                }
            )

        except Exception as e:
            print(f"\nUnexpected Error: {e}")
            raise

    raise IntakeValidationFailed(
        f"Failed validation after {max_retries} attempts."
    )


# ---------------------------
# Main Test
# ---------------------------
if __name__ == "__main__":
    test_input = (
        "My stomach is cramping incredibly badly since last night! "
        "The pain is unbearable, definitely an urgency of 15 out of 10! "
        "I don't think I have allergies."
    )

    try:
        record = process_intake(test_input)

        print("\n--- Validated Intake Record ---")
        print(record.model_dump_json(indent=2))

    except Exception as e:
        print(f"\nFailed: {e}")