Safety Modules
==============

Safety modules provide code validation, resource limit enforcement, and security checks
for generated code execution.

Code Validation
---------------

Validates generated code for safety and correctness.

.. automodule:: kosmos.safety.validator
   :members:
   :undoc-members:
   :show-inheritance:

Safety Rules
------------

Defines and enforces safety rules for code execution.

.. automodule:: kosmos.safety.rules
   :members:
   :undoc-members:
   :show-inheritance:

Resource Limits
---------------

Enforces resource limits (CPU, memory, time) for safe execution.

.. automodule:: kosmos.safety.limits
   :members:
   :undoc-members:
   :show-inheritance:

Safety Features
---------------

Kosmos implements multiple layers of safety:

**Code Validation**
   - AST analysis to detect dangerous operations
   - Blacklist of prohibited functions and imports
   - Whitelist of allowed modules

**Resource Limits**
   - CPU time limits
   - Memory usage caps
   - Disk space restrictions
   - Network access control

**Sandboxing**
   - Docker container isolation
   - Read-only filesystem (except output directory)
   - No privileged operations
   - Process monitoring

**Runtime Monitoring**
   - Real-time resource usage tracking
   - Automatic termination on limit exceeded
   - Detailed error reporting

Usage Examples
--------------

**Validating code before execution**::

   from kosmos.safety.validator import CodeValidator

   validator = CodeValidator()

   code = '''
   import numpy as np

   def analyze_data(data):
       result = np.mean(data)
       return result
   '''

   # Validate code
   validation_result = validator.validate(code)

   if validation_result.is_safe:
       print("Code is safe to execute")
       print(f"Allowed imports: {validation_result.imports}")
       print(f"Functions called: {validation_result.function_calls}")
   else:
       print("Code contains safety violations:")
       for violation in validation_result.violations:
           print(f"  - {violation.message}")
           print(f"    Severity: {violation.severity}")
           print(f"    Line: {violation.line_number}")

**Defining safety rules**::

   from kosmos.safety.rules import SafetyRuleSet

   # Create custom rule set
   rules = SafetyRuleSet()

   # Add rules
   rules.add_rule(
       name="no_file_write",
       description="Prohibit file write operations",
       check=lambda node: not (
           isinstance(node, ast.Call) and
           hasattr(node.func, 'id') and
           node.func.id in ['open', 'write']
       ),
       severity="high"
   )

   rules.add_rule(
       name="allowed_imports",
       description="Only allow specific imports",
       check=lambda node: (
           not isinstance(node, ast.Import) or
           all(alias.name in ALLOWED_MODULES for alias in node.names)
       ),
       severity="high"
   )

   # Validate with custom rules
   validator = CodeValidator(rules=rules)
   result = validator.validate(code)

**Setting resource limits**::

   from kosmos.safety.limits import ResourceLimits

   # Define limits
   limits = ResourceLimits(
       max_cpu_time_seconds=300,      # 5 minutes max
       max_memory_mb=4096,             # 4 GB RAM
       max_disk_mb=1024,               # 1 GB disk
       max_processes=10,               # Max 10 processes
       network_access=False,           # No network
       allow_gpu=False                 # No GPU access
   )

   # Use with executor
   from kosmos.execution.executor import Executor

   executor = Executor(resource_limits=limits)
   result = executor.execute(code, input_data)

**Monitoring execution**::

   from kosmos.safety.limits import ResourceMonitor

   monitor = ResourceMonitor(limits)

   # Start monitoring
   monitor.start()

   try:
       # Run code
       result = execute_user_code(code)

       # Check resource usage
       usage = monitor.get_usage()
       print(f"CPU time: {usage.cpu_time:.2f}s")
       print(f"Memory: {usage.memory_mb:.1f} MB")
       print(f"Disk: {usage.disk_mb:.1f} MB")

   finally:
       monitor.stop()

   # Check if limits were exceeded
   if monitor.limit_exceeded:
       print(f"Resource limit exceeded: {monitor.exceeded_resource}")

Prohibited Operations
---------------------

The following operations are blocked by default:

**File System**
   - Writing to files (except designated output directory)
   - Deleting files
   - Changing permissions
   - Creating symbolic links

**Network**
   - Socket operations
   - HTTP requests (unless explicitly allowed)
   - FTP, SSH, etc.

