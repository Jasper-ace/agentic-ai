# Part I: Code Debugging/Correction (10 Points)

### 1. The Stateless Loop (2 pts)

**Error:**  
Chat session initialized inside the loop

**Fix:**  
 Move chat = client.chats.create(...) outside the loop so the same session is reused

### 2. The Leaky Identity (2 pts)

**Error:**  
The System Instruction only defines the agent's identity but does not include behavioral constraints, so the model may reveal the answer instead of giving only a hint.

**Fix (System Instruction):**  
You are a math tutor. Be helpful. Only provide hints and explanations. Never reveal the final answer unless explicitly instructed to do so.

### 3. The Memory Bloat (2 pts)

**Error:**  
Incorrect history it keeps the first message instead of th most recent turn.

**Fix (Line B):**  
chat.history = chat.history[-2:] (keep only the last 2 messages).

### 4. The Perception Crash (2 pts)

**Error:**  
Missing required price field cause ValidationError

**Fix (Pydantic Model):**  
Make price optional (Optional[float] = None)

### 5. The Infinite Backoff (2 pts)

**Error:**  
Infinite retry loop for non-429 errors.

**Fix (Else Block):**  
raise e to stop retrying unrecoverable errors.

---

# Part II: Schema Design & Evaluation (10 Points)

## Task 1: The Multi-Agent Router (5 Points)

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from enum import Enum

class Department(str, Enum):
    PAYROLL = "PAYROLL"
    RECRUITING = "RECRUITING"
    LEAVE_REQUEST = "LEAVE_REQUEST"

```

---

## Task 2: Architecture Evaluation (5 Points)
Architecture B is better, because Pydantic Response Schema validates outputs and prevents malformed data, while the Sliding Window reduces token usage and API costs. 
The ReAct loop also improves reliability by allowing self-correction. Therefore, it is more resilient and cost-effective for 24/7 operation.







