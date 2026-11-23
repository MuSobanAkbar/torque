# choosing how the AI will work 
I could have chosen to have the AI swallow down the price_list and glossary csv and md into 1 prompt, however
that would be prone to a lot of hallucinations. 

essentially seperating probablistic language tasks from deterministic code. 


so, what i have chosen, is that I wnat the AI to handle the language, while python handles the numbers and the rules.


If it does end up halluicinating somewhere, we would know because we run a deterministic python check that 
extracts every dollar amount from the llms explanation text and verifies it against the quote's real numbers.





# extract.py 
So we need pydantic to generate a strict json blueprint. and then hand that to groq, with strict:true.