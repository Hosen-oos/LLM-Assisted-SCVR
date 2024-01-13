# prompt 1 (Description - Detection)

### version 1.0

**Turn 1**

**System:** You are a smart contract auditor. You will be asked questions related to smart contract vulnerabilities. You can mimic the answer five times in the background and provide me with the most comprehensive answer. Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**Conceptual explanations**: Please explain the **Price Oracle Manipulation** vulnerability in Smart Contract Vulnerabilities. Give the scenarios and code characteristics of this vulnerability, and organize the result in a json format like

{"scenarios": " your answers  here", "code characteristics": "your answers  here"}

**Turn 2**

**vulnerability detection:**You are a smart contract auditor. You will be asked questions related to smart contract vulnerabilities. Please study and memorize the explanation of the vulnerability provided to you (**explain.json**), and later test for the vulnerability in the smart contract provided (**contract.sol**), paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided.

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

# prompt 2 (Feeding-Detection)

### version 1.0

**System:** You are a smart contract auditor. You will be asked questions related to smart contract vulnerabilities. You can mimic the answer five times in the background and provide me with the most comprehensive answer. Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**vulnerability detection:**Please study and memorize the explanation and characterization of vulnerabilities (explaint.json) provided to you, and later test for the vulnerability in the smart contract provided (**contract.sol**), paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

# prompt3(Debatable)

### version 1.0

A-**Turn 1**

**System:** You are a smart contract auditor. You will be asked questions related to smart contract vulnerabilities. You can mimic the answer five times in the background and provide me with the most comprehensive answer. Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**vulnerability detection:**Please test for the vulnerability in the smart contract provided (**contract.sol**), paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided.

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

**A-Turn2**

**System:** You are a smart contract auditor.Now there is a report (**explain_B.json**) of your colleague's inspection of the same smart contract (**contract.json**).Please combine it with your report (**explain_A.json**) and regenerate the report.Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**vulnerability detection:** You need to judge the correctness of **explain_B.json** and re-check the correctness of **explain_A.json,** considering whether there are any vulnerabilities that were not previously detected. And please paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided.

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

**A-Turn3-X**

same as A-turn 2

B-**Turn 1**

**System:** You are a smart contract auditor. You will be asked questions related to smart contract vulnerabilities. You can mimic the answer five times in the background and provide me with the most comprehensive answer. Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**vulnerability detection:**Please test for the vulnerability in the smart contract provided (**contract.sol**), paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided.

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

**B-Turn2**

**System:** You are a smart contract auditor.Now there is a report (**explain_A.json**) of your colleague's inspection of the same smart contract (**contract.json**).Please combine it with your report (**explain_B.json**) and regenerate the report.Additionally, Please strictly adhere to the output format specified in the question. The output format specified in the question;

---

**vulnerability detection:** You need to judge the correctness of **explain_A.json** and re-check the correctness of **explain_B.json**, considering whether there are any vulnerabilities that were not previously detected. And please paying extra attention to the **Price Oracle Manipulation** vulnerability and **consider attacks from external calls and external inputs.**

You can mimic the answer five times in the background and provide me with the the most comprehensive answer. Only the **vulnerability type**, **vulnerability location** and **explanation** are required to be answered, no modifications need to be provided.

Please organize the result in a json format like

{"First vulnerability": " your answers  here", 

"Second vulnerability": "your answers  here"

………

}

**B-Turn3-X**

same as B-turn 2