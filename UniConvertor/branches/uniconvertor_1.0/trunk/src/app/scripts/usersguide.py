#
# Scripts from the users guide
#

def hello_world(context):
	context.application.MessageBox(title = "My Script", 
									message = "Hello World!")

# register scripts
import Sketch.Scripting
Sketch.Scripting.AddFunction('ug_hello_world', 'Hello World',
								hello_world, menu = "User's Guide")