**System**
   - Executing shell commands
   - Spawning subprocesses (unless limited)
   - Accessing environment variables (unless allowed)
   - Modifying system settings

**Dangerous Modules**
   - `os.system`, `subprocess.Popen` (unrestricted)
   - `eval`, `exec`, `compile` (on user input)
   - `__import__`, `importlib` (dynamic imports)
   - `pickle`, `marshal` (arbitrary code execution)

Example prohibited code::

   # This will be blocked
   import os
   os.system("rm -rf /")  # Dangerous system command

   # This will be blocked
   import subprocess
   subprocess.call(["curl", "http://evil.com"])  # Network access

   # This will be blocked
   eval(user_input)  # Arbitrary code execution

Allowed Operations
------------------

The following operations are allowed by default:

**Data Processing**
   - NumPy, Pandas, SciPy operations
   - Matplotlib plotting
   - Statistical analysis

**Scientific Computing**
   - Scikit-learn models
   - PyTorch, TensorFlow (if installed)
   - BioPython, RDKit

**File Reading**
   - Reading from input directory
   - Writing to output directory
   - CSV, JSON, pickle (trusted files)

Example allowed code::

   import numpy as np
   import pandas as pd
   import matplotlib.pyplot as plt

   # Read data
   data = pd.read_csv('/input/data.csv')

   # Process
   result = np.mean(data['values'])

   # Plot
   plt.figure()
   plt.plot(data['x'], data['y'])
   plt.savefig('/output/plot.png')

   return {"mean": result}

Custom Safety Rules
-------------------

Implement custom safety checks:

.. code-block:: python

   from kosmos.safety.rules import SafetyRule
   import ast

   class NoRecursionRule(SafetyRule):
       \"\"\"Prohibit recursive function calls.\"\"\"

       name = "no_recursion"
       severity = "medium"

       def check(self, tree: ast.AST) -> List[Violation]:
           violations = []

           for node in ast.walk(tree):
               if isinstance(node, ast.FunctionDef):
                   # Check if function calls itself
                   for child in ast.walk(node):
                       if isinstance(child, ast.Call):
                           if (hasattr(child.func, 'id') and
                               child.func.id == node.name):
                               violations.append(
                                   Violation(
                                       rule=self.name,
                                       message=f"Recursive call to {node.name}",
                                       line=child.lineno,
                                       severity=self.severity
                                   )
                               )

           return violations

   # Use custom rule
   validator = CodeValidator()
   validator.add_rule(NoRecursionRule())

Security Best Practices
------------------------

When working with generated code:

1. **Always validate** before execution
2. **Use Docker sandboxing** for isolation
3. **Set resource limits** appropriate for task
4. **Monitor execution** in real-time
5. **Log security events** for audit trail
6. **Review generated code** for sensitive operations
7. **Limit data access** to necessary files only
8. **Use read-only mounts** where possible

Example secure execution::

   from kosmos.safety.validator import CodeValidator
   from kosmos.safety.limits import ResourceLimits
   from kosmos.execution.executor import Executor

   # Validate
   validator = CodeValidator()
   result = validator.validate(code)

   if not result.is_safe:
       raise SecurityError(f"Code validation failed: {result.violations}")

   # Set limits
   limits = ResourceLimits(
       max_cpu_time_seconds=300,
       max_memory_mb=4096,
       network_access=False
   )

   # Execute in sandbox
   executor = Executor(
       docker_image="kosmos-sandbox:latest",
       resource_limits=limits,
       readonly_paths=["/app", "/lib"],
       writable_paths=["/output"]
   )

   try:
       execution_result = executor.execute(code, input_data)
   except Exception as e:
       # Log security event
       logger.error(f"Execution failed: {e}", extra={"code": code})
       raise

Incident Response
-----------------

Handle security incidents:

.. code-block:: python

   from kosmos.safety.incident import IncidentLogger

   logger = IncidentLogger()

   try:
       result = executor.execute(code, input_data)
   except SecurityViolation as e:
       # Log incident
       logger.log_incident(
           severity="high",
           incident_type="security_violation",
           details={
               "violation": str(e),
               "code": code,
               "timestamp": datetime.now(),
               "user": current_user
           }
       )

       # Take action
       if e.severity == "critical":
           notify_security_team(e)
           disable_user_access(current_user)

       raise
