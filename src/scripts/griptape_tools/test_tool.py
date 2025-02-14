import maya.cmds as cmds
from griptape.drivers.prompt.ollama import OllamaPromptDriver
from griptape.structures import Agent


def hello_griptape():
    agent = Agent(prompt_driver=OllamaPromptDriver(model="llama3.2"))
    response = agent.run("Generate a fun greeting about Maya and Griptape.ai")
    cmds.confirmDialog(title="Griptape Test", message=response.output, button=["OK"])


def test_setup():
    print("Griptape Maya Tools loaded successfully!")
    return True
