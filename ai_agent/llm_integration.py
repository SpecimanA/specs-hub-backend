# ai_agent/llm_integration.py
import openai
import json
import logging
from django.conf import settings
from .models import AIAgent, AITool
from ai_agent import tools # ייבוא קובץ הכלים

logger = logging.getLogger(__name__)

class AzureOpenAIAgent:
    def __init__(self, agent_name: str):
        self.agent_config = AIAgent.objects.get(name=agent_name, is_active=True)
        
        openai.api_key = settings.AZURE_OPENAI_API_KEY
        openai.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT
        openai.api_version = settings.AZURE_OPENAI_API_VERSION
        openai.azure_deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME

        self.client = openai.AzureOpenAI() # שימוש ב-AzureOpenAI client
        
        self.system_prompt = self.agent_config.system_prompt
        self.llm_settings = self.agent_config.llm_settings or {}
        
        self.available_tools = self._get_available_tools()

    def _get_available_tools(self):
        """
        מחזיר רשימה של הכלים הזמינים לסוכן בפורמט הנדרש על ידי OpenAI.
        """
        agent_tools = self.agent_config.tools.all()
        openai_tools = []
        for tool in agent_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.function_name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return openai_tools

    def _call_tool_function(self, tool_name: str, arguments: dict):
        """
        מפעיל את פונקציית הכלי בפועל מקובץ tools.py.
        """
        if hasattr(tools, tool_name):
            tool_function = getattr(tools, tool_name)
            try:
                # קריאה לפונקציית הכלי עם הארגומנטים
                result = tool_function(**arguments)
                return json.dumps(result)
            except Exception as e:
                logger.error(f"Error calling tool '{tool_name}' with arguments {arguments}: {e}")
                return json.dumps({"status": "error", "message": f"שגיאה בהפעלת הכלי {tool_name}: {e}"})
        else:
            logger.warning(f"Tool function '{tool_name}' not found in tools.py.")
            return json.dumps({"status": "error", "message": f"פונקציית כלי {tool_name} לא נמצאה."})

    def chat(self, user_message: str, conversation_history: list = None):
        """
        מנהל שיחה עם מודל השפה, כולל הפעלת כלים.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME, # או model=self.llm_settings.get('model')
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto", # מאפשר למודל לבחור כלי או להשיב
                temperature=self.llm_settings.get('temperature', 0.7),
                # ... פרמטרים נוספים מ-llm_settings
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                # המודל רוצה להפעיל כלי
                messages.append(response_message) # הוסף את התגובה עם קריאת הכלי להיסטוריה
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    tool_output = self._call_tool_function(function_name, function_args)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_output,
                    })
                
                # שלח שוב את ההודעות עם פלט הכלי כדי שהמודל יסכם
                second_response = self.client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=messages,
                    tools=self.available_tools,
                    tool_choice="auto",
                    temperature=self.llm_settings.get('temperature', 0.7),
                )
                return second_response.choices[0].message.content
            else:
                # המודל השיב ישירות
                return response_message.content

        except openai.APIError as e:
            logger.error(f"Azure OpenAI API Error: {e}")
            return f"שגיאה בחיבור לשירותי AI: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return f"שגיאה בלתי צפויה: {e}"

